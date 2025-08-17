
import pandas as pd
import pandera as pa
from pandera import Column, DataFrameSchema, Index

import pandas as pd
import pandera as pa
from pandera import Column, DataFrameSchema

class ReinsuranceProg:
    """Reinsurance program validator with context"""
    
    def __init__(self, sam_scr):
        self.ri_contracts = sam_scr.classes['data'].output['data']['ri_contract'].index.unique().tolist()
        self.schema = self._create_schema()
    
    def _create_schema(self):
        """Create the validation schema with access to self.sam_scr"""
        return DataFrameSchema({
            "reinid": Column(
                str,
                nullable=False,
                unique=True,
                description="Unique asset identifier"
            ),
            "asset_description": Column(
                str,
                nullable=True,
                description="Asset description"
            ),
            "level_1": Column(
                str,
                checks=[
                    Check.isin(['div_a', 'div_b', 'div_c', 'other'])
                ],
                nullable=True,
                description="Level 1 Division"
            ),
            "level_2": Column(
                str,
                nullable=True,
                description="Level 2 Division"
            ),
            "level_3": Column(
                str,
                nullable=True,
                description="Level 3 Division"
            ),
            "asset_type": Column(
                str,
                nullable=True,
                description="Type of asset"
            ),
            "counterparty_id": Column(
                str,
                checks=[
                    pa.Check.isin(self.ri_contracts, error="Invalid contract ID included.")
                ],
                nullable=True,
                description="Reference to counterparty table"
            ),
            "asset_cqs": Column(
                int,
                nullable=True,
                description="Asset Credit Quality Step"
            ),
            "lgd_adj": Column(
                float,
                nullable=True,
                description="Loss Given Default adjustment"
            ),
            "mod_duration": Column(
                float,
                nullable=True,
                description="Modified duration"
            ),
            "market_value": Column(
                float,
                nullable=True,
                description="Market value of the asset"
            ),
            "nominal_value": Column(
                float,
                nullable=True,
                description="Nominal value of the asset"
            ),
            "collateral": Column(
                str,
                nullable=True,
                description="Collateral information"
            ),
            "bond_type_old": Column(
                str,
                nullable=True,
                description="Legacy bond type classification"
            ),
            "maturity_date": Column(
                str,  # Will be converted to datetime in preprocessing
                nullable=True,
                description="Asset maturity date"
            ),
            "coupon": Column(
                str,  # Handle percentage strings like "7.8%"
                nullable=True,
                description="Coupon rate"
            ),
            "spread": Column(
                str,  # Handle percentage strings like "0.00%"
                nullable=True,
                description="Spread over benchmark"
            ),
            "coupon_freq": Column(
                int,
                checks=[
                    pa.Check.isin([1, 2, 4, 12])  # Annual, Semi-annual, Quarterly, Monthly
                ],
                nullable=True,
                description="Coupon frequency per year"
            ),
            "bond_type": Column(
                str,
                checks=[
                    pa.Check.isin(['fixed', 'floating', 'inflation_linked', 'zero_coupon'])
                ],
                nullable=True,
                description="Bond type"
            ),
            "equity_volatility_shock": Column(
                float,
                nullable=True,
                description="Equity volatility shock factor"
            ),
            "spread_credit_up_shock": Column(
                float,
                nullable=True,
                description="Spread credit up shock"
            ),
            "spread_credit_down_shock": Column(
                float,
                nullable=True,
                description="Spread credit down shock"
            )
        },
        strict=False,
        name="asset_data_schema",
        description="Schema for asset data with market and risk information"
        )
    
    def validate(self, df, **kwargs):
        """Validate the DataFrame"""
        return self.schema.validate(df, **kwargs)

# Usage:
#validator = AssetDataValidator(sam_scr)
#test = validator.validate(sam_scr.classes['data'].output['data']['asset_data'], lazy=True)