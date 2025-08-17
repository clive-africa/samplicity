from typing import Union
import pandas as pd
from .ri_man_made import f_man_made
from .ri_prog import f_apply_ri_prog
from ..helper import log_decorator


class Reinsurance:
    """Class to calcualte reinsurance recoveries."""

    @log_decorator
    def __init__(self, sam_scr, class_name="reinsurance", calculate=False):
        self.output = {}
        """ A dictionary that will store all of the results of the class."""

        self.scr = sam_scr
        """ A reference to the main SCR object. """

        self.scr.classes[class_name] = self

        if calculate:
            self.f_calculate_net_events()

    @log_decorator
    def f_calculate_net_events(self: "Reinsurance") -> bool:
        """Calculate net events for all different events with applicable reinsurance."""

        # ##########

        # HAIL CHARGE

        # ##########

        net_event = {}
        recoveries = {}
        detail_recoveries = {}
        counterparty_recoveries = {}

        # ##########

        # NAT CAT CHARGES
        # FACTOR CHARGES
        # NON-PROP CHARGES

        # ##########

        # We sue the same code given the similarity in the approach
        # We add a prefix differentiate between the perils and
        # avoid issues where the perils repeat names.
        # We also need to make allowance for the horizontal event,
        # the base provide four rows that get duplicated
        # This would create a 3D array which is not really possible to manage
        # We just combined the figures for the horizontal event
        f_charge_names = self.scr.f_data("data", "metadata", "factor_cat_charge").index
        event_list = (
            ["nc_hail", "nc_earthquake", "nc_horizontal"]
            + list(f_charge_names.to_series())
            + ["np_property", "np_credit_guarantee"]
        )

        # Provide an easy mapping of the different events to factories
        event_map = {"fc_": "factor_cat", "np_": "non_prop_cat", "nc_": "nat_cat"}

        for event in event_list:
            # We need to get the category to know which module to call
            cat = event_map[event[:3]]

            # This returns a datafrmae where the columns are the different RI arrangements
            # The column __none__  is where there is no reinsurance
            # This will be the total event for all 'divisions'
            event_set = self.scr.f_data(cat, "reinsurance", event)

            # Need to allow for scenarios when we don't have any events
            if event_set is None:
                total_event = 0
            else:
                # Given we prepare everyting as a frozenset, to cater for all the combinations
                # We need to convert the columns to just text strings
                # This is so that we can use the columns in the reinsurance programme
                event_set.columns = [
                    list(x)[0] if isinstance(x, frozenset) else x
                    for x in event_set.columns
                ]
                # Sum across the columns to get the toal event across all reinsurance structures
                total_event = sum(event_set.sum(axis=1))

            # Deal with the case where there is no event
            # We store None here
            # Could possible place this above, but maybe there is a zero event?

            if total_event == 0:
                # We know the event is zero
                net_event[event] = 0.0
                recoveries[event] = None
                detail_recoveries[event] = None
                counterparty_recoveries[event] = None
                continue

            # We can proceed with the calculation
            # These are results by division and structure
            # They have alreayd been pro-rataed across the divisions and structures
            if event == "nc_horizontal":
                div_struct = self.scr.f_data(
                    "nat_cat", "div_structure", "horizontal_combined"
                )
            else:
                div_struct = self.scr.f_data(cat, "div_structure", event)

            # We need to make allowance for the horizontal event here
            # All other events will have a single event but the horizontal
            # event will have 4 events

            # Need to get the proportion of these of the total event
            # row_sums = div_struct.sum(axis=1)
            # row_sums = row_sums / total_event

            # At this stage we know how much eahc combination of divisions contributes to the total event
            # An assumption of this tool is that when we look at the different divisions we pr-rate the recoveries
            # IT is not reasonable to assume thaat the sum reinsurance strucre would remain in palce

            # TO DO: Worry that I am double dividing here

            # div_struct = div_struct.multiply(row_sums, axis=0)
            event_columns = div_struct.columns

            div_struct = div_struct.loc[:, event_columns].div(
                event_set.iloc[0][event_columns]
            )
            div_struct.index.name = "division"
            div_struct.reset_index(inplace=True)
            div_struct = pd.melt(
                frame=div_struct,
                id_vars="division",
                var_name="structure",
                value_name="perc",
            )

            # We need to remove the event with no reinsurance
            # This will be named "__none__"
            if event_set is not None and len(event_set) > 0:
                event_set.drop(columns=["__none__"], inplace=True, errors="ignore")
                (
                    net_event[event],
                    recoveries[event],
                    df,
                ) = self.f_calculate_recoveries(event_name=event, event_set=event_set)

                # df=detail_recoveries[event]
                df = df.merge(
                    div_struct,
                    how="inner",
                    left_on="structure",
                    right_on="structure",
                )
                df["recovery"] = df["recovery"] * df["perc"]
                df = df[~(df["recovery"] == 0)]
                df = df[["division", "counterparty_id", "structure", "recovery"]]
                detail_recoveries[event] = df
                df = df[["division", "counterparty_id", "recovery"]]
                df = df.groupby(["division", "counterparty_id"], as_index=False).sum()
                df.index = df["division"]
                df.index.names = ["index"]
                df.drop(columns=["division"], inplace=True)
                counterparty_recoveries[event] = df

        # ##########

        # MAN-MADE CHARGE

        # ##########

        # The man-made catstrophe events rae treated slightly differently
        # The clacualtion is, in most cases, more conservative than if we did
        # a proper calculation
        # It does mean that how we calcaulte reinsurance is somewhat different
        # W eneed to return values for each combination of division

        # We call a seperate function given the length
        # These will return dictionaries
        net, recovery, counterparty, detail = f_man_made(self)

        # Merge all of the dictionaries together
        net_event = dict(**net_event, **net)
        recoveries = dict(**recoveries, **recovery)
        detail_recoveries = dict(**detail_recoveries, **detail)
        counterparty_recoveries = dict(**counterparty_recoveries, **counterparty)

        self.output["net_event"] = net_event
        self.output["recoveries"] = recoveries
        self.output["detail_recoveries"] = detail_recoveries
        self.output["counterparty_recoveries"] = counterparty_recoveries

        # counterparty_recoveries['man_made']=df

        return True

    def f_calculate_recoveries(self, event_name, event_set):
        """Calculate the recoveries for an event."""

        # DATA MANIPULATIONS

        # Some of the oclumn headings are stored as tuples
        # We need to convert these to just text strings

        event_set.columns = [
            x[0] if isinstance(x, frozenset) else x for x in event_set.columns
        ]

        rein_prog = self.scr.f_data("data", "data", "reinsurance_prog")

        # This will determine the recoveries by counterparty
        contract_share = self.scr.f_data("data", "data", "ri_contract_share")

        # If this error occurs there are events which don't exist in our
        # reinsurance programme.

        # Need to allow for the "__none__" event which is where there is no reinsurance
        # We need to remove this event from the event set
        if len(event_set.columns.difference(rein_prog.columns)) > 0:
            raise Exception(
                "reinsurance",
                "f_calculate_recoveries",
                f"Invalid reinsurance structure provided: {event_name}",
            )

        # We create a copy of the reinsurance contract, we will only be
        # filtering out the rows and columns we need
        rein_prog = rein_prog[event_set.columns]
        # We remove the rows where all the rows are NA
        # This si where the reinsurance structure is note sued
        # Done to spped up the calculation
        rein_prog = rein_prog[rein_prog.any(axis=1)]

        # Preform the necessary data manipulation for
        # the reinsurance contracts
        contract = self.__f_prepare_contract()

        # We need to get our recoveries per structure and counterparty
        # We create a seperate dataframe to store this information
        struc_share = None

        # Loop through the event sin the event set
        for i in range(len(event_set)):
            # event_idx = event_set.index[i]
            # print(event_idx)
            gross_event = event_set.iloc[[i], :].copy(deep=True)

            # Apply the reinsurance programme
            net_event, contract, struc_share = f_apply_ri_prog(
                rein_prog, contract, gross_event, struc_share
            )

        # At this stage we have calcualted recoveries for all the events
        # We now need to allocated them to the counterparties
        # I think all of these entries can be removed, we probably only need to
        # keep the recoveries by cparty_struct_rec
        cparty_recov, cparty_struct_rec = self.__f_alloc_cparty(
            contract, struc_share, contract_share, event_set.columns
        )

        return (net_event, cparty_recov, cparty_struct_rec)

    def __f_prepare_contract(self) -> pd.DataFrame:
        """Data manipulation for the reinsurance contracts."""
        # Add additional columns for the calcualtion
        # All the recoveries will start at 0
        contract = self.scr.f_data("data", "data", "ri_contract")
        contract[["prior_recov", "actual_recov", "theo_recov"]] = 0.0
        # contract["actual_recov"] = 0
        # contract["theo_recov"] = 0

        # We get the share of eahc counterparty in the reinsurance contract
        # This deals with cases where a contratc hs not bee fully palced
        ri_total_contract_share = self.scr.f_data("data", "data", "ri_contract_share")
        ri_total_contract_share = ri_total_contract_share[
            ["reinsurance_id", "counterparty_share"]
        ]
        ri_total_contract_share = ri_total_contract_share.groupby(
            by="reinsurance_id", as_index=True
        ).sum()
        # At this stage we have eahc contract with the proportion ceded
        # to all counterparties
        ri_total_contract_share.rename(
            columns={"counterparty_share": "total_counterparty_share"}, inplace=True
        )
        # Add the counterparty share to the contract variables
        contract = contract.merge(
            ri_total_contract_share, left_index=True, right_index=True, how="left"
        )

        # In case there is not counterparty share, we set the share to be zero
        contract.fillna({"total_counterparty_share": 0}, inplace=True)

        # We convert our dataframe into a dictionary of contracts
        # Within eahc dictionary is a dictioanry of arguments
        return contract

    def __f_alloc_cparty(self, contract, struc_share, contract_share, event_cols):
        """Allocated recoveries to counterparties."""
        # We now determien the reinsurance recoveries by counterparty
        cparty_recov = contract.merge(
            contract_share, left_index=True, right_on="reinsurance_id"
        )
        cparty_recov["cparty_recov"] = (
            cparty_recov["actual_recov"]
            * cparty_recov["counterparty_share"]
            / cparty_recov["total_counterparty_share"]
        )
        cparty_recov = (
            cparty_recov[["counterparty_id", "cparty_recov"]]
            .groupby(by=["counterparty_id"], as_index=True)
            .sum()
        )

        # We have recoveries by counterparty
        cparty_struct_rec = struc_share.merge(
            contract_share, left_index=True, right_on="reinsurance_id"
        )

        cparty_struct_rec[event_cols] = (
            cparty_struct_rec[event_cols]
            .multiply(cparty_struct_rec["counterparty_share"], axis="index")
            .divide(cparty_struct_rec["total_counterparty_share"], axis="index")
        )
        # Remove all the excess columns
        cparty_struct_rec = cparty_struct_rec[list(event_cols) + ["counterparty_id"]]

        # Metl the dataframe to just give us counterparty information
        cparty_struct_rec = cparty_struct_rec.melt(
            id_vars=["counterparty_id"], var_name="structure", value_name="recovery"
        )

        return (cparty_recov, cparty_struct_rec)

    def f_data(self, data: str, sub_data: str) -> Union[pd.DataFrame, None]:
        """Return the output values stored in Reinsurance class."""
        err = f"Error: Cannot find {data} - {sub_data}"
        data = data.lower().strip()
        sub_data = sub_data.lower().strip()

        try:
            if data in (
                "net_event",
                "recoveries",
                "detail_recoveries",
                "counterparty_recoveries",
            ):
                df = self.output[data][sub_data]
            else:
                raise ValueError(err)
        except KeyError:
            raise ValueError(err)
        else:
            return df.copy() if df is not None else None
