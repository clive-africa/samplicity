import pandas as pd
import pandera.pandas as pa
from pandera import Column, DataFrameSchema

base_input_schema = DataFrameSchema(
    columns={
        "valuation_date": Column(
            pd.DatetimeTZDtype(tz="UTC"),
            nullable=False,
            description="Valuation date."
        ),
        "company_name": Column(
            str,
            nullable=True,
            description="Company name"
        ),
        "level_3": Column(
            str,
            nullable=True,
            description="Level 3 identifier"
        ),
        "diversification_level": Column(
            str,
            checks=pa.Check.isin(['level_1', 'level_2', 'level_3'],
                                 error="Invalid diversification level. Must be one of 'level_1', 'level_2', or 'level_3'."),
            nullable=False,
            description="Diversification field"
        ),
        "calculation_level": Column(
            str,
            checks=pa.Check.isin(['overall', 'individual', 'diversification'],
                                 error="Invalid calculation level. Must be one of 'overall', 'individual', 'diversification'."),
            nullable=False,
            description="Calculation detail level"
        ),        
        "tax_percent": Column(
            float,
            nullable=False,
            description="Company level tax percentage."
        ),
        "max_lacdt": Column(
            float,
            nullable=False,
            description="Maximum company level LACDT value."
        ),
        "lapse_risk": Column(
            float,
            nullable=False,
            description="Company level lapse risk shock."
        )
    },
    strict=False,
    name="base_input_schema",
    description="Schema for the base calcualtion inputs."
)

