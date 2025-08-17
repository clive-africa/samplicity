"""
The FactorCat class is contained in teh factor_cat.py module.
"""

from itertools import product
import logging
import numpy as np
import pandas as pd
from .helper import combins_df_col, log_decorator
from typing import Literal
from typing import Any, Dict, Optional, Union


logger = logging.getLogger(__name__)


class FactorCat:
    """
    A class to calculate the gross factor based risk of the SAM SCR.

    ...

    Attributes
    ----------
        None

    Methods
    -------
    calculate(sam_scr):
        Data manipulation and calcutions to calculate gross factor cat risk..
        The results are returned as a dictionary.
    """

    @log_decorator
    def __init__(self, sam_scr, class_name="factor_cat", calculate=False):
        """Initialise the class."""

        self.scr = sam_scr
        """ A reference to the main SCR class."""

        self.output = {}
        """Stores all of the output of the class. """

        self.output["factor_data"] = self.__f_data_prep()
        """Stores all of our factor factor after we have manipulated it."""

        factor_charges = self.scr.f_data("data", "metadata", "factor_cat_charge")
        factor_charges["lob"] = factor_charges["lob"].astype(str)

        df_factor_charge = pd.concat(
            factor_charges.index.to_series()
            .apply(lambda fact: self.__f_normalise_factor(factor_charges, fact))
            .to_list()
        )
        df_factor_charge["complete_lob"] = (
            df_factor_charge.loc[:, "lob_type"] + df_factor_charge.loc[:, "lob"]
        )
        self.output["factor_charge"] = df_factor_charge.pivot_table(
            "factor", "complete_lob", "peril", aggfunc="max"
        ).fillna(0)

        self.scr.classes[class_name] = self

        if calculate:
            self.f_calculate()

    def __f_data_prep(self):
        """Prepares the data for use in the calculation."""
        # Filter our data to only remove the rows where the indicator is
        # equal to 'Y'. We do some text manipulation to make sure that we don't
        # miss some of the data.
        factor_data = self.scr.f_data("data", "data", "prem_res")
        factor_data["include_factor_cat"] = factor_data["include_factor_cat"].map(
            str.upper
        )
        factor_data["include_factor_cat"] = factor_data["include_factor_cat"].map(
            str.strip
        )
        factor_data = factor_data[factor_data["include_factor_cat"] == "Y"]

        # The code expects the LOB in a slightly different format to that of
        # the SCR standard formulae. We do this to make user input a lot
        # easier. We now need to adjust for as as part of the NonProp class.
        # Basically we capture more detail in the input comapred to the
        # SCR calcualtion which groups everything together.
        factor_data.loc[factor_data["lob_type"] == "O", "lob"] = "18c"
        factor_data.loc[factor_data["lob_type"] == "FO", "lob"] = "18f"

        factor_data.loc[
            (factor_data["lob_type"] == "NP") & (factor_data["lob"] != "14"), "lob"
        ] = "18b"
        factor_data.loc[
            (factor_data["lob_type"] == "FNP") & (factor_data["lob"] != "14"), "lob"
        ] = "18e"

        # Need to remove specific LOB where there is no factor based cat
        remove = ["3i", "9", "15", "17i", "17ii", "17iii", "17iv"]
        factor_data = factor_data[~factor_data["lob"].isin(remove)]

        factor_data.loc[:, "complete_lob"] = (
            factor_data["lob_type"] + factor_data["lob"]
        )

        div_field = self.scr.f_data("data", "data", "base_inputs")["base_inputs"][
            "diversification_level"
        ]

        # Replace the None values with '__none__'
        # Thsi ensure that we cna get the calculation working properly
        factor_data["ri_structure"] = factor_data["ri_structure"].fillna("__none__")

        factor_data["div_structure"] = list(
            factor_data[[div_field, "ri_structure"]].itertuples(index=False, name=None)
        )

        return factor_data

    def __f_normalise_factor(self, f_chrg, index_value):
        """Normalise our factor cat charge matrix."""

        lob_type = pd.DataFrame(
            list(
                product(
                    [index_value],
                    f_chrg.loc[index_value, "lob_type"].split(";"),
                    f_chrg.loc[index_value, "lob"].split(";"),
                )
            ),
            columns=["peril", "lob_type", "lob"],
        )
        lob_type["factor"] = f_chrg.loc[index_value, "factor"]
        df_factor_charge = pd.DataFrame(
            lob_type, columns=["peril", "lob_type", "lob", "factor"]
        )
        return df_factor_charge

    @log_decorator
    def f_calculate(self):
        """Calculate the gross factor based catastrophe charges."""

        # Create the different combinations that we need for the calculation.
        for calc in ("base", "reinsurance", "div_structure"):
            result = self.f_indv_calculation(calc)

            # No maniulation is needed here
            if calc == "base":
                # The gross factor based charges are calcualted
                # No need for any further manipulation
                self.output[calc] = result

            # The general guidance requires that for the reinsurance
            # calculation we must allocate the charges proportionately.
            # It is difficult to decide where this should happen -
            # and the placement of this calculation is a little debatable.
            # Ultimately it has been decided to put the calcualtion here.
            # For factor cat this is alsmost always not necessary as the
            # charges are linear but could be necessary where premiums
            # are negative.

            elif calc == "reinsurance":
                # We have charges for eahc reinsurance structure
                # we need to sclae teh results to return he same result as the overall charge.

                # We get the index, we are lookign for the total entry.
                # This should always be the last entry, but we check
                max_length = max(len(x) for x in result.index)
                if len(result.index[len(result) - 1]) != max_length:
                    raise Exception(
                        "factor_cat",
                        "f_calculate",
                        "Diversification listing is incorrect",
                        "",
                    )

                # At this stage we are good to proceed
                # This formual is slightly more complex than nat_cat as we
                # use vector the calculation

                # We are summing all the different reinsurance arrangements, excluding the total event
                # Calculate the sum of charges excluding the last row (total event)
                sum_charges = result.iloc[:-1, :].sum(axis=0)

                # Normalize the charges by dividing each row by the sum of charges
                # and then multiplying by the total event charges (last row)
                normalized_charges = (
                    result.iloc[:-1, :]
                    .div(sum_charges, axis=1)
                    .mul(result.iloc[-1, :], axis=1)
                    .fillna(0)
                )

                # We drop the toal column as the reuslt is not accurate at this stage.
                normalized_charges = normalized_charges.drop(
                    columns=["fc_total"], errors="ignore"
                )
                self.output[calc] = normalized_charges

            # A similar approahc needs to happen for the calculations by
            # division and structure. We will be consistent in our approach
            # and perform the allocation here. Because we know that the
            # divsion_structure calcualtion happens last, we have referenced
            # the base calculation

            elif calc == "div_structure":
                # We have charges fro each division combination and
                # reinsurance structure. We need to scale the charges
                # This is used to ensure the appropriate reinsurance allocation

                # We have a dataframe with gross charges for every diversification and reinsurance strcuture combination

                # The index is a tuple of the form (division, structure)
                # We need to convert this to a DataFrame with columns 'div' and 'structure'
                result[["div", "structure"]] = [
                    np.array([x[0], x[1]], dtype=object) for x in result.index
                ]

                # The base data we must use to pro-rate our events
                # THis has the events per division combination
                base_data = self.output["base"]

                # This data is slighty different when compared to nat cat.
                # We will need to store each peril seperately
                temp_result = {}
                perils = pd.Series(self.output["factor_charge"].columns.values)
                for per in perils:
                    # We don't need an aggregation function as there will only ever be one value
                    tmp = result.pivot(
                        index="div", columns="structure", values=per
                    ).fillna(0)
                    # Get the different structures active for the event
                    structs = tmp.columns.values
                    # Get the totals for each division combination
                    df_total = base_data.loc[tmp.index, per]
                    row_total = tmp[structs].sum(axis=1)
                    # We pro-rate the vlaues by the total for eahc division combination
                    tmp[structs] = (
                        tmp[structs]
                        .divide(row_total.replace(0, np.nan), axis=0)
                        .multiply(df_total, axis=0)
                        .fillna(0)
                    )

                    temp_result[per] = tmp

                self.output[calc] = temp_result

        return True

    def __f_allocation(
        self: "FactorCat",
        calculation_type: Literal["base", "div_structure", "reinsurance"],
    ) -> tuple[str, pd.DataFrame]:
        """Prepare the allocation matrix for the calculation."""

        # For bothe the base and div_structure calculation we need the diversification combinations.
        if calculation_type in ("base", "div_structure"):
            # We will need to cahgne thsi field back to 'div_structure'
            # We temporarily overwrite this field here for the 'div_strcure' calculation
            div_field = self.scr.f_data("data", "data", "base_inputs")["base_inputs"][
                "diversification_level"
            ]
            calc_level = self.scr.f_data("data", "data", "base_inputs")["base_inputs"][
                "calculation_level"
            ]
        elif calculation_type == "reinsurance":
            div_field = "ri_structure"
            calc_level = "individual"
        else:
            raise ValueError(
                "calculation type should be: base, div_structure or reinsurance"
            )

        # This will return a list of tuples with the combinations
        # We will use this to create the allocation matrix
        # The combinations are based on the div_field and the calculation level
        lst, _ = combins_df_col(self.output["factor_data"], div_field, calc_level)

        # Here we calcualte the allocation matrix for each structure in each divsion
        # This gives us the event per structure for eahc division combination
        if calculation_type == "div_structure":
            structure_list = self.output["factor_data"]["ri_structure"].unique()
            division_list = self.output["factor_data"][div_field].unique()

            # The rows will have all the combinations of divisions and structures
            rows = [(div, struct) for div in lst for struct in structure_list]
            # There is only an entry for each division and structure
            cols = [(div, struct) for div in division_list for struct in structure_list]

            mat = [x[0] in y[0] and x[1] in y[1] for x in cols for y in rows]
            mat = np.reshape(mat, (len(cols), len(rows))).T.astype(int)
            df_allocation = pd.DataFrame(mat, index=rows, columns=cols)

            # Now we move back to normal to allow the calculation to take place
            # We change the field back from our initial loop
            # In the initial data population we create the div_structure field
            div_field = "div_structure"
        else:
            df_allocation = (
                pd.DataFrame(lst, index=lst).apply(pd.Series.value_counts, 1).fillna(0)
            )
        return div_field, df_allocation

    def f_indv_calculation(
        self: "FactorCat",
        calculation_type: Literal["base", "div_structure", "reinsurance"],
    ) -> pd.DataFrame:
        """Actual gross factor based charge calculation."""

        # Allow for the scenario when there is no data for the calculation
        if self.output["factor_data"] is None or len(self.output["factor_data"]) == 0:
            return None

        # Get the div_field and allocation matrix
        # Splti this out into a new smaller function
        div_field, df_allocation = self.__f_allocation(calculation_type)

        # We now need to ggroup the data according to the diversification fields
        # For the diversification calcualtion we have created a field called div_structure
        factor_data = (
            self.output["factor_data"][[div_field, "complete_lob", "gross_p"]]
            .groupby([div_field, "complete_lob"], as_index=False)
            .sum()
        )
        factor_data = factor_data.pivot_table(
            "gross_p", "complete_lob", div_field, aggfunc="sum"
        ).fillna(0)

        # Multiply by the allocation matrix to get the
        factor_data_allocate = factor_data.dot(df_allocation[factor_data.columns].T)
        # Remove any negative premium values, don't beleive we should allow fro negative premiums
        factor_data_allocate[factor_data_allocate < 0] = 0

        df_factor_charge = self.output["factor_charge"].loc[factor_data_allocate.index]

        # THsi takes a big of mind breaking to understand the algebra going on here.
        calc_chrg = pd.DataFrame(
            np.einsum("ij,ik->jk", factor_data_allocate, df_factor_charge),
            index=df_allocation.index,
            columns=df_factor_charge.columns,
        )

        # The aggregation formual for the different charges is a little irritating
        # We need to exlcude these charges form the initial aggregation
        sel_cols = calc_chrg.columns[
            (calc_chrg.columns != "fc_accident_health")
            & (calc_chrg.columns != "fc_non_prop_accident_health")
        ]

        # At this atge we now add the accident and health charges to the initial calculation
        calc_chrg["fc_total"] = np.sqrt(
            np.square(calc_chrg.loc[:, sel_cols]).sum(axis=1)
            + np.square(
                calc_chrg.loc[:, "fc_accident_health"]
                + calc_chrg.loc[:, "fc_non_prop_accident_health"]
            )
        )

        return calc_chrg

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

            if data in ("div_structure"):
                res = self.output[data][sub_data]
            elif data in ("base", "reinsurance") and sub_data in (
                "fc_storm",
                "fc_flood",
                "fc_earthquake",
                "fc_hail",
                "fc_major_fire_explosion",
                "fc_marine_aviation_transit",
                "fc_prof_liability",
                "fc_public_laibility",
                "fc_employer_liability",
                "fc_officer_liability",
                "fc_product_liability",
                "fc_other_liability",
                "fc_credit_guarantee",
                "fc_miscellaneous",
                "fc_non_prop_other",
                "fc_other_risk_mitigation",
                "fc_accident_health",
                "fc_non_prop_accident_health",
                "fc_total",
            ):
                res = self.output[data][[sub_data]].T
            elif data in ("base", "reinsurance") and sub_data in ("all", None):
                res = self.output[data]
            elif data in ("events"):
                res = self.output["factor_charge"].columns.to_frame()
            else:
                res = self.output[data]
        except:
            # logger.critical(f"Error: {data} - {sub_data}")
            raise ValueError(f"cannot find {data} - {sub_data}")
        else:
            return None if res is None else res.copy(deep=True)
