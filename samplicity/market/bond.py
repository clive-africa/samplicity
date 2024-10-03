# -*- coding: utf-8 -*-
"""
Created on Sat Feb 11 18:55:30 2023

@author: chogarth
"""
import numpy as np
import pandas as pd
import datetime
from scipy.optimize import newton

# import pandasql as ps
# import datetime
from dateutil import relativedelta
import math

#import logging
from typing import List, Union
import numpy as np
from scipy.optimize import newton
from typing import Tuple
import pandas as pd
import numpy as np

from ..helper import log_decorator

#logger = logging.getLogger(__name__)
#

class BOND_VAL:
    #@log_decorator
    def __init__(self, val_date, real_curve, nominal_curve, shock_interest_rate):
        #logger.debug("Function start")
        # We need to populate the reisnurance data with all of the parameters

        # We get the forward rate curve and convert it to daily
        # We are going overkill but auditors love to check market risk in extreme detail so we need to allow for this.
        # Have had many an audit query on assuming cashflows at the begiining or end of the month
        # I don't bleeive this calcualtion is appropriate for non-life insurers

        self.val_date = val_date

        risk_curve = nominal_curve
        risk_curve = risk_curve.merge(real_curve, on=["start_date", "end_date"])
        risk_curve.columns = ["start_date", "end_date", "nominal", "real"]
        # shock_interest_rate=metadata['shock_interest_rate']

        # Resolve issues about leap years
        # self.val_date=sam_scr.data_files['base_inputs'].at['valuation_date','base_inputs'].date()
        # asset=sam_scr.data_files['asset_data']

        # Need to llok at moving the end date to the last maturity date of of assets.
        # This could lengthen the calculation in an extreme event.
        end_date = risk_curve.loc[len(risk_curve) - 1, "end_date"]
        date_range = pd.date_range(self.val_date, end_date, freq="d")
        interest_curve = date_range.to_frame(index=False, name="date_range")
        interest_curve["date_range"] = pd.to_datetime(
            interest_curve["date_range"]
        ).dt.date

        # The where works on a not function
        # A little bit frsutrating but the 'leap year' function can only be applied to as date range.
        interest_curve["days_year"] = 365
        interest_curve["days_year"] = interest_curve["days_year"].where(
            np.logical_not(date_range.is_leap_year), 366
        )

        # For soem reaossn the merge_asof function needs these to be in the format of Pydatetime
        # We replaced the the pandassql code as it works a lot faster.
        # interest_curve["date_range"] = np.array(pd.to_datetime(
        #     interest_curve["date_range"], format="%Y-%m-%d"
        # ).dt.to_pydatetime())
        # risk_curve["end_date"] = np.array(pd.to_datetime(
        #     risk_curve["end_date"], format="%Y-%m-%d"
        # ).dt.to_pydatetime())
        interest_curve["date_range"] = pd.to_datetime(
            interest_curve["date_range"], format="%Y-%m-%d")
        risk_curve["end_date"] =pd.to_datetime(
            risk_curve["end_date"], format="%Y-%m-%d")
        interest_curve = pd.merge_asof(
            interest_curve,
            risk_curve[["end_date", "nominal", "real"]],
            left_on="date_range",
            right_on="end_date",
            direction="forward",
        )
        interest_curve.drop("end_date", inplace=True, axis=1)
        # The interest rate is not zero.
        # However, for our calcualtions we don't need an interest rate here
        # Cahsflows are assumed to occur at the end of the date so disocunting doesn't apply to the frist date
        # The first date is the valuation date
        interest_curve.loc[0, ["nominal", "real"]] = 0
        # Get the duration for our calculation
        # We are cheating a bit here and abusing the fact that the index will start at 0.
        interest_curve["duration"] = interest_curve.index / interest_curve["days_year"]

        # We convert our forward rates into a series of spot rates
        # We leave them here are accumulation factors

        for crv in ["nominal", "real"]:
            # The calcualtion is numpy is significantly faster than in pandas.
            # Hence we do the calcualtion in numpy and populate our dataframe later
            # This is particularly with the cumprod function.
            # We make sure that we explicitely convert the data to a numpy array.
            tmp = np.cumprod(
                np.power(
                    1 + interest_curve[crv].to_numpy(),
                    1 / interest_curve["days_year"].to_numpy(),
                )
            )
            np.nan_to_num(tmp, copy=False, nan=1)
            interest_curve["accum_" + crv] = tmp
            interest_curve["disc_" + crv] = 1 / tmp
            interest_curve["annual_spot_" + crv] = (
                interest_curve["accum_" + crv].pow(
                    interest_curve["days_year"] / interest_curve.index
                )
                - 1
            )

        # We apply the base shock here
        for shock in ["nominal_up", "nominal_down", "real_up", "real_down"]:
            curve = "annual_spot_" + shock.replace("_up", "").replace("_down", "")
            # Using numpy for the interpolation is a lot faster than doing it manually.
            interest_curve["spot_" + shock] = interest_curve[curve] * (
                1
                + np.interp(
                    interest_curve["duration"],
                    shock_interest_rate["maturity"],
                    shock_interest_rate[shock],
                )
            )

        # Now we need to apply the minimum shcoks that are equired per the FSI
        # THis is a minimum shock of -1% and 1%
        for crv in ["nominal", "real"]:
            interest_curve["spot_" + crv + "_down"] = interest_curve[
                "spot_" + crv + "_down"
            ].where(
                interest_curve["spot_" + crv + "_down"]
                < interest_curve["annual_spot_" + crv] - 0.01,
                interest_curve["annual_spot_" + crv] - 0.01,
            )
            interest_curve["spot_" + crv + "_up"] = interest_curve[
                "spot_" + crv + "_up"
            ].where(
                interest_curve["spot_" + crv + "_up"]
                > interest_curve["annual_spot_" + crv] + 0.01,
                interest_curve["annual_spot_" + crv] + 0.01,
            )
        # For nominal rates there is a requirement that the interest rate should not be below 0.

        # Now we need to multiply by the different shocks for the different columns
        interest_curve["spot_nominal_down"] = interest_curve["spot_nominal_down"].where(
            interest_curve["spot_nominal_down"] > 0, 0
        )
        interest_curve.loc[
            0,
            ["spot_nominal_down", "spot_nominal_up", "spot_real_down", "spot_real_up"],
        ] = 0

        for crv in [
            "spot_nominal_down",
            "spot_nominal_up",
            "spot_real_down",
            "spot_real_up",
        ]:
            interest_curve["disc_" + crv.replace("spot_", "")] = np.power(
                1 + interest_curve[crv], -1 * interest_curve["duration"]
            )

        # interest_curve.index=pd.to_datetime(interest_curve['date_range']).dt.date
        interest_curve.index = interest_curve["date_range"]

        # Need to remvoe some columns here
        self.interest_curve = interest_curve

    #@log_decorator
    def f_calculate(self, asset):
        """Calculate the present value of a bond."""
        #logger.debug("Function start")

        # The data needed for our calculations
        maturity_date = asset["maturity_date"]
        coupon_freq = asset["coupon_freq"]
        spread = np.nan_to_num(asset["spread"], nan=0.0)
        bond_type = asset["bond_type"]
        coupon = np.nan_to_num(asset["coupon"], nan=0.0)
        nominal_value = asset["nominal_value"]
        market_value = asset["market_value"]

        # Entries used for debugging purposes
        asset_desc = asset["asset_description"]
        asset_id = asset["id"]

        # Some data chekcs on the bond data
        if np.isnan(coupon_freq):
            raise ValueError(
                f"A coupon frequency must be populated: {asset_id} {asset_desc}."
            )

        try:
            # We determined the number of coupon payments there will be
            iterations = relativedelta.relativedelta(maturity_date, self.val_date)
            # We add one to be safe in case the calculation miscalxulates
            iterations = iterations.years * 12 + iterations.months + 1
            # Now we determine the coupon payments
            iterations = math.ceil(iterations * coupon_freq / 12)

            # Get the dates of the various coupon payments
            date_range = (
                pd.Index(
                    [
                        maturity_date
                        + pd.offsets.DateOffset(months=-i * 12 / coupon_freq)
                        for i in range(iterations)
                    ]
                )
                .to_series()
                .dt.date
            )
            date_range = date_range[date_range > self.val_date]
            date_range = pd.to_datetime(date_range).dt.date

            # Standrd fixed interest bond where the coupon is fixed
            if bond_type == "fixed":
                res = f_fixed(
                    coupon,
                    nominal_value,
                    market_value,
                    coupon_freq,
                    date_range,
                    self.interest_curve,
                )

            # Thsi is a floating rate note where the coupon paid is based on the 3 month interest rate & the coupon is calculated at the exact date of payment.
            # In reality this is not correct, there is usually a time delay.
            elif bond_type == "floating_3_0":
                res = f_floating(
                    spread,
                    nominal_value,
                    market_value,
                    coupon_freq,
                    date_range,
                    self.interest_curve,
                )
        except:
            raise ValueError(f"Error with {asset_id} - {asset_desc}")
            # bond_valuation=None
            # bond_duration=None
            # ytm=None
            res = tuple(None) + tuple(None) + tuple(None)

        #logger.debug("Function end")

        return res

