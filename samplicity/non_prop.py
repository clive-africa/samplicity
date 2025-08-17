"""
A module containing the NonProp class.
"""

# A package for the display of dataframes in the console.
# from tabulate import tabulate
#import logging

import numpy as np
import pandas as pd
from typing import Optional, Union

#logger = logging.getLogger(__name__)

from .helper import allocation_matrix, combins_df_col, log_decorator


class NonProp:
    """
    A class to calculate the gross non-proportional catastrophe risk.

    This class supports the class 'SCR'.

    Attributes
    ----------
        None

    Methods
    -------
    calculate(sam_scr):
    Performs the data manipulation and calcutions required.
    The results are returned as a dictionary.

    .. warning::
        - If the column 'include_non_prop_cat' is left blank it will be defaulted to 'N' and no charge will be calculated for the data point.
        - In performing the calcualtion of the charges for the different reinsurance arrangements, the charges are pro-rated across the different reinsurance treaties.
        - If no reinsurance arrangement (ri_structure) is provided it is defaulted to '__none__'.
    

    """

    @log_decorator
    def __init__(self, sam_scr, class_name="non_prop_cat", calculate=False):
        # logger.debug("Function start")

        self.scr = sam_scr
        """ A reference to the main SCR module."""

        self.output = {}
        """ A dictionary to store all the results of the class. """

        # We get only the rows that we need for the calculation.
        factor_data = self.scr.f_data("data", "data", "prem_res")
        
        factor_data.fillna({"include_non_prop_cat": "N"}, inplace=True)
        factor_data["include_non_prop_cat"] = factor_data["include_non_prop_cat"].map(
            str.upper
        )
        factor_data["include_non_prop_cat"] = factor_data["include_non_prop_cat"].map(
            str.strip
        )
        factor_data = factor_data[factor_data["include_non_prop_cat"] == "Y"]

        # Now we need to map to the correct charge that will be allocated
        # We simply make the charges for 11,12,13 equal to 'credit_guarantee'

        factor_data["lob"] = factor_data["lob"].map(str.upper)
        factor_data["lob"] = factor_data["lob"].map(str.strip)

        factor_data["non_prop_charge"] = "np_property"
        # update=factor_data['lob'] in (11,12,13,'11','12','13')
        factor_data.loc[
            factor_data["lob"].isin([11, 12, 13, "11", "12", "13"]), "non_prop_charge"
        ] = "np_credit_guarantee"

        factor_data[["gross_p_last", "gross_p"]] = factor_data[
            ["gross_p_last", "gross_p"]
        ].fillna(0)

        # We populate the field 'ri_structure' with 'None' where no reinsurance is provided.
        # This avoid countless issues later on in the ocde when delaing with scenarios where
        # users may not populate any reinsurance arrangements.
        factor_data["ri_structure"] = factor_data["ri_structure"].fillna("__none__")

        div_field = self.scr.f_data("data", "data", "diversification_level").iloc[0]
        factor_data["div_structure"] = list(
            factor_data[[div_field, "ri_structure"]].itertuples(index=False, name=None)
        )

        self.output["factor_data"] = factor_data

        self.scr.classes[class_name] = self

        if calculate:
            self.f_calculate()

    def f_indv_calculation(self, calculation_type):
        """Perform calcualtions for each calcaultion type."""

        if calculation_type in ("base", "div_structure"):
            div_field = self.scr.f_data("data", "data", "diversification_level").iloc[0]
            calc_level = self.scr.f_data("data", "data", "calculation_level").iloc[0]
        elif calculation_type == "reinsurance":
            div_field = "ri_structure"
            calc_level = "individual"
        else:
            div_field = div_field
            calc_level = "diversification"

        # For the division structure calcualtion we need to create a special matrix
        # This allows for the calcualtion to be performed in a single step
        if calculation_type == "div_structure":
            lst, _ = combins_df_col(self.output["factor_data"], div_field, calc_level)

            division_list = np.unique(self.output["factor_data"][div_field])

            # Need to allow for scenarios where we do not have any reinsurance
            # arrangements populated. np.unique will not work
            # Thsi was fixed by defualting all of the reinsurance arrangements to 'None'
            structure_list = np.unique(self.output["factor_data"]["ri_structure"])

            new_lst = [(x, y) for x in lst for y in structure_list]
            cols = [(x, y) for x in division_list for y in structure_list]

            matrix = [x[0] in y[0] and x[1] in y[1] for x in cols for y in new_lst]
            matrix = np.reshape(matrix, (len(cols), len(new_lst))).T.astype(int)
            df_allocation = pd.DataFrame(matrix, index=new_lst, columns=cols)
            
            # Now we move back to normal to allow the calculation to take place
            lst = new_lst
            div_field = "div_structure"
        else:
            df_allocation = allocation_matrix(
                self.output["factor_data"], div_field, calc_level
            )

        # Perform the actual calculation here

        factor_data = self.output["factor_data"][
            [div_field, "non_prop_charge", "gross_p_last", "gross_p"]
        ]
        factor_data = factor_data.groupby(
            [div_field, "non_prop_charge"], as_index=False, dropna=False
        ).sum()
        factor_data["p"] = factor_data[["gross_p", "gross_p_last"]].max(axis=1)
        factor_data = factor_data.pivot_table(
            "p", "non_prop_charge", div_field, aggfunc="sum"
        ).fillna(0)

        factor_data_allocate = factor_data.dot(df_allocation[factor_data.columns].T).T
        # Issue si occuring here the reinsurance is returning two values
        # but only a single column
        # Need to chekc the reason for this.
        # Could just be when there is a single 'None' reinsurance structure.
        factor_data_allocate.index = df_allocation.index
        factor_data_allocate[factor_data_allocate < 0] = 0

        for var in ("np_property", "np_credit_guarantee"):
            factor_data_allocate[var] = factor_data_allocate.get(var, 0)

        # Now we need to
        # calc_cahrge={}
        calc_charge = pd.DataFrame(
            0.0,
            columns=["np_property", "np_credit_guarantee"],
            index=factor_data_allocate.index,
        )
        calc_charge["np_property"] = factor_data_allocate["np_property"] * 2.5
        calc_charge["np_credit_guarantee"] = (
            factor_data_allocate["np_credit_guarantee"] * 1.5
        )

        return calc_charge

    @log_decorator
    def f_calculate(self):
        """Perform calcualtions for all the calcaultion types."""
        # logger.debug("Function start")

        # We only follow the rest of the steps if we have data to work with
        if self.output["factor_data"] is None or len(self.output["factor_data"]) == 0:
            return None

        # Create all the combinations that we need for the calculation.
        for calc in ("base", "reinsurance", "div_structure"):
            result = self.f_indv_calculation(calc)

            # The general guidance requires that for the reinsurance
            # calculation we must allocate the charges proportionately.
            # It is difficult to decide where this should happen -
            # and the placement of this calculation is a little debatable.
            # Ultimately it has been decided to put the calcualtion here.
            # For factor cat thsi is alsmost always not necessary as the
            # charges are linear but could be necessary where premiums are
            # negative. The same calculation will need to be repeated for
            # factor based catastrophe risk.
            if calc == "base":
                self.output[calc] = result

            elif calc == "reinsurance":
                # We get the index, we are looking for the total entry.
                # This should always be the last entry, but we check
                max_length = max([len(x) for x in result.index])
                if len(result.index[len(result) - 1]) != max_length:
                    raise Exception(
                        "non_prop",
                        "f_calculate",
                        "Diversification listing is incorrect",
                        "",
                    )

                # At this stage we are good to proceed
                # This formula is slightly more complex than nat_cat as we
                # vectorise the calculation. In these steps we are proportionately
                # pro-rating the total charge across the different reinsurance treaties.
                # We do this for all of the columns in the matrix in one step
                sum_charges = (
                    result.sum(axis=0) - result.loc[[result.index[len(result) - 1]], :]
                )
                sum_charges.reset_index(inplace=True, drop=True)
                result.iloc[0 : len(result) - 1, :] = (
                    result.iloc[0 : len(result) - 1, :]
                    .div(sum_charges.values[0])
                    .mul(result.values[len(result) - 1])
                    .fillna(0)
                )

                # We remove the last total row
                result = result[:-1]
                result["np_total"] = np.sqrt(
                    np.square(result["np_property"])
                    + np.square(result["np_credit_guarantee"])
                )

                self.output[calc] = result

            # A similar approahc needs to happen for the calculations by
            # division and structure. We will be consistent in our approach
            # and perform the allocation here.
            # Because we knwo that the divsion_structure calcualtion
            # happens last, we have reference the base calculation

            elif calc == "div_structure":
                # Just doign this to keep this a little short
                # We need to split our tuples out here

                # We are creating two columsn with the division and structure
                result[["div", "structure"]] = [
                    np.array([x[0], x[1]], dtype=object) for x in result.index
                ]

                # The base data we must use to pro-rate our events
                base_data = self.output["base"]

                temp_result = {}
                #perils = pd.Series(["np_property", "np_credit_guarantee"])
                for p in ["np_property", "np_credit_guarantee"]:
                    df = pd.pivot_table(
                        data=result[["div", "structure", p]],
                        values=p,
                        index="div",
                        columns="structure",
                        aggfunc="sum",
                    ).fillna(0)
                    cols = df.columns.values
                    df_total = base_data.loc[df.index, p].iloc[0]
                    if df_total != 0:
                        row_total = df[cols].sum(axis=1)
                        df[cols] = (
                            df[cols]
                            .divide(row_total, axis=0)
                            .multiply(df_total, axis=0)
                        )

                    temp_result[p] = df

                self.output[calc] = temp_result

        return result

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

            if data == "div_structure":
                df = self.output[data][sub_data]
            elif sub_data != "np_all":
                df = self.output[data][[sub_data]]
            elif sub_data == "np_all":
                df = self.output[data]

            if data == "reinsurance":
                df = df.T
        except Exception as e:
            raise ValueError(f"Cannot find {data} - {sub_data}") from e
            return None
        else:
            return df.copy(deep=True)
