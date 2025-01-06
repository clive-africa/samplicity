import pandas as pd
import numpy as np
from typing import Optional, Union
from .helper import combins_df_col, log_decorator, allocation_matrix


class NatCat:
    """
    A class to calculate the gross natural catastrophe risk of the SAM SCR.

    :ivar scr: Reference to the SCR class which stores the supporting data.
    :type scr: SCR
    :ivar output: A dictionary that stores all of the results from the class.
    :type output: Dict[str, pd.DataFrame]

    :Example:

    >>> # Create a NatCat class and perform a calculation
    >>> nat_cat = NatCat(sam_scr, "nat_cat", True)
    >>> # An alternative methodology to do this
    >>> nat_cat_module = sam_scr.create_supporting("nat_cat")

    """

    @log_decorator
    def __init__(self, sam_scr, class_name="nat_cat", calculate=False):
        self.scr = sam_scr
        """A reference to the main SCR object"""

        self.output = {}
        """Stores all of the outputs of the class."""

        # self.data_meta=sam_scr.data_meta

        nat_cat_si = self.scr.f_data("data", "data", "nat_cat_si").sort_values(
            by="postal_code"
        )
        nc_mapping = self.scr.f_data(
            "data", "metadata", "nat_cat_zone_mapping"
        ).sort_values(by="postal_min")

        nc_data = pd.merge_asof(
            left=nat_cat_si,
            right=nc_mapping[["zone", "postal_min"]],
            left_on="postal_code",
            right_on="postal_min",
            direction="backward",
        ).sort_values(by="postal_code")

        # Create a single column to get our cat risk calcualted by
        # divsion and structure
        # Thsi is used to allocate reinsurance recoveries later
        div_field = self.scr.f_data("data", "data", "diversification_level").iloc[0]
        nc_data["div_structure"] = list(
            nc_data[[div_field, "ri_structure"]].itertuples(index=False, name=None)
        )

        self.output["nat_cat_data"] = nc_data

        # Add the class to the SCR object
        self.scr.classes[class_name] = self

        if calculate:
            self.f_calculate()

    def f_data_aggregation(self, calc_type):
        # Get the different combinatiosn we need to calcualte the natural
        # catstrophe risk for
        # We do this for each function individually as this significanly
        # impacts our overall fucntion pseed.
        # we need to get our diversifciation columns and the method of
        # diversification
        if calc_type in ("base", "div_structure"):
            div_level = self.scr.f_data("data", "data", "diversification_level").iloc[0]
            calc_level = self.scr.f_data("data", "data", "calculation_level").iloc[0]
        elif calc_type == "reinsurance":
            div_level = "ri_structure"
            calc_level = "individual"
        else:
            div_level = "div_structure"
            calc_level = "diversification"

        if calc_type == "div_structure":
            lst = combins_df_col(self.output["nat_cat_data"], div_level, calc_level)

            structure_list = np.unique(self.output["nat_cat_data"]["ri_structure"])
            division_list = np.unique(self.output["nat_cat_data"][div_level])

            new_lst = [(x, y) for x in lst for y in structure_list]
            cols = [(x, y) for x in division_list for y in structure_list]

            matrix = [
                np.array(x[0] in y[0] and x[1] in y[1], dtype=object)
                for x in cols
                for y in new_lst
            ]
            matrix = np.reshape(matrix, (len(cols), len(new_lst))).T.astype(int)
            df_allocation = pd.DataFrame(matrix, index=new_lst, columns=cols)
            # Now we move back to normal to allow the calcaultion to take place
            div_level = "div_structure"
            lst = new_lst
        else:
            df_allocation = allocation_matrix(
                self.output["nat_cat_data"], div_level, calc_level
            )

        # df_allocation.index=lst

        mat_index = self.scr.f_data("data", "metadata", "nat_cat_zone_mapping")[
            ["zone"]
        ]
        mat_index = np.unique(mat_index)
        cols = np.unique(self.output["nat_cat_data"][[div_level]])
        base_matrix = pd.DataFrame(0, index=mat_index, columns=cols)

        calc_nat_cat_data = self.output["nat_cat_data"][
            [
                div_level,
                "res_buildings",
                "comm_buildings",
                "contents",
                "engineering",
                "motor",
                "zone",
            ]
        ]
        calc_nat_cat_data = calc_nat_cat_data.groupby(
            [div_level, "zone"], as_index=False
        ).sum()

        calc_nat_cat_data["hail_rci"] = (
            calc_nat_cat_data["res_buildings"] + calc_nat_cat_data["comm_buildings"]
        )
        calc_nat_cat_data["hail_motor"] = calc_nat_cat_data["motor"]
        calc_nat_cat_data["total_si"] = calc_nat_cat_data[
            ["res_buildings", "comm_buildings", "contents", "engineering", "motor"]
        ].sum(axis=1)

        return (
            calc_nat_cat_data.copy(deep=True),
            base_matrix.copy(deep=True),
            df_allocation.copy(deep=True),
        )

    def f_cat_calculation(
        self, nat_cat_data, base_matrix, df_allocation, div_field, calc_type
    ):
        # logger.debug("Function start")

        if calc_type == "base":
            div_field = div_field
        elif calc_type == "reinsurance":
            div_field = "ri_structure"
        else:
            div_field = "div_structure"

        calc_data = {}
        calc_data_allocate = {}
        zone_charge = self.scr.f_data("data", "metadata", "zone_charge")
        for calc in [
            "res_buildings",
            "comm_buildings",
            "contents",
            "engineering",
            "motor",
            "hail_rci",
            "hail_motor",
            "total_si",
        ]:
            calc_data[calc] = nat_cat_data.pivot_table(
                calc, "zone", div_field, aggfunc="sum"
            )
            calc_data[calc].fillna(0, inplace=True)
            calc_data[calc] = calc_data[calc].combine_first(base_matrix)
            map_list = map(calc_data[calc].index.tolist().index, zone_charge.index)
            calc_data[calc] = calc_data[calc].iloc[list(map_list)]
            calc_data_allocate[calc] = calc_data[calc].dot(
                df_allocation[calc_data[calc].columns].T
            )

        weighted_sum_insured = {}
        for calc in [
            "res_buildings",
            "comm_buildings",
            "contents",
            "engineering",
            "motor",
            "hail_rci",
            "hail_motor",
        ]:
            # Will need this line to do the matrix multiplication when
            # we have multiple product lines
            weighted_sum_insured[calc] = pd.DataFrame(
                np.einsum("i,il->il", zone_charge[calc], calc_data_allocate[calc]),
                index=zone_charge.index,
                columns=df_allocation.index,
            )
            # weighted_sum_insured=sum_insured_data*weights

        corr_matrix = {}
        for corr in [
            "res_buildings",
            "comm_buildings",
            "contents",
            "engineering",
            "motor",
        ]:
            corr_matrix[corr] = self.scr.f_data("data", "metadata", "corr_" + corr)

        corr_matrix["hail_rci"] = self.scr.f_data("data", "metadata", "corr_hail")
        corr_matrix["hail_motor"] = self.scr.f_data("data", "metadata", "corr_hail")

        nat_cat = {}
        for calc in [
            "res_buildings",
            "comm_buildings",
            "contents",
            "engineering",
            "motor",
            "hail_rci",
            "hail_motor",
        ]:
            nat_cat[calc] = pd.DataFrame(
                np.sqrt(
                    np.einsum(
                        "ij,jk,ki->i",
                        weighted_sum_insured[calc].T,
                        corr_matrix[calc],
                        weighted_sum_insured[calc],
                    )
                ),
                index=df_allocation.index,
                columns=["charge"],
            )

        dfs = [
            nat_cat["res_buildings"].T,
            nat_cat["comm_buildings"].T,
            nat_cat["contents"].T,
            nat_cat["engineering"].T,
            nat_cat["motor"].T,
        ]
        eq_nat_cat = pd.concat(dfs)
        eq_nat_cat.index = [
            "res_buildings",
            "comm_buildings",
            "contents",
            "engineering",
            "motor",
        ]

        risk_charge = self.scr.f_data("data", "metadata", "risk_charge")
        eq_nat_cat = eq_nat_cat.reindex(risk_charge.index)
        eq_charges = np.einsum("ij,il->il", risk_charge, eq_nat_cat)

        corr_risk = self.scr.f_data("data", "metadata", "corr_risk")
        corr_risk = corr_risk[risk_charge.index][risk_charge.index]

        eq_charge = pd.DataFrame(
            np.sqrt(np.einsum("ij,jk,ki->i", eq_charges.T, corr_risk, eq_charges)),
            index=df_allocation.index,
            columns=["charge"],
        )

        # We are going to use this variable a few times below
        chrg = self.scr.f_data("data", "metadata", "base_charge")

        eq_charge = eq_charge * chrg.at["earthquake", "base_charge"]

        hail_charge = (nat_cat["hail_rci"] + nat_cat["hail_motor"]) * chrg.at[
            "hail", "base_charge"
        ]

        total_si = nat_cat_data[["total_si", div_field]]
        total_si = total_si.groupby([div_field], as_index=True).sum().fillna(0)
        total_si = df_allocation[total_si.index].dot(total_si)
        horizontal_10 = chrg.at["1_in_10", "base_charge"] * total_si
        horizontal_10.columns = ["charge"]
        horizontal_20 = chrg.at["1_in_20", "base_charge"] * total_si
        horizontal_20.columns = ["charge"]

        return eq_charge, hail_charge, horizontal_10, horizontal_20

    # Calcualtion to calcualte the natural catastrophe risk
    @log_decorator
    def f_calculate(self):
        """Calculates natural catastrophe risk charges.

        The function aggregates the data supplied by the SCR class.
        After that, the gross natural catastrophe risk is calculated for the
        different diversifition levels.
        Results are returned as a dictionary.

        Parameters:
        ----------
        sam_scr (SCR):
            An SCR class that contains the various SCR inputs

        Returns:
        ----------
        overall_risk_charge (dictionary):
            A dictionary of the gross natural catastrophe risk charges.
        """
        # logger.debug("Function start")

        div_level = self.scr.f_data("data", "data", "diversification_level").iloc[0]
        for calc_type in ("base", "reinsurance", "div_structure"):
            nat_cat_data, base_matrix, df_allocation = self.f_data_aggregation(
                calc_type
            )
            (
                eq_charge,
                hail_charge,
                horizontal_10,
                horizontal_20,
            ) = self.f_cat_calculation(
                nat_cat_data, base_matrix, df_allocation, div_level, calc_type
            )

            self.output[(calc_type, "eq_charge")] = eq_charge
            self.output[(calc_type, "hail_charge")] = hail_charge
            self.output[(calc_type, "horizontal_10")] = horizontal_10
            self.output[(calc_type, "horizontal_20")] = horizontal_20

            # The general guidance requires that for the reinsurance
            # calculation we must allocate the charges proportionately.
            # It is difficult to decide where this should ahppen -
            # and the placement of this calcualtion is a little debatable.
            # Ultimately it has been decided to put the calcualtion here.
            # The same calculation will need to be repeated for factor
            # based catastrophe risk.

            if calc_type == "reinsurance":
                for shck in [
                    "eq_charge",
                    "hail_charge",
                    "horizontal_10",
                    "horizontal_20",
                ]:
                    # Just doign this to keep this a little short
                    data = self.output[("reinsurance", shck)]

                    # We get the index, we are lookign for the total entry.
                    # This should always be the last entry, but we check
                    max_length = max([len(x) for x in data.index])
                    if len(data.index[len(data) - 1]) != max_length:
                        raise Exception(
                            "nat_cat_risk",
                            "f_calculate",
                            "Diversification listing is incorrect",
                            "",
                        )

                    # At this stage we are good to proceed
                    # 20240812 Bug Fix:
                    # T Futter discovered that when there was only a single reinsurance
                    # structure the code rna into issues. It was caused by a duplicate key.
                    # Fixed the code to make sure that index was no longer used.
                    # Also added additional chekcs to prevent similar issues
                    sum_charges = sum(data[:-1]["charge"])
                    chrg_col = data.columns.get_loc("charge")
                    if sum_charges > 0:
                        # Pro-rate the total charge across all of the reinsurance schemes
                        data.iloc[0 : len(data) - 1, chrg_col] = (
                            data.iat[len(data) - 1, chrg_col]
                            * data.iloc[0 : len(data) - 1, chrg_col]
                            / sum_charges
                        )
                    else:
                        # Teh charge is zero, or less than zero
                        # We set the charge equal to 0.
                        data.iloc[0 : len(data) - 1, chrg_col] = 0

                    # We remove the last total row
                    data = data[:-1]
                    # Thsi doesn't seem to work with frozensets
                    # data.drop(index=data.index[-1], axis=0, inplace=True)

                    # Don't think this is needed but does seem to be for some weired reson
                    self.output[("reinsurance", shck)] = data
            # A similar approahc needs to happen for the calculations by
            # division and structure. We will be consistent in our approach
            # and perform the allocation here ecause we knwo that the
            # divsion_structure calcualtion happens last,
            # we have reference the base calculation

            if calc_type == "div_structure":
                for shck in [
                    "eq_charge",
                    "hail_charge",
                    "horizontal_10",
                    "horizontal_20",
                ]:
                    # Just doign this to keep this a little short
                    data = self.output[("div_structure", shck)]
                    # We need to split our tuples out here
                    data[["div", "structure"]] = [
                        np.array([x[0], x[1]], dtype=object) for x in data.index
                    ]

                    # The base data we must use to pro-rate our events
                    base_data = self.output[("base", shck)]

                    data = data[["div", "structure", "charge"]]
                    # We now need to pivot our div data
                    data = pd.pivot_table(
                        data=data,
                        values="charge",
                        index="div",
                        columns="structure",
                        aggfunc="sum",
                    )
                    cols = data.columns.values
                    data["__total__"] = base_data.loc[data.index, "charge"]
                    row_total = data[cols].sum(axis=1)
                    data[cols] = (
                        data[cols]
                        .divide(row_total, axis=0)
                        .multiply(data["__total__"], axis=0)
                    )
                    data = data[cols]

                    self.output[(calc_type, shck)] = data

        return self.output

    def f_data(self, data="", sub_data="info", df=None):
        """Return the output values stored in NatCat class."""

        # Just some cleaning of our inputs to ensure no errors occur
        data = data.lower().strip()
        sub_data = sub_data.lower().strip()

        try:
            if data in ("base", "reinsurance", "div_structure") and sub_data in (
                "earthquake",
                "hail",
                "horizontal 10",
                "horizontal 20",
            ):
                # Deal with some text replacement that needs to happen for the
                # differently calculated charges.
                # Need to maybe look at aligning naming conventions
                if sub_data == "earthquake":
                    sub_data = "eq_charge"
                elif sub_data == "hail":
                    sub_data = "hail_charge"
                else:
                    sub_data = sub_data.replace(" ", "_")

                df = self.output[(data, sub_data)]

                # Reinsurance needs the data in a slightly different format
                # that we accomodate for here
                # Not sure i is the best palce btu ...
                if data == "reinsurance":
                    df = df.T

            elif data in ("div_structure") and sub_data in ("horizontal_combined"):
                df = pd.concat(
                    [
                        self.output[(data, "horizontal_10")],
                        self.output[(data, "horizontal_10")],
                        self.output[(data, "horizontal_10")],
                        self.output[(data, "horizontal_20")],
                    ]
                )
                df = df.groupby(by="div").sum()

            elif data in ("base", "reinsurance", "div_structure") and sub_data in (
                "horizontal"
            ):
                df = pd.concat(
                    [
                        self.output[(data, "horizontal_10")].T,
                        self.output[(data, "horizontal_10")].T,
                        self.output[(data, "horizontal_10")].T,
                        self.output[(data, "horizontal_20")].T,
                    ],
                    ignore_index=True,
                )

            elif data in ("base", "reinsurance", "div_structure") and sub_data in (
                "all"
            ):
                df = self.output[(data, "hail_charge")]
                df = df.rename(columns={"charge": "hail"}, inplace=False)
                for v in [
                    "eq_charge",
                    "horizontal_10",
                    "horizontal_10",
                    "horizontal_10",
                    "horizontal_20",
                ]:
                    tmp = self.output[(data, v)]
                    tmp = tmp.rename(columns={"charge": v}, inplace=False)
                    df = df.merge(tmp, left_index=True, right_index=True, how="outer")

                df.columns = [
                    "hail",
                    "earthquake",
                    "horizontal_1",
                    "horizontal_2",
                    "horizontal_3",
                    "horizontal_4",
                ]
                df["horizontal_total"] = df[
                    ["horizontal_1", "horizontal_2", "horizontal_3", "horizontal_4"]
                ].sum(axis=1)
        except:
            raise ValueError(f"cannot find {data} - {sub_data}")
        else:
            return df.copy(deep=True)
