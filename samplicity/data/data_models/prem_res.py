import pandas as pd
import pandera as pa
from pandera import Column, DataFrameSchema


class PremRes:
    """Validation of the natural catastrophe data with context"""

    def __init__(self, sam_scr):
        # All the difference diversionfication levels
        self.levels = {}
        for lev in [1, 2, 3]:
            self.levels[lev] = (
                sam_scr.classes["data"]
                .output["data"]["division_detail"][f"level_{lev}"]
                .unique()
                .tolist()
            )
            # We will degault all missing, null values to '__none__'
            self.levels[lev].append("__none__")

        # The different RI structures that are allowed
        self.ri_structure = (
            sam_scr.classes["data"]
            .output["data"]["reinsurance_prog"]
            .index.unique()
            .to_list()
        )

        # We will degault all missing, null values to '__none__'
        self.ri_structure.append("__none__")

        self.ri_contracts = (
            sam_scr.classes["data"]
            .output["data"]["ri_contract"]
            .index.unique()
            .tolist()
        )
        self.ri_contracts.append("__none__")

        self.lob=["1a",  "1b",  "2a",  "2b",  "3i",  "3ii",  "3iii",  "4i"] \
                +["4ii",  "5i",  "5ii",  "6i",   "6ii", "7i", "7ii", "8i", "8ii"] \
                +[ "9", "10i", "10ii", "10iii", "10iv", "10v", "10vi", "10vii"] \
                +["11", "12", "13", "14", "15", "16i", "16ii", "16iii", "17i"] \
                +["17ii", "17iii", "17iv", "18b", "18c"]

        self.schema = self._create_schema()

    def _create_schema(self):
        """Create the validation schema with access to self.sam_scr"""
        
        # We have a number of repeated columsn with the same conditions
        # To avoid keepign the schema repetitive, we will create a helper function
        
        base_cols = {
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
                "lob_type": Column(
                    str,
                    checks=pa.Check.isin(
                        ["D", "P", "NP", "O", "FP", "FNP", "FO"],
                        error="Invalid type of business included.",
                    ),
                    nullable=False,
                    unique=False,
                    description="Type of business",
                ),
                "lob": Column(
                    str,
                    checks=pa.Check.isin(self.lob, error="Invalid line of business included.",
                    ),
                    nullable=False,
                    unique=False,
                    description="Line of business",
                ),
                "include_factor_cat": Column(
                    str,
                    # We inlcude some conversions to convert yes, no to Y, N
                    parsers=[
                        pa.Parser(lambda s: s.fillna("N").str.upper().str[0])
                    ],
                    checks=pa.Check.isin(['Y', 'N'], error="Include factor catastrophe must be 'Y' or 'N'."),
                    nullable=False,
                    unique=False,
                    description="Include factor catastrophe",
                ),
                "include_non_prop_cat": Column(
                    str,
                    # We inlcude some conversions to convert yes, no to Y, N
                    parsers=[
                        pa.Parser(lambda s: s.fillna("N").str.upper().str[0])
                    ],
                    checks=pa.Check.isin(['Y', 'N'], error="Include non-proportional catastrophe msut be 'Y' or 'N'."),
                    nullable=False,
                    unique=False,
                    description="Include non-proportional catastrophe",
                ),
                "reinsurance_id": Column(
                    str,
                    parsers=[pa.Parser(lambda s: s.fillna("__none__"))],
                    checks=pa.Check.isin(self.ri_contracts, error="Invalid reinsurance contract."
                    ),
                    nullable=False,
                    unique=False,
                    description="Reinsurance contract",
                ),
                "ri_strcuture": Column(
                    str,
                    parsers=[pa.Parser(lambda s: s.fillna("__none__"))],
                    checks=pa.Check.isin(self.ri_structure, error="Invalid reinsurance structure."
                    ),
                    nullable=False,
                    unique=False,
                    description="Reinsurance structure",
                )
        }
        
        amount_cols={}
        ri_map={'gross': 'Gross', 'net': 'Net'}
        col_map={
            '_p': 'premium',
            '_p_last': 'last year premium',
            '_p_last_24': 'prior year premium',
            '_fp_existing': 'future premium of existing business',
            '_fp_future': 'future premium of new business',
            '_claim': 'claims provisions',
            '_other': 'other provisions'
        }
        for ri in ['gross','net']:
            for col in ['_p',	'_p_last',	'_p_last_24','_fp_existing','_fp_future','_claim','_other']:   
                
                amount_cols[f"{ri}{col}"]=Column(
                    float,
                    parsers=[pa.Parser(lambda s: pd.to_numeric(s, errors='coerce').fillna(0.0))],
                    nullable=False,
                    unique=False,
                    description=f"{ri_map[ri]} {col_map[col]}",
                )


        return DataFrameSchema(base_cols | amount_cols,            strict=False,
            name="natural_catastrophe_schema",
            description="Schema for checking the natural catastrohe exposure data",
            coerce=True)
        
    def validate(self, df, **kwargs):
        """Validate the DataFrame"""
        return self.schema.validate(df, **kwargs)


# Usage:
#validator = PremResValidator(sam_scr)
#test = validator.validate(
#    sam_scr.classes["data"].output["data"]["prem_res"], lazy=True
#)