def f_newton_calc(
    cashflows: List[float], 
    duration: float, 
    market_value: float, 
    initial_guess: float = 0
) -> float:
    """
    Solve the yield to maturity.

    Parameters:
    cashflows (array-like): The cashflows of the bond.
    duration (float): The duration of the bond.
    market_value (float): The market value of the bond.
    initial_guess (float, optional): The initial guess for the yield to maturity. Defaults to 0.

    Returns:
    float: The yield to maturity of the bond.
    """
    #logger.debug("Function start")

    def f(i: float) -> float:
        return float(market_value) - float(np.dot(cashflows, np.exp(-i * duration)))

    root, status = newton(f, initial_guess, full_output=True, disp=True, tol=0.0001)
    if status.converged:
        return np.exp(root) - 1
    else:
        return np.nan


def f_fixed(
    coupon: float,
    nominal_value: float,
    market_value: float,
    coupon_freq: int,
    date_range: List[datetime.date],
    interest_curve: pd.DataFrame
) -> Tuple[float, float, float]:
    """
    Calculate the Yield to Maturity (YTM), bond duration, and present value of a fixed interest bond.

    Args:
        coupon (float): The coupon rate of the bond.
        nominal_value (float): The nominal value of the bond.
        market_value (float): The market value of the bond.
        coupon_freq (int): The frequency of coupon payments per year.
        date_range (List[datetime.date]): The list of dates representing the bond's cash flow periods.
        interest_curve (pd.DataFrame): The interest curve containing discount factors and durations.

    Returns:
        Tuple[float, float, float]: A tuple containing the bond valuation, bond duration, and YTM.

    """
    #logger.debug("Function start")

    # Get the discount curve we will be using
    discount_curve = interest_curve.loc[
        date_range, ["disc_nominal", "disc_nominal_down", "disc_nominal_up"]
    ]

    cashflows = [coupon * nominal_value / coupon_freq] * len(date_range)
    cashflows[0] = cashflows[0] + nominal_value
    cashflows_mult_dur = cashflows * interest_curve.loc[date_range, "duration"]

    bond_valuation = np.einsum("i,il->l", cashflows, discount_curve).astype(float)
    bond_duration = np.einsum("i,il->l", cashflows_mult_dur, discount_curve).astype(
        float
    )

    ytm = f_newton_calc(
        cashflows,
        interest_curve.loc[date_range, "duration"],
        market_value,
        initial_guess=0.0,
    ).astype(float)

    # We now need to calculate the discounted mean term of the bonds
    # Convert to float to deal with some boundary cases.
    bond_duration = bond_duration.astype(float) / bond_valuation.astype(float)

    # bond_valuation should be a tuple of 3 values
    return tuple(bond_valuation) + tuple([bond_duration[0]]) + tuple([ytm])

