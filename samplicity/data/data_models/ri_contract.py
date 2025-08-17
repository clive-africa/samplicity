
import pandas as pd
import pandera as pa
from pandera import Column, DataFrameSchema, Index

reinsurance_schema = DataFrameSchema(
    columns={
        "contract_type": Column(pa.String, nullable=False, checks=pa.Check.isin(["prop", "xol"])),
        "ri_share": Column(pa.Float, nullable=False, checks=pa.Check.gt(0), coerce=True),
        "excess": Column(pa.Float, nullable=True, checks=pa.Check.gt(0), coerce=True),
        "layer_size": Column(pa.Float, nullable=True, checks=pa.Check.gt(0), coerce=True),
        "reinstate_count": Column(
            "Int64", 
            parsers=[
                pa.Parser(lambda s: pd.to_numeric(s, errors='coerce').fillna(0)),  # Fill NaN with 0
                pa.Parser(lambda s: s.astype('Int64'))
            ],
            nullable=True, 
            checks=pa.Check.ge(0)  # Adjusted to allow 0 after fillna
        ),
        "reinstate_rate": Column(pa.Float, nullable=True, checks=pa.Check.gt(0), coerce=True),
    },
    index=Index(pa.String, name="id", unique=True)
)

#reinsurance_schema.validate(sam_scr.classes['data'].output['data']['reinsurance_prog'], lazy=True)

