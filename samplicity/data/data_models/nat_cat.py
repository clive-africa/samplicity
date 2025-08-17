import pandas as pd
import pandera.pandas as pa
from pandera import Column, DataFrameSchema


class NatCat:
    """Validation of the natural catastrophe data with context"""

    def __init__(self, sam_data):
        # All the difference diversionfication levels
        self.levels = {}
        for lev in [1, 2, 3]:
            self.levels[lev] = (
                sam_data
                .output["data"]["division_detail"][f"level_{lev}"]
                .unique()
                .tolist()
            )
            self.levels[lev].append("__none__")
        # The different RI structures that are allowed
        self.ri_structure = (
            sam_data
            .output["data"]["reinsurance_prog"]
            .index.unique()
            .to_list()
        )
        self.ri_structure.append("__none__")
        self.schema = self._create_schema()

    def _create_schema(self):
        """Create the validation schema with access to self.sam_scr"""
        return DataFrameSchema(
            {
                "level_1": Column(
                    str,
                    parsers=[pa.Parser(lambda s: s.fillna("__none__"))],
                    checks=pa.Check.isin(
                        self.levels[1], error="Invalid division level 1 included."
                    ),
                    nullable=False,
                    unique=False,
                    description="Level 1 division identifier",
                ),
                "level_2": Column(
                    str,
                    parsers=[pa.Parser(lambda s: s.fillna("__none__"))],
                    checks=pa.Check.isin(
                        self.levels[2], error="Invalid division level 2 included."
                    ),
                    nullable=False,
                    unique=False,
                    description="Level 2 division identifier",
                ),
                "level_3": Column(
                    str,
                    parsers=[pa.Parser(lambda s: s.fillna("__none__"))],
                    checks=pa.Check.isin(
                        self.levels[3], error="Invalid division level 3 included."
                    ),
                    nullable=False,
                    unique=False,
                    description="Level 3 division identifier",
                ),
                "ri_structure": Column(
                    str,
                    parsers=[pa.Parser(lambda s: s.fillna("__none__"))],
                    checks=pa.Check.isin(
                        self.ri_structure,
                        error="Invalid reinsurance structure included.",
                    ),
                    nullable=False,
                    unique=False,
                    description="Applicable reinsurance structure for the exposure.",
                ),
                "postal_code": Column(
                    int,
                    checks=[
                        pa.Check.ge(0, error="Postal code must be non-negative."),
                        pa.Check.le(10000, error="Postal code must be below 10 000."),
                    ],
                    nullable=False,
                    unique=False,
                    description="Postal code of sum insured exposure",
                ),

                "res_buildings": Column(
                    float,
                    parsers=[pa.Parser(lambda s: pd.to_numeric(s, errors='coerce').fillna(0.0))],
                    checks=pa.Check.ge(0, error="Residential buildings exposure must not be negative."),
                    nullable=False,
                    unique=False,
                    description="Residential buildings exposure."
                ),

                "comm_buildings": Column(
                    float,
                    parsers=[pa.Parser(lambda s: pd.to_numeric(s, errors='coerce').fillna(0.0))],
                    checks=pa.Check.ge(0, error="Commercial buildings exposure must not be negative."),
                    nullable=False,
                    unique=False,
                    description="Commerical buildings exposure."
                ),

                "contents": Column(
                    float,
                    parsers=[pa.Parser(lambda s: pd.to_numeric(s, errors='coerce').fillna(0.0))],
                    checks=pa.Check.ge(0, error="Contents exposure must not be negative."),
                    nullable=False,
                    unique=False,
                    description="Contents exposure."
                ),

                "engineering": Column(
                    float,
                    parsers=[pa.Parser(lambda s: pd.to_numeric(s, errors='coerce').fillna(0.0))],
                    checks=pa.Check.ge(0, error="Engineering exposure must not be negative."),
                    nullable=False,
                    unique=False,
                    description="Engineering exposure."
                ),

                "motor": Column(
                    float,
                    parsers=[pa.Parser(lambda s: pd.to_numeric(s, errors='coerce').fillna(0.0))],
                    checks=pa.Check.ge(0, error="Motor exposure must not be negative."),
                    nullable=False,
                    unique=False,
                    description="Motor exposure."
                )

            },
            strict=False,
            name="natural_catastrophe_schema",
            description="Schema for checking the natural catastrohe exposure data",
            coerce=True,
        )

    def validate(self, df, **kwargs):
        """Validate the DataFrame"""
        return self.schema.validate(df, **kwargs)


# Usage:
#validator = NatCatValidator(sam_scr)
#test = validator.validate(
#    sam_scr.classes["data"].output["data"]["nat_cat_si"], lazy=True
#)