import numpy as np
import pandas as pd
import math


import logging

logger = logging.getLogger(__name__)


def f_apply_ri_prog(rein_prog, contract, gross_event, struc_share):
    """Apply the reinsurance programme to the event."""
    #logger.debug("Function start")
    # First we need to see if we need a datafrme to store alll of our recoveries
    # by strucure and counterparty.
    if not isinstance(struc_share, pd.DataFrame):
        struc_share = pd.DataFrame(
            0.0,
            columns=list(rein_prog.columns) + ["__total__", "total_counterparty_share"],
            index=rein_prog.index,
        )
        # Update the dataframe to have the counterparty share in the dataframe
        struc_share["total_counterparty_share"] = contract.loc[
            struc_share.index, "total_counterparty_share"
        ].astype(float)

    # We let the net event be equal to the gross event
    # There is not reinsurance at this stage
    event_idx = gross_event.index[0]
    net_event = gross_event

    cols = gross_event.columns

    gross_event["__total__"] = gross_event[cols].sum(axis=1)
    net_event["__total__"] = gross_event[cols].sum(axis=1)

    first_loop = True
    prior_ri_idx = ri_idx = None

    # Loop though the reinsurance programme
    for ri_idx in rein_prog.index.values:
        # for j in range(len(rein_prog)):
        # print(j)

        # ri_idx = list(rein_prog.index)[j]
        # ri_idv = contract.loc[ri_idx].to_dict()
        ri_idv = contract.loc[ri_idx].to_dict()
        # Mkae sure we pass floats to the function
        # ri_idv = {key: float(value) for key, value in ri_idv.items()}

        skip_calc = rein_prog.loc[ri_idx, :].isnull()
        include_calc = np.logical_not(skip_calc)
        # The last columns is always the total
        include_list = list(include_calc) + [False]

        # We only do the comparison after the first loop
        if first_loop:
            first_loop = False
        else:
            # First check if the order has been updated
            update_values = rein_prog.loc[ri_idx, :] != rein_prog.loc[prior_ri_idx, :]

            update_values[skip_calc] = False
            update_list = list(update_values) + [False]
            # We want to make sure we remove the total column
            gross_event.loc[:, update_list] = net_event.loc[:, update_list]
            gross_event["__total__"] = gross_event.loc[:, update_list].sum(axis=1)
            net_event["__total__"] = net_event.loc[:, update_list].sum(axis=1)

        prior_ri_idx = ri_idx

        ri_amount = gross_event.loc[event_idx, include_list].sum(axis=0)
        # Teh share of the event that goes to eahc strcuture
        ri_split = gross_event.loc[event_idx, :] / ri_amount
        # Make sure that the cells not inlcuded have a 0 value.
        ri_split.loc[np.logical_not(include_list)] = 0.0

        # Calcualte the actual recovery
        actual_recov, theo_recov = f_apply_reinsurance(ri_amount, ri_idv)

        # Now we only reduce the net event, in th rare evetn that the
        # net event is already 0 we do nothing.
        # Can't imagine a scenario like this but need to try make
        # the code bullet proof.

        if net_event.at[event_idx, "__total__"] > 0.0:
            net_event.loc[event_idx, :] = (
                net_event.loc[event_idx, :] - ri_split * theo_recov
            )

        if len(cols) == 1:
            net_event.at[event_idx, "__total__"] = net_event.at[event_idx, cols[0]]
        else:
            net_event.at[event_idx, "__total__"] = (
                net_event.loc[[event_idx], cols].sum(axis=1).iloc[0]
            )

        # Calculate the recoveries across the different structures
        # We add the recoveries to the existing recoveries
        struc_share.loc[ri_idx, ri_split.index] = struc_share.loc[
            ri_idx, ri_split.index
        ].astype(float) + float(actual_recov) * ri_split[ri_split.index].astype(float)
        struc_share.at[ri_idx, "__total__"] = struc_share.loc[ri_idx, cols].sum(axis=0)

        contract.at[ri_idx, "prior_recov"] = (
            contract.at[ri_idx, "prior_recov"] + actual_recov
        )
        contract.at[ri_idx, "actual_recov"] = (
            contract.at[ri_idx, "actual_recov"] + actual_recov
        )
        contract.at[ri_idx, "theo_recov"] = (
            contract.at[ri_idx, "theo_recov"] + theo_recov
        )

    return (net_event, contract, struc_share)


def f_apply_reinsurance(event, ri_idv):
    """Calculate the recoveries for a single monetary amount."""
    #logger.debug("Function start")

    if ri_idv["contract_type"] == "xol":
        del ri_idv["contract_type"]
        actual_recov, theo_recov = __f_xol(event, ri_idv)

    elif ri_idv["contract_type"] == "prop":
        del ri_idv["contract_type"]
        actual_recov, theo_recov = __f_prop(event, ri_idv)
    else:
        # Pyhton didn't run into an error here we created an error.
        raise Exception(
            "reinsurance", "apply_recoveries", "Invalid reinsurance contract", ""
        )

    return (actual_recov, theo_recov)


def __f_xol(event: float, contract: dict[str, float]) -> tuple[float, float]:
    """Calculate the recoveries for an xol contract."""
    #logger.debug("Function start")

    # Need to make sure that we explciitley define some of the data
    # handling (and assumptions) that we will be making
    # None will always evaluate to False
    rein_count = contract["reinstate_count"] or 0
    rein_rate = contract["reinstate_rate"] or 0

    # Work out the toal amount that can be recovered from the layer
    # The or statement is here to remove where a user has not entered
    # the number of reinstatements.
    # We assume the number of reinstatements to be 0 in these instances
    # None will always evaluate to False
    max_recov = contract["layer_size"] * (rein_count + 1)
    remain_recov = max_recov - contract["prior_recov"]
    theo_recov = min(
        remain_recov,
        min(contract["layer_size"], max(event - contract["excess"], 0)),
    )
    # Allow for the reinstatement premium
    # Need to still allow for when reinstatements are exhausted
    rein_prem = (
        max(
            contract["layer_size"] * rein_count - contract["prior_recov"],
            theo_recov,
            0,
        )
        * rein_rate
    )

    theo_recov = theo_recov * contract["ri_share"]

    actual_recov = (theo_recov - rein_prem) * contract["total_counterparty_share"]

    return (actual_recov, theo_recov)


def __f_prop(event: float, contract: dict[str, float]) -> tuple[float, float]:
    """Calculates the recoveries from proportional reinsurance."""
    #logger.debug("Function start")

    theo_recov = event * float(contract["ri_share"])
    #logger.debug("Theo_recovery")
    if pd.isna(contract["layer_size"]):
        layer_size = math.inf
    else:
        layer_size = float(contract["layer_size"])
    actual_recov = min(theo_recov, layer_size) * float(
        contract["total_counterparty_share"]
    )
    #logger.debug("actual_recovery")
    return (actual_recov, theo_recov)
