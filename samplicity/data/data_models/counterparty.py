import pandas as pd
import pandera as pa
from pandera import Column, DataFrameSchema

counterparty_schema = DataFrameSchema(
    parsers=[
        pa.Parser(lambda df: df.assign(counterparty_group=df['counterparty_group'].fillna(df['id'])))
    ],
    columns={
        "id": Column(
            str,
            nullable=False,
            unique=True,
            description="Unique counterparty identifier"
        ),
        "counterparty_name": Column(
            str,
            # checks=[pa.Check.str_length(min_value=1, max_value=250)],  # Uncomment if needed
            nullable=False,
            unique=True,
            description="Counterparty name"
        ),
        "counterparty_cqs": Column(
            int,
            parsers=[
                # Convert to numeric first, coercing errors to NaN
                pa.Parser(lambda s: pd.to_numeric(s, errors='coerce')),
                # Fill null values with 19 and handle downcasting properly
                pa.Parser(lambda s: s.fillna(19).infer_objects(copy=False)),
                # Convert to int64 and clip values
                pa.Parser(lambda s: s.astype('int64').clip(lower=1, upper=19))
            ],
            checks=pa.Check.in_range(min_value=1, max_value=19, error="CQS must be between 1 and 19"),
            nullable=True,
            description="Counterparty Credit Quality Step"
        ),
        "counterparty_equivalent": Column(
            str,
            parsers=[
                pa.Parser(lambda s: s.str.upper()),
                pa.Parser(lambda s: s.fillna('Y'))
            ],
            checks=pa.Check.isin(
                ["Y", "N"],
                error="Must be either 'Y' or 'N'"
            ),
            nullable=True,
            description="Counterparty equivalent indicator check."
        ),
        "counterparty_group": Column(
            str,
            nullable=False,
            description="Counterparty group"
        ),
        "counterparty_group_cqs": Column(
            int,
            parsers=[
                # Convert to numeric first, coercing errors to NaN
                pa.Parser(lambda s: pd.to_numeric(s, errors='coerce')),
                # Fill null values with 19 and handle downcasting properly
                pa.Parser(lambda s: s.fillna(19).infer_objects(copy=False)),
                # Convert to int64 and clip values
                pa.Parser(lambda s: s.astype('int64').clip(lower=1, upper=19))
            ],
            nullable=True,
            description="Counterparty group Credit Quality Step"
        ),
        "counterparty_collateral": Column(
            float,
            parsers=[
                # Use a more explicit approach to avoid the warning
                pa.Parser(lambda s: pd.to_numeric(s, errors='coerce').fillna(0.0)),
                pa.Parser(lambda s: s.astype(float))  # Convert to float
            ],
            checks=pa.Check.greater_than_or_equal_to(0, error="Collateral must be non-negative"),
            nullable=False,
            description="Counterparty collateral information"
        )
    }, 
    strict=False,
    name="counterparty_schema",
    description="Schema for counterparty reference data"
)
