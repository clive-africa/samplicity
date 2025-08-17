import pandas as pd
import pandera.pandas as pa
from pandera import Column, DataFrameSchema


class AssetShocks:
    """Asset data validator with context"""

    def __init__(self, sam_data):
        # We don't have nay special settigns for asset shocks
        self.asset_shocks=["equity_global",
                "equity_sa",
                "equity_infrastructure",
                "equity_other",
                "equity_volatility",
                "property",
                "currency",
                "spread_credit,"
                "concentration",
                "concentration_bank",
                "concentration_government",
                "default_type_1",
                "default_type_2",
                "default_type_2_overdue",
                "default_type_3",
                "spread_interest", 
                "spread_interest_infrastructure",
                "interest_rate"]
        self.schema = self._create_schema()

    def _create_schema(self):
        """Create the validation schema with access to sam_data"""
        return DataFrameSchema(
            {
                "asset_type": Column(
                    str,
                    nullable=False,
                    unique=False,

                    description="Asset type.",
                ),
                "shock": Column(
                    str, 
                    checks=pa.Check.isin(self.asset_shocks, error="Invalid asset shock captured."),
                    nullable=False,
                    description="Asset shock."
                ),
            },
            checks=
                pa.Check(lambda df: ~df[["asset_type", "shock"]].duplicated().any(), 
             error="The same shocks cannot be repeated for the same asset type.",
             raise_warning=False),
            strict=False,
            name="asset_shocks_schema",
            description="Schema for the shocks to be applied to the different asset types.",
        )

    def validate(self, df, **kwargs):
        """Validate the DataFrame"""
        return self.schema.validate(df, **kwargs)


# Usage:
validator = AssetShocks(sam_data)
test = validator.validate(
    sam_data.output["data"]["asset_shocks"], lazy=True
)
