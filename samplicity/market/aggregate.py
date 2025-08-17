import pandas as pd
import math
import numpy as np

from ..helper import log_decorator

#@log_decorator
def f_aggregate_market(mkt_risk):
    """Aggregate the various market risk charges."""

    sum_data = mkt_risk.output["summary_data"].copy(deep=True)

    # First we dela with interest rate curve shcoks
    # For now we ignore the asset shcoks, need to address that
    int_rate_nominal = sum_data[
        ["int_curve_nominal_up", "int_curve_nominal_down"]
    ].max(axis=1)
    int_rate_real = sum_data[["int_curve_real_up", "int_curve_real_down"]].max(
        axis=1
    )

    sum_data["interest_rate_curve_nominal"] = int_rate_nominal
    sum_data["interest_rate_curve_real"] = int_rate_real
    sum_data["interest_rate_curve"] = np.sqrt(
        int_rate_nominal**2
        + 2 * 0.25 * int_rate_nominal * int_rate_real
        + int_rate_real**2
    )
    sum_data["result_interest_rate_risk"] = np.sqrt(
        sum_data["interest_rate_curve"] ** 2
        + 2 * 0.5 * sum_data["interest_rate_curve"] * sum_data["int_volatility"]
        + sum_data["int_volatility"] ** 2
    )

    # Now we calculate the various equity risk shocks
    equity_price = sum_data[
        [
            "equity_price_global",
            "equity_price_sa",
            "equity_price_infrastructure",
            "equity_price_other",
        ]
    ]
    equity_corr = mkt_risk.scr.f_data("data", "metadata", "corr_equity_price")
    # equity_price_charge
    sum_data["equity_price"] = pd.DataFrame(
        np.sqrt(
            np.einsum("ij,jk,ki->i", equity_price, equity_corr, equity_price.T)
        ),
        index=equity_price.index,
        columns=["charge"],
    )

    sum_data["equity_risk"] = np.sqrt(
        sum_data["equity_price"] ** 2
        + 2 * 0.5 * sum_data["equity_price"] * sum_data["equity_volatility"]
        + sum_data["equity_volatility"] ** 2
    )

    # Now need for further calculations on property risk

    # Now we calculate the currency risk
    sum_data["currency_risk"] = sum_data["currency_up"].where(
        sum_data["currency_up"] > sum_data["currency_down"],
        sum_data["currency_down"],
    )
    sum_data["currency_risk"] = sum_data["currency_risk"].where(
        sum_data["currency_risk"] > 0, 0
    )

    # Now we calculate spread risk
    sum_data["spread_credit"] = sum_data["spread_credit_up"].where(
        sum_data["spread_credit_up"] > sum_data["spread_credit_down"],
        sum_data["spread_credit_down"],
    )
    sum_data["spread_credit"] = sum_data["spread_credit"].where(
        sum_data["spread_credit"] > 0, 0
    )
    sum_data["spread_risk"] = (
        sum_data["spread_interest"] + sum_data["spread_credit"]
    )

    # We now calcualte default risk

    # We bring the result sin from the credit (type 1 default rick charge.
    # These were calculated independantly from the other charges.
    sum_data["credit_type_1"] = mkt_risk.output["credit_type_1_charge"]["result"]
    sum_data["concentration_risk"] = mkt_risk.output["concentration_risk_charge"][
        "result"
    ]

    sum_data["default_risk"] = np.sqrt(
        sum_data["credit_type_1"].fillna(0) ** 2
        + 2
        * 0.75
        * sum_data["credit_type_1"].fillna(0)
        * sum_data["credit_type_2"].fillna(0)
        + sum_data["credit_type_2"].fillna(0) ** 2
    ) + sum_data["credit_type_3"].fillna(0)

    # COmbined spread and default risk
    sum_data["spreak_and_default_risk"] = (
        sum_data["spread_risk"] + sum_data["default_risk"]
    )

    # Manipulate our data to put in zero where the charge doesn't apply
    # Allows use a single consistent matrix across the calculation

    interest_up = sum_data["result_interest_rate_risk"]
    interest_up.where(
        sum_data["int_curve_nominal_up"] >= sum_data["int_curve_nominal_down"],
        other=0,
        inplace=True,
    )
    interest_down = sum_data["result_interest_rate_risk"]
    interest_down.where(
        sum_data["int_curve_nominal_up"] < sum_data["int_curve_nominal_down"],
        other=0,
        inplace=True,
    )

    currency_up = sum_data["currency_up"].where(
        sum_data["currency_up"] >= sum_data["currency_down"], other=0
    )
    currency_down = sum_data["currency_up"].where(
        sum_data["currency_up"] < sum_data["currency_down"], other=0
    )

    # Create a dataframe that we will use for the correlation calculation
    corr_data = pd.DataFrame(
        {
            "interest_up": interest_up,
            "interest_down": interest_down,
            "equity": sum_data["equity_risk"],
            "property": sum_data["property"],
            "spread_and_default": sum_data["spreak_and_default_risk"],
            "currency_up": currency_up,
            "currency_down": currency_down,
            "concentration": sum_data["concentration_risk"],
            "illiquidity": sum_data["illiquidity"],
        }
    )
    # Calculate
    corr_market = mkt_risk.scr.f_data("data", "metadata", "corr_market")

    sum_data["total_market"] = np.sqrt(
        np.einsum("ij,jk,ki->i", corr_data, corr_market, corr_data.T)
    )

    """
    
    Need to add concentration and counterparty default (type 1) rsisk here.
    Still need to clarify how to treat the collateral in the calcualtion.
    
    """

    # We get the sum assets that will be sued for our calculation
    # conc_total_assets=self.credit_data['conc_assets'].sum()
    # self.credit_data.merge(sam_scr.)

    # Now we need to use a bit of a hack to the correlation matrix.
    # Effectivley we will be adding entires to the matrix

    return sum_data