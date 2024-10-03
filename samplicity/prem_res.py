"""
The PremRes class is contained in the prem_res.py module.

"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Union

import numpy as np
import pandas as pd

from .helper import allocation_matrix, combins_df_col, log_decorator

logger = logging.getLogger(__name__)


class PremRes:
    """
    A class to calculate the premium and reserve risk component of the SAM SCR.

    :ivar scr: Reference to the SCR class which stores the supporting data.
    :type scr: SCR
    :ivar output: A dictionary that stores all of the results from the class.
    :type output: Dict[str, pd.DataFrame]

    :Example:

    >>> # Create a PremRes class and perform a calculation
    >>> prem_res = PremRes(sam_scr, "prem_res", True)
    >>> # An alternative methodology to do this
    >>> prem_res_module = sam_scr.create_supporting("prem_res")

    """

    #@log_decorator
    def __init__(
        self, sam_scr: "SCR", class_name: str = "prem_res", calculate: bool = False
    ) -> PremRes:
        """
        Initialize the PremRes class. At this stage the the class is added to the SCR object.

        :param sam_scr: The base SCR class.
        :type sam_scr: str
        :param class_name: The name that should be used for the prem_res class.
        :type class_name: str
        :param calculate: If the PremRes calculation should be performed.
        :type calculate: bool

        """

        self.scr: "SCR" = sam_scr
        self.scr.classes[class_name] = self
        self.output: Dict[str, pd.DataFrame] = {}

        if calculate:
            self.f_calculate()

    @log_decorator
    def f_calculate(self) -> Dict[str, pd.DataFrame]:
        """
        Calculate premium and reserve risk.

        The function aggregates the data supplied in the 'data' dictionary
        of the SCR class. After the aggregation and manipulation, the premium
        and reserve risk are calculated for the different diversification levels.

        :return: A dictionary of Dataframes with the results.
        :rtype: Dict[str, pd.DataFrame]

        :Example:

        >>> # This assumes that the PremRes class has been added but not calculated.
        >>> res=sam_scr.classes['prem_res'].f_calculate()
        >>> res=PremRes.f_calculate()

        """
        div_field: str = self.scr.f_data("data", "data", "diversification_level").iloc[
            0
        ]
        calc_level: str = self.scr.f_data("data", "data", "calculation_level").iloc[0]

        data: pd.DataFrame = self.scr.f_data("data", "data", "prem_res")

        # Data manipulation
        data.loc[data["lob_type"] == "NP", "lob"] = "18b"
        data.loc[data["lob_type"] == "FNP", "lob"] = "18b"
        data.loc[data["lob_type"] == "O", "lob"] = "18c"
        data.loc[data["lob_type"] == "FO", "lob"] = "18c"

        data["complete_lob"] = data["lob_type"] + data["lob"]

        lob: pd.DataFrame = (
            data[["complete_lob", "lob_type", "lob"]].value_counts().reset_index()
        )

        corr: pd.DataFrame = self.scr.f_data("data", "metadata", "corr_prem_res").loc[
            lob["lob"], lob["lob"]
        ]
        corr.index = lob["complete_lob"]
        corr.columns = lob["complete_lob"]

        df_allocation: pd.DataFrame = allocation_matrix(data, div_field, calc_level)

        prem_res: Dict[tuple, pd.DataFrame] = {}
        prem_alloc: Dict[tuple, np.ndarray] = {}

        base_matrix: pd.DataFrame = pd.DataFrame(
            0, index=lob["complete_lob"], columns=np.unique(data[div_field])
        )

        # Calculate premium and reserve volumes
        # The columns contain the divisions, the rows contain the lob's
        for val in ["gross", "net"]:
            for dat in ["p", "p_last", "fp_existing", "fp_future", "claim"]:
                prem_res[(val, dat)] = (
                    data.pivot_table(
                        val + "_" + dat, "complete_lob", div_field, aggfunc="sum"
                    )
                    .fillna(0)
                    .combine_first(base_matrix)
                )

        # Process reinsurance data, we join the contracts to the reinsurer shares
        ri_contract: pd.DataFrame = self.scr.f_data("data", "data", "ri_contract")[
            ["ri_share"]
        ]
        ri_share: pd.DataFrame = self.scr.f_data("data", "data", "ri_contract_share")[
            ["reinsurance_id", "counterparty_id", "counterparty_share"]
        ]

        ri_data: pd.DataFrame = pd.merge(
            ri_contract,
            ri_share,
            left_index=True,
            right_on="reinsurance_id",
            how="left",
        )

        ri_data["ri_contract_counterparty_share"] = (
            ri_data["ri_share"] * ri_data["counterparty_share"]
        )

        # Join the reinsurance data to the actual data
        calc_ri: pd.DataFrame = pd.merge(
            data,
            ri_data[
                ["reinsurance_id", "ri_contract_counterparty_share", "counterparty_id"]
            ],
            on="reinsurance_id",
            how="inner",
        )
        calc_ri.fillna({"ri_contract_counterparty_share": 0}, inplace=True)

        for dat in ["p", "p_last", "fp_existing", "fp_future", "claim"]:
            calc_ri.fillna({f"gross_{dat}": 0}, inplace=True)
            calc_ri["rein_" + dat] = (
                calc_ri["gross_" + dat] * calc_ri["ri_contract_counterparty_share"]
            )
            # Calcualte a matrix of the reinsurer shares
            prem_res[("reinsurance", dat)] = calc_ri.pivot_table(
                "rein_" + dat, "complete_lob", div_field, aggfunc="sum"
            )
            prem_res[("reinsurance", dat)] = (
                prem_res[("reinsurance", dat)].fillna(0).combine_first(base_matrix)
            )
            # Subtract the reinsurance matrix from the gross matrix
            prem_res[("calc_net", dat)] = prem_res[("gross", dat)].sub(
                prem_res[("reinsurance", dat)], fill_value=0
            )

        reinsurer_data: pd.DataFrame = calc_ri[
            [
                div_field,
                "complete_lob",
                "counterparty_id",
                "rein_p",
                "rein_p_last",
                "rein_fp_existing",
                "rein_fp_future",
                "rein_claim",
            ]
        ]
        reinsurer_data = reinsurer_data.groupby(
            ["counterparty_id", "complete_lob", div_field], as_index=False
        ).sum()

        # For each reinsurer we add back their value to the calculated net
        # Has the same effect of removing everything but them from the gross
        calc_list: np.ndarray = np.unique(reinsurer_data.counterparty_id)
        for rein in calc_list:
            data = reinsurer_data[reinsurer_data["counterparty_id"] == rein]
            for dat in ["p", "p_last", "fp_existing", "fp_future", "claim"]:
                pvt = data.pivot_table(
                    "rein_" + dat, "complete_lob", div_field, aggfunc="sum"
                ).fillna(0)
                prem_res[(rein, dat)] = prem_res[("calc_net", dat)].add(
                    pvt, fill_value=0
                )

        # Data preparation is complete at this stage

        std_dev: pd.DataFrame = self.scr.f_data(
            "data", "metadata", "std_dev_prem_res"
        ).loc[lob["lob"]]

        add_values: list = ["gross", "net", "calc_net", "reinsurance"]
        # We will calculate values fro eahc reinsurer as well as gross, net, calc_net, reinsurance
        # Reinsurance is probably a bit overkill but gives the reinsurance premium & reserve risk figures
        for val in [*calc_list, *add_values]:
            for dat in ["p", "p_last", "fp_existing", "fp_future", "claim"]:
                # Need to sor to make sure they are in the same order
                # Must match the std_dev
                prem_res[(val, dat)] = prem_res[(val, dat)].loc[lob["complete_lob"]]
                cols = prem_res[(val, dat)].columns
                prem_alloc[(val, dat)] = (
                    prem_res[(val, dat)].values @ df_allocation[cols].T.values
                )

            p = prem_alloc[(val, "p")]
            p_last = prem_alloc[(val, "p_last")]
            prem_alloc[(val, "premium")] = np.where(p > p_last, p, p_last)
            prem_alloc[(val, "premium")] += (
                prem_alloc[(val, "fp_existing")] + prem_alloc[(val, "fp_future")]
            )

            # We actually don't calculate the standard deviation
            # The calcualtion can be simplified.
            # The specification divides by the vouem measure to immediately multiply by it again
            sigma: Dict[str, np.ndarray] = {}
            sigma["premium"] = np.einsum(
                "ij,il->il", std_dev[["prem"]], prem_alloc[(val, "premium")]
            )
            sigma["reserve"] = np.einsum(
                "ij,il->il", std_dev[["res"]], prem_alloc[(val, "claim")]
            )
            sigma["overall"] = np.sqrt(
                np.square(sigma["premium"])
                + 2 * 0.5 * sigma["premium"] * sigma["reserve"]
                + np.square(sigma["reserve"])
            )

            temp: Dict[str, np.ndarray] = {}
            for calc in ["premium", "reserve", "overall"]:
                temp[calc] = 3 * np.sqrt(
                    np.einsum("ij,jk,ki->i", sigma[calc].T, corr.values, sigma[calc])
                )
                self.output[val] = pd.DataFrame(temp)
                self.output[val].index = df_allocation.index

        # Merge the various dataframes for the different counterparties into single dataframes
        dic_reinsurance: list = [
            df.assign(counterparty=party)
            for party, df in self.output.items()
            if party not in add_values
        ]
        # Only need this step if we ahve reinsurance recoveries
        if len(dic_reinsurance) > 0:
            df_reinsurance: pd.DataFrame = pd.concat(dic_reinsurance)
            df_net: pd.DataFrame = self.output["calc_net"]
            df_default: pd.DataFrame = pd.merge(
                df_net, df_reinsurance, left_index=True, right_index=True, how="left"
            )
            for calc in ["premium", "reserve", "overall"]:
                df_default[calc] = df_default[calc + "_y"] - df_default[calc + "_x"]
            df_default = df_default[["counterparty", "premium", "reserve", "overall"]]
            self.output["default"] = df_default

        return self.output

    def f_data(
        self, data: Optional[str] = None, sub_data: Optional[str] = None
    ) -> Union[pd.DataFrame, None]:
        """
        Retrieve data from the PremRes class. Supports f_data from the SCR class.

        :param data: The specific data name to retrieve.
        :type data: str
        :param sub_data: The sub-data name, if applicable.
        :type sub_data: str, optional
        :return: The retrieved data as a pandas DataFrame or None if not found.
        :rtype: Union[pd.DataFrame, None]
        :raises ValueError: If the requested data cannot be found or accessed.

        .. note::
            All input strings are converted to lowercase and stripped of leading/trailing spaces
            to improve user experience and reduce errors due to case sensitivity or whitespace.

        """
        try:
            data = data.lower().strip() if data else ""
            sub_data = sub_data.lower().strip() if sub_data else ""

            if sub_data == "all" or sub_data is None:
                df = self.output[data]
            else:
                df = self.output[data][[sub_data]]

        except Exception as e:
            raise ValueError(f"Cannot find {data} - {sub_data}") from e
            return None
        else:
            return None if df is None else df.copy(deep=True)
