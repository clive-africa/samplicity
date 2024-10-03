from .ri_prog import f_apply_ri_prog
import numpy as np
import pandas as pd
import math


import logging

logger = logging.getLogger(__name__)


def f_man_made(rein):
    """Calculate the man-made reinsurance recoveries."""
    #logger.debug("Function start")

    # GET DATA

    # Get the data needed by the function

    # The list of complete man-made events
    man_made_perils = [
        "mm_motor",
        "mm_fire_property",
        "mm_marine",
        "mm_aviation",
        "mm_liability",
        "mm_credit_guarantee",
        "mm_terrorism",
        "mm_accident_health",
    ]

    # The list of division combinations
    div_list = rein.scr.f_data("scr", "list_combinations").iloc[:, 0].values.tolist()

    # Teh field used for the diversification calculation
    div_field = rein.scr.f_data("data", "data", "diversification_level").iloc[0]

    # The overall gross event for the entire entity
    mm_overall = rein.scr.f_data("data", "data", "man_made_overall")
    # Get the perils in the order the apply.
    # man_made_perils = mm_overall.index.tolist()

    # The invidual man-made events per division
    mm_events = rein.scr.f_data("data", "data", "man_made_division_event")
    # Drop all additional divisional fields,
    # Mainly to ensure teh order comes trhough correctly
    mm_events = mm_events[[div_field] + man_made_perils]

    # The applicable reinsurance structures
    # These are the names of the structures that msut be applied to event event
    reinsurance = rein.scr.f_data("data", "data", "man_made_division_reinsurance")
    reinsurance = reinsurance[[div_field] + man_made_perils]

    # DATA CHECKS

    max_element = [len(x) for x in div_list]

    if max_element[len(max_element) - 1] != max(max_element):
        raise Exception(
            "reinsurance",
            "f_calculate_net_events",
            "Diversification listing is incorrect",
            "",
        )

    # THE OVERALL EVENT
    # We identify this as the one with all the divisions
    overall_index = div_list[len(div_list) - 1]

    # We remove all entries where there is no reinsurance
    filtered_mm_overall = mm_overall[
        mm_overall["ri_structure"].fillna("none") != "none"
    ]

    # We use this later to populate the dictionaires with the skipped events
    skip_mm_overall = [
        mm for mm in man_made_perils if mm not in filtered_mm_overall.index.values
    ]

    # Create a balank dataframe that will append our different events to
    # Thsi si doen in the loop below
    mm_overall_net_event = pd.DataFrame()
    mm_overall_recoveries = pd.DataFrame()
    # We loop through each row here
    # Could use apply functtion but the speed improvement will be minimla
    # Complicates teh calcualtion a lot
    # We don't immediately copy the results to the dictioanry as some
    # more manipulation is required
    # We are calcualting the recoveries for each event
    # at an overall basis.
    for row in filtered_mm_overall.itertuples():
        event_set = pd.DataFrame(
            row.gross_event, columns=[row.ri_structure], index=[row.Index]
        )
        net, rec, rec_struct = rein.f_calculate_recoveries(row.Index, event_set)
        rec["event"] = [row.Index] * len(rec)
        rec["structure"] = [row.ri_structure] * len(rec)
        # Deals with the first case where the dataframe will be blank
        if len(mm_overall_net_event) > 0:
            mm_overall_net_event = pd.concat([mm_overall_net_event, net])
            mm_overall_recoveries = pd.concat([mm_overall_recoveries, rec])
        else:
            mm_overall_net_event = net.copy(deep=True)
            mm_overall_recoveries = rec.copy(deep=True)

    # IT is jsut the recoveries that we need to add with 0 recoveries
    # for mm in skip_mm_overall:
    #    rec[event]

    # Populate the gross events and populate zeros where needed
    mm_overall["net_event"] = mm_overall["gross_event"].fillna(0)
    # Overwrite where we have net events - these will have reinsurance
    mm_overall.loc[mm_overall_net_event.index, "net_event"] = mm_overall_net_event[
        "__total__"
    ]
    # Need to poplate the event with ehte index
    mm_overall["event"] = mm_overall.index

    # Add the divsion for the 'total' event
    mm_overall["div"] = [overall_index] * len(mm_overall)

    mm_overall_recoveries.reset_index(inplace=True)
    mm_overall_recoveries["div"] = [overall_index] * len(mm_overall_recoveries)

    # INDIVIDUAL DIVISION EVENTS

    # IT is too complicated to potentially consider the impact of all the different
    # combinations of events that could occur. We sue a simple sum approach.

    # We normalise our data
    mm_events = mm_events.melt(
        id_vars=div_field, var_name="event", value_name="gross_event"
    )
    reinsurance = reinsurance.melt(
        id_vars=div_field, var_name="event", value_name="ri_structure"
    )
    # Create a single dataset with all the gross events and the reinsurance
    # We need to do all the calculations to allow for cases where a
    # higher gross event migth be netted down
    mm_events = mm_events.merge(
        reinsurance,
        how="left",
        left_on=[div_field, "event"],
        right_on=[div_field, "event"],
    )
    # Remove the null events
    mm_events = mm_events[-mm_events["gross_event"].isnull()]
    # Remove events with no reinsurace
    filtered_mm_events = mm_events[mm_events["ri_structure"].fillna("none") != "none"]

    mm_net_event = pd.DataFrame()
    mm_recoveries = pd.DataFrame()
    for row in filtered_mm_events.itertuples():
        event_set = pd.DataFrame(
            row.gross_event, columns=[row.ri_structure], index=[row.Index]
        )
        net, rec, rec_struct = rein.f_calculate_recoveries(row.Index, event_set)
        rec["event"] = [row.event] * len(rec)
        rec["div_field"] = [getattr(row, div_field)] * len(rec)
        # Added for the detailed recoveried
        rec["structure"] = [getattr(row, 'ri_structure')] * len(rec)
        if len(mm_net_event) > 0:
            mm_net_event = pd.concat([mm_net_event, net])
            mm_recoveries = pd.concat([mm_recoveries, rec])
        else:
            mm_net_event = net.copy(deep=True)
            mm_recoveries = rec.copy(deep=True)

    # Teh counterparty is sitting in the index
    mm_recoveries.reset_index(inplace=True)

    # Copy the gross event across
    mm_events.loc[:,"net_event"] = mm_events["gross_event"].astype(float).fillna(0)
    # Only replace the gross event where we have a cauculated net event
    mm_events.loc[mm_net_event.index, "net_event"] = mm_net_event["__total__"]

    # AT this stage we have the the events per division
    # We now need to calcualte for all the different combinations
    # We get a list of all the divisions that make up the different combinations
    mm_agg = pd.DataFrame(div_list[:-1], index=div_list[:-1])
    mm_agg = mm_agg.stack().to_frame(name="div_field").reset_index(drop=True, level=1)
    mm_agg["div"] = mm_agg.index

    # We are creating a normalised view to allow us to join to the data
    # stored in the diversification table.

    # Join all the divison net events with the different
    # division combinations
    mm_agg_event = mm_agg.merge(
        mm_events[["net_event", div_field, "event"]],
        left_on="div_field",
        right_on=div_field,
        how="inner",
    )

    # Do the same with the reinsurance rercoveries
    mm_agg_recoveries = mm_agg.merge(
        mm_recoveries[["cparty_recov", "counterparty_id", "event", "div_field", "structure"]],
        left_on="div_field",
        right_on="div_field",
        how="inner",
    )

    # At this stage we will have divisions with no events
    # Changed this with an inner join

    # W eno longer have a use for the division field
    mm_agg_event = mm_agg_event.drop(["div_field", div_field], axis=1)
    mm_agg_recoveries = mm_agg_recoveries.drop(["div_field"], axis=1)


    # We do the same with our recoveries
    detail_recoveries = pd.concat(
        [
            mm_agg_recoveries[["div", "cparty_recov", "counterparty_id", "structure", "event"]],
            mm_overall_recoveries[["div", "cparty_recov", "counterparty_id", "structure","event"]],
        ]
    )

    detail = {}
    counterparty = {}
    for event in detail_recoveries["event"].unique():
        # Get the entires we need
        # Added the fiedls here 'div' and 'structure'
        # This could be wrong
        tmp = detail_recoveries.loc[
            detail_recoveries["event"] == event, ["div","counterparty_id", "structure","cparty_recov"]
        ]
        tmp.columns=["division","counterparty_id","structure","recovery"]
        # MAke counterparty_di the index
        #tmp.index = tmp["counterparty_id"]
        #tmp.drop(columns=["counterparty_id"], inplace=True)

        # Now get the counterparty summary
        df = detail_recoveries.loc[detail_recoveries["event"] == event, :]
        df = df[["div", "counterparty_id", "cparty_recov"]]
        df = df.groupby(["div", "counterparty_id"], as_index=False).sum()
        df.index = df["div"]
        df.index.names = ["index"]
        df.drop(columns=["div"], inplace=True)
        df.rename(columns={"cparty_recov": "recovery"}, inplace=True)

        # Add to the dictionary
        # The recoveries by reinsurer for each event
        # This is repeated for each division combinatons
        detail[event] = tmp
        # Teh same as above but with the division ID for each
        counterparty[event] = df
        # print(detail.keys())

    # The vlaues we pass to net_evetn should be the recoveries for the
    # Total with the reinsurance columns at the top
    # Teh should also be a total column

    # Teh values we pass for recoveries should be the recoveries by
    # reinsurance counterparty and event
    recoveries = {}
    event_list = mm_overall_recoveries["event"].unique()
    for event in event_list:
        # Get the entires we need
        tmp = mm_overall_recoveries.loc[
            mm_overall_recoveries["event"] == event,
            ["counterparty_id", "cparty_recov"],
        ]
        # MAke counterparty_di the index
        tmp.index = tmp["counterparty_id"]
        tmp.drop(columns=["counterparty_id"], inplace=True)
        # Add to the dictionary
        recoveries[event] = tmp

    #

    # Now we need just to oder the overall net event
    net_event = {}
    for idx in mm_overall_net_event.index:
        row = mm_overall_net_event.loc[[idx]]
        row.dropna(axis="columns", inplace=True)
        cols = row.columns.to_series()
        cols = cols[cols != "__total__"].sort_values().tolist()

        net_event[idx] = row[[*cols, "__total__"]]

    # Need to add the missing perils to our data
    # We add them as None and 0.
    # Thsi ensures that we don't have any error.
    for mm in skip_mm_overall:
        net_event[mm] = np.nan_to_num(mm_overall.at[mm, "gross_event"])
        recoveries[mm] = None
        counterparty[mm] = None
        detail[mm] = None

    #TODO: The foramt of the data of detail si differenet whn comapred to nat cat
    # Nat cat has: division	counterparty_id	structure	recovery
    # MM has: counterparty_id, recovery

    return (net_event, recoveries, counterparty, detail)