def f_floating(
    spread: float,
    nominal_value: float,
    market_value: float,
    coupon_freq: int,
    date_range: pd.DatetimeIndex,
    interest_curve: pd.DataFrame
) -> Tuple[float, float, float]:
    """
    Calculate YTM, bond duration, and present value of a floating bond.

    Parameters:
    - spread (float): The spread of the bond.
    - nominal_value (float): The nominal value of the bond.
    - market_value (float): The market value of the bond.
    - coupon_freq (int): The frequency of the bond's coupon payments.
    - date_range (pandas.DatetimeIndex): The date range for the bond's cash flows.
    - interest_curve (pandas.DataFrame): The interest curve used for discounting.

    Returns:
    - bond_valuation (float): The present value of the bond's cash flows.
    - bond_duration (float): The duration of the bond.
    - ytm (float): The yield to maturity of the bond.
    """
    #logger.debug("Function start")

    # Get the discount curve we will be using
    discount_curve = interest_curve.loc[
        date_range, ["disc_nominal", "disc_nominal_down", "disc_nominal_up"]
    ]

    current_spot = interest_curve.loc[
        date_range, ["disc_nominal", "disc_nominal_down", "disc_nominal_up"]
    ]
    future_spot = interest_curve.loc[
        date_range + pd.offsets.DateOffset(months=3),
        ["disc_nominal", "disc_nominal_down", "disc_nominal_up"],
    ]
    future_spot["date"] = future_spot.index.values
    current_spot["date"] = current_spot.index.values
    future_spot.index = current_spot.index

    # We don't multiply only to divide by coupon frequency, All contained in one
    date_diff = (
        future_spot.at[future_spot.index[0], "date"]
        - current_spot.at[current_spot.index[0], "date"]
    ) / np.timedelta64(1, "D")
    date_diff = (
        date_diff
        / interest_curve.loc[
            current_spot.at[current_spot.index[0], "date"], "days_year"
        ]
    )

    coupon = (
        current_spot[["disc_nominal", "disc_nominal_down", "disc_nominal_up"]]
        / future_spot[["disc_nominal", "disc_nominal_down", "disc_nominal_up"]]
        - 1
    ) + spread * date_diff
    coupon[coupon < 0] = 0
    cashflows = nominal_value * coupon

    cashflows.iloc[0, :] = cashflows.iloc[0, :] + nominal_value
    cashflows_mult_dur = cashflows.multiply(
        interest_curve.loc[date_range, "duration"], axis=0
    )

    # Perform the calculations
    bond_valuation = np.einsum("il,il->l", cashflows, discount_curve).astype(float)
    bond_duration = np.einsum("il,il->l", cashflows_mult_dur, discount_curve).astype(
        float
    )

    ytm = f_newton_calc(
        cashflows["disc_nominal"].fillna(0),
        interest_curve.loc[date_range, "duration"],
        market_value,
        initial_guess=0.00,
    ).astype(float)

    # We now need to calculate the discounted mean term of the bonds
    # Convert to float to deal with some boundary cases.
    bond_duration = bond_duration / bond_valuation

    return tuple(bond_valuation) + tuple([bond_duration[0]]) + tuple([ytm])
