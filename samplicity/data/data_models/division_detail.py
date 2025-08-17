import pandas as pd
import pandera as pa
from pandera import Column, DataFrameSchema



division_detail_schema = DataFrameSchema(
    columns={
        "level_1": Column(
            str,
            nullable=True,
            description="Level 1 identifier"
        ),
        "level_2": Column(
            str,
            nullable=True,
            description="Level 2 identifier"
        ),
        "level_3": Column(
            str,
            nullable=True,
            description="Level 3 identifier"
        ),
        "tax_percent": Column(
            float,
            parsers=[pa.Parser(lambda s: pd.to_numeric(s, errors='coerce').fillna(0.0))],
            checks=pa.Check.greater_than_or_equal_to(0, error="tax_percent must be non-negative"),
            nullable=True,
            description="Tax percentage"
        ),
        "max_lacdt": Column(
            float,
            parsers=[pa.Parser(lambda s: pd.to_numeric(s, errors='coerce').fillna(0.0))],
            nullable=True,
            description="Maximum LACDT value"
        ),
        "scr_cover_ratio": Column(
            float,
            parsers=[pa.Parser(lambda s: pd.to_numeric(s, errors='coerce').fillna(0.0))],
            checks=pa.Check.greater_than_or_equal_to(0, error="SCR cover ratio must be non-negative"),
            nullable=True,
            description="SCR cover ratio"
        ),
        "lapse_risk": Column(
            float,
            parsers=[pa.Parser(lambda s: pd.to_numeric(s, errors='coerce').fillna(0.0))],
            nullable=False,
            description="Lapse risk information"
        )
    },
    strict=False,
    name="division_detail_schema",
    description="Schema for division detail data"
)

