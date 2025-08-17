import pandas as pd
import pandera as pa
from pandera import Column, DataFrameSchema


class AssetData:
    """Asset data validator with context"""

    def __init__(self, sam_data):
        # Teh different counterparties
        self.counterparties = sam_data.output["data"]["counterparty"]["id"].unique().tolist()
        self.asset_types = sam_data.output["data"]["asset_data"]["asset_type"].unique().tolist()
        # The divisiosn that we allow for
        self.levels = {}
        for lev in [1, 2, 3]:
            self.levels[lev] = (
                sam_data.output["data"]["division_detail"][f"level_{lev}"]
                .unique()
                .tolist()
            )
            # We will degault all missing, null values to '__none__'
            self.levels[lev].append("__none__")       
        
        self.schema = self._create_schema()



    def _create_schema(self):
        """Create the validation schema with access to self.sam_scr"""
        return DataFrameSchema(
            {
                "id": Column(
                    str,
                    nullable=False,
                    unique=True,
                    description="Unique asset identifier",
                ),
                "asset_description": Column(
                    str, nullable=True, description="Asset description"
                ),
                "level_1": Column(
                    str,
                    parsers=[pa.Parser(lambda s: s.fillna("__none__"))],
                    checks=pa.Check.isin(
                        self.levels[1], error="Invalid division level 1 included."
                    ),
                    nullable=True,
                    description="Level 1 Division",
                ),
                "level_2": Column(
                    str,
                    parsers=[pa.Parser(lambda s: s.fillna("__none__"))],
                    checks=pa.Check.isin(
                        self.levels[2], error="Invalid division level 2 included."
                    ),
                    nullable=True,
                    description="Level 1 Division",
                ),
                "level_3": Column(
                    str,
                    parsers=[pa.Parser(lambda s: s.fillna("__none__"))],
                    checks=pa.Check.isin(
                        self.levels[3], error="Invalid division level 3 included."
                    ),
                    nullable=True,
                    description="Level 1 Division",
                ),
                "asset_type": Column(
                    str, 
                    checks=pa.Check.isin(self.asset_types, error="Asset type has not been properly mapped."), 
                    nullable=True, 
                    description="Type of asset"
                ),
                "counterparty_id": Column(
                    str,
                    checks=pa.Check.isin(self.counterparties, error="Invalid counterparty ID format")
                    nullable=True,
                    description="Reference to counterparty table",
                ),
                "asset_cqs": Column(
                    int, nullable=True, description="Asset Credit Quality Step"
                ),
                "lgd_adj": Column(
                    float, nullable=True, description="Loss Given Default adjustment"
                ),
                "mod_duration": Column(
                    float, nullable=True, description="Modified duration"
                ),
                "market_value": Column(
                    float, nullable=True, description="Market value of the asset"
                ),
                "nominal_value": Column(
                    float, nullable=True, description="Nominal value of the asset"
                ),
                "collateral": Column(
                    str, nullable=True, description="Collateral information"
                ),
                "bond_type_old": Column(
                    str, nullable=True, description="Legacy bond type classification"
                ),
                "maturity_date": Column(
                    str,  # Will be converted to datetime in preprocessing
                    nullable=True,
                    description="Asset maturity date",
                ),
                "coupon": Column(
                    str,  # Handle percentage strings like "7.8%"
                    nullable=True,
                    description="Coupon rate",
                ),
                "spread": Column(
                    str,  # Handle percentage strings like "0.00%"
                    nullable=True,
                    description="Spread over benchmark",
                ),
                "coupon_freq": Column(
                    int,
                    checks=[
                        pa.Check.isin(
                            [1, 2, 4, 12]
                        )  # Annual, Semi-annual, Quarterly, Monthly
                    ],
                    nullable=True,
                    description="Coupon frequency per year",
                ),
                "bond_type": Column(
                    str,
                    checks=[
                        pa.Check.isin(
                            ["fixed", "floating", "inflation_linked", "zero_coupon"]
                        )
                    ],
                    nullable=True,
                    description="Bond type",
                ),
                "equity_volatility_shock": Column(
                    float, nullable=True, description="Equity volatility shock factor"
                ),
                "spread_credit_up_shock": Column(
                    float, nullable=True, description="Spread credit up shock"
                ),
                "spread_credit_down_shock": Column(
                    float, nullable=True, description="Spread credit down shock"
                ),
            },
            strict=False,
            name="asset_data_schema",
            description="Schema for asset data with market and risk information",
        )

    def validate(self, df, **kwargs):
        """Validate the DataFrame"""
        return self.schema.validate(df, **kwargs)


# Usage:
#validator = AssetData(sam_scr)
#test = validator.validate(
#    sam_scr.classes["data"].output["data"]["asset_data"], lazy=True
#)
