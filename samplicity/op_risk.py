"""
op_risk.

A module containing the OpRisk class.
This class is used to calculate the operational risk as 
part of the non-life SCR.

@author: chogarth
"""
from __future__ import annotations

from typing import Dict, Optional
import pandas as pd
import logging

from .helper import log_decorator, allocation_matrix
#from .scr import SCR  # Import the SCR class

logger = logging.getLogger(__name__)

class OpRisk:
    """
    Class to calculate operational risk.

    Attributes:
        scr (SCR): A reference to the main SCR class.
        output (Dict[str, pd.DataFrame]): Store all of the outputs from the calculation.

    Methods:
        f_calculate(): Calculate operational risk charges.
        f_data(data: Optional[str] = None, sub_data: Optional[str] = None) -> pd.DataFrame: Output values that are stored with the OpRisk class.
    """

    @log_decorator
    def __init__(self, sam_scr: 'SCR', class_name: str = "op_risk", calculate: bool = True) -> None:
        """
        Initialize the OpRisk class.

        Args:
            sam_scr (SCR): Reference to the main SCR class.
            class_name (str): Name of the class. Defaults to "op_risk".
            calculate (bool): Whether to calculate immediately after initialization. Defaults to True.
        """
        self.scr: 'SCR' = sam_scr
        self.output: Dict[str, pd.DataFrame] = {}

        # Add the class to the SCR object
        self.scr.classes[class_name] = self

        if calculate:
            self.f_calculate()

    @log_decorator
    def f_calculate(self) -> bool:
        """
        Calculate operational risk charges.

        This method calculates the operational risk charges based on the provided data.
        It performs various calculations and generates the output for premium, provisions,
        and operational risk.

        Returns:
            bool: True if the calculation is successful, False otherwise.

        Raises:
            Exception: If an unknown error occurs during the calculation.
        """
        try:
            # Get the premium and reserve data
            pr_data: pd.DataFrame = self.scr.f_data("data", "data", "prem_res")

            # Get the diversification fields
            div_field: str = self.scr.f_data("data", "data", "diversification_level").iloc[0]
            calc_level: str = self.scr.f_data("data", "data", "calculation_level").iloc[0]

            # Generate allocation matrix
            df_allocation: pd.DataFrame = allocation_matrix(pr_data, div_field, calc_level)

            # Group our data by the diversification field
            pr_data.loc[:, ["gross_p_last", "gross_p_last_24", "gross_claim", "gross_other"]] = (
                pr_data[["gross_p_last", "gross_p_last_24", "gross_claim", "gross_other"]].fillna(0)
            )
            pr_data["gross_tech_prov"] = pr_data["gross_claim"] + pr_data["gross_other"]

            pr_data = (
                pr_data[[div_field, "gross_p_last", "gross_p_last_24", "gross_tech_prov"]]
                .groupby(by=div_field)
                .sum()
            )

            # Perform matrix multiplication
            pr_data = df_allocation[pr_data.index].dot(pr_data)

            # Calculate the growth in excess of 20%
            pr_data["excess_prem_growth"] = (
                pr_data["gross_p_last"] - 1.2 * pr_data["gross_p_last_24"]
            )

            # Remove negative values
            pr_data[pr_data < 0] = 0

            # Calculate operational risk components
            pr_data["op_premium"] = (
                0.03 * pr_data["gross_p_last"] + 0.03 * pr_data["excess_prem_growth"]
            )
            pr_data["op_prov"] = 0.03 * pr_data["gross_tech_prov"]

            # Take the greater of premium and provisions based
            pr_data["op_risk"] = pr_data[["op_premium", "op_prov"]].max(axis=1)

            self.output["premium"] = pr_data[["op_premium"]]
            self.output["provisions"] = pr_data[["op_prov"]]
            self.output["operational_risk"] = pr_data[["op_risk"]]

            return True

        except Exception as e:
            logger.exception("Unknown error in OpRisk calculation")
            raise Exception("op_risk", "calculate", "Unknown error", str(e))

    def f_data(self, data: Optional[str] = None, sub_data: Optional[str] = None) -> pd.DataFrame:
        """
        Return output values stored with the OpRisk class.

        Args:
            data (Optional[str]): The main data category to retrieve. Defaults to None.
            sub_data (Optional[str]): The sub-category of data to retrieve. Defaults to None.

        Returns:
            pd.DataFrame: The requested data as a DataFrame.

        Raises:
            ValueError: If the requested data cannot be found.
        """
        try:
            data = data.lower().strip() if data else ""
            sub_data = sub_data.lower().strip() if sub_data else ""

            if data in ("premium", "provisions", "operational_risk"):
                if sub_data in ("op_premium", "op_prov", "op_risk") or sub_data == "all" or sub_data is None:
                    df = self.output[data]
                else:
                    raise ValueError(f"Cannot find {data} - {sub_data}")
            else:
                raise ValueError(f"Cannot find {data} - {sub_data}")
        except Exception as e:
            logger.critical(f"Error: {data} - {sub_data}")
            raise ValueError(f"Cannot find {data} - {sub_data}") from e
        else:
            return df.copy(deep=True) if df is not None else pd.DataFrame()