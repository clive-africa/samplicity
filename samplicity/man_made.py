"""
A module containing the ManMade class.
"""

import pandas as pd
from typing import Union
import logging

from .helper import log_decorator
logger = logging.getLogger(__name__)


class ManMade:
    """A class to 'calculate' the man-made catastrophe risk.

    The majority of the man made inputs are manual.
    This class, for now, just helps to aggregate the charges and import them
    into the SCR calculation. An approximation is used in that the different
    divisions are assumed to take the summation of each level below.
    Reality is that the event could technically increase across product lines,
    or there could be a diversification benefit. This is an approximation.

    Attributes
    ----------

    Methods
    -------
    __init__:
        Creates the various dictionaries that will be used by the class.
    f_calculate:
        Performs the 'calculation' of the man-made CAT.

    """

    @log_decorator
    def __init__(
        self, sam_scr, class_name: str = "man_made_cat", calculate: bool = False
    ):
        #logger.debug("Function start")

        self.output = {}
        """A dictionary that will store all of the results of the class."""
        self.scr = sam_scr
        """Store a reference to the main SCR class with all the metadata."""

        self.scr.classes["man_made_cat"] = self

        if calculate:
            self.f_calculate()
    
    @log_decorator
    def f_calculate(self):
        """Aggregate the inputs to return the gross man-made charges."""
        #logger.debug("Function start")

        # RETRIEVE THE DATA WE NEED FOR THE CALCULATION

        div_field = self.scr.f_data("data", "data", "diversification_level").iloc[0]

        # To ensure that we get the overall view right we calculate
        # (and store) these inputs seperately
        overall = self.scr.f_data("data", "data", "man_made_overall")
        overall = overall[["gross_event"]].astype(float).fillna(0)
        overall = overall.T

        # The inputs for each division are stored in a seperate location
        # This is doen to make sure that the overall figures are correct.
        man_made_perils = overall.columns.tolist()
        man_made = self.scr.f_data("data", "data", "man_made_division_event")
        man_made[man_made_perils] = man_made[man_made_perils].astype(float).fillna(0)
        man_made = man_made[[div_field] + man_made_perils]
        
        # We now get the list of different product combinations.
        div_list = (
            self.scr.f_data("scr", "list_combinations").iloc[:, 0].values.tolist()
        )

        # PERFORM DATA CHECKS

        # We need to find the total row
        # Thsi will be the one with all the divisions in the index
        max_element = [len(x) for x in div_list]

        # Thsi should be the last element in our dataframe,
        # otherwise there has been and error.
        # We are relying on how the combinations function works.
        if max_element[len(max_element) - 1] != max(max_element):
            raise Exception(
                "man_made", "f_calculate", "Diversification listing is incorrect", ""
            )

        # GROSS CALCULATION

        # We calcaulte the gross event figures for all combinations.
        # Users input values for each division
        # The assumption is that we can jsut add figures together.
        # Thsi is an approximation that is wrong
        # May need to revisit this calcualtion

        self.output["man_made_cat"] = self.f_gross_event(
            div_field, div_list, man_made, overall
        )

    def f_gross_event(
        self,
        div_field: str,
        div_list: list,
        man_made: pd.DataFrame,
        overall: pd.DataFrame,
    ) -> pd.DataFrame:
        """Aggregate the inputs to return the gross man-mande charges."""
        #logger.debug("Function start")

        # We remove the total row, form the division listin
        # We foucs on all the other combinations
        # Teh total will be added later

        mm_agg = pd.DataFrame(div_list[:-1], index=div_list[:-1])
        mm_agg = (
            mm_agg.stack().to_frame(name="div_field").reset_index(drop=True, level=1)
        )
        mm_agg["index"] = mm_agg.index

        # We are creating a normalised view to allow us to join to the data
        # stored in man_made. We need to split all of the tuples into their
        # components parts.
        # We join all the events, we will late sum them.
        # We are assuming that all man-made events should be summed
        # See the statements made above.
        mm_agg = mm_agg.merge(
            man_made, left_on="div_field", right_on=div_field, how="left"
        )

        # We only care about the perild, we can drop the joining field
        mm_agg = mm_agg.drop(["div_field", div_field], axis=1)

        # Add bakc the overall event to the dataframe list
        overall["index"] = [frozenset(div_list[len(div_list) - 1])]
        # Fill the blanks, there will be, to ensure the sums work
        # We know that our data arrives here all sorted.
        mm_agg = pd.concat([mm_agg, overall])

        # At this stage we have a single row for eahc division combination
        mm_agg = mm_agg.groupby(by="index", as_index=True).sum()

        return mm_agg

    def f_data(
        self, data: str = "", sub_data: str = "info", df: pd.DataFrame = None
    ) -> Union[pd.DataFrame, None]:
        """Return the output values stored in the MAN_MADE classes."""
        #logger.debug("Function start")

        try:
            # Just some cleaning of our inputs to ensure no errors occur
            data = data.lower().strip()
            sub_data = sub_data.lower().strip()

            if data == "perils":
                df = pd.DataFrame(
                    self.output["man_made_cat"].columns.values, columns=["heading"]
                )
            elif sub_data == "all":
                df = self.output[data]
            else:
                df = self.output[data][sub_data]
        except:
            logger.critical(f"Error: {data} - {sub_data}")
            raise ValueError(f"cannot find {data} - {sub_data}")
        else:
            if not df is None:
                df = df.copy(deep=True)
            return df

