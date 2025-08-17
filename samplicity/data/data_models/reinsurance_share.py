import pandas as pd
import pandera as pa
from pandera import Column, DataFrameSchema


class ReinsuranceShare:
    """Validation of the reinsurance share data model with context"""

    def __init__(self, sam_scr):
        self.counterparties = sam_scr.classes["data"].output["data"]["counterparty"]["id"].unique()
        self.ri_contracts = sam_scr.classes["data"].output["data"]["ri_contract"].index.unique().to_list()
        self.schema = self._create_schema()

    def _create_schema(self):
        """Create the validation schema with access to self.sam_scr"""
        return DataFrameSchema(
            {
            "reinsurance_id": Column(
            str,
            checks=pa.Check.isin(self.ri_contracts, error="Invalid reinsurance contract ID included."),
            nullable=False,
            unique=False,
            description="Reinsurance contract identifier",
            ),
            "counterparty_id": Column(
            str, 
            checks=pa.Check.isin(self.counterparties, error="Invalid counterparty ID included."),
            nullable=False, 
            description="Counterparty identifier"
            ),
            "counterparty_share": Column(
            float,
            checks=[
            pa.Check.ge(0, error="Counterparty share must be greater than or equal to 0."),
            pa.Check.le(1, error="Counterparty share must be less than or equal to 1.")
            #pa.Check(lambda s: s.sum() <= 1, element_wise=False)
            ],
            nullable=False,
            unique=False,
            description="Share of reinsurance contract held by the counterparty",
            ),
            },
            strict=False,
            name="reinsurance_share_schema",
            description="Schema for checkign reinsurance contract share data",
            coerce=True,
        )

    def validate(self, df, **kwargs):
        """Validate the DataFrame"""
        return self.schema.validate(df, **kwargs)


# Usage:
#validator = ReinsuranceShareValidator(sam_scr)
#test = validator.validate(
#    sam_scr.classes["data"].output["data"]["ri_contract_share"], lazy=True
#)
