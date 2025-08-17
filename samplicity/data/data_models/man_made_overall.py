import pandas as pd
import pandera.pandas as pa
from pandera import Column, DataFrameSchema


class ManMadeOverall:
    """Validation of the natural catastrophe data with context"""

    def __init__(self, sam_scr):
        # All the difference diversionfication levels

        # The different RI structures that are allowed
        self.ri_structure = (
            sam_data["reinsurance_prog"]
            .output["data"]["division_detail"][f"level_{lev}"]
            .unique()
            .tolist()
        )
        self.ri_structure.append("__none__")
        self.schema = self._create_schema()

    def _create_schema(self):
        """Create the validation schema with access to self.sam_scr"""
        return DataFrameSchema(
    columns={
        "mm_event": Column(
            str,
            checks=pa.Check.isin(['mm_motor','mm_fire_property','mm_marine','mm_aviation','mm_liability','mm_credit_guarantee','mm_terrorism','mm_accident_health'], 
                                 error="Invalid man-made event type specified.")
            nullable=False,
            description="Man-Made Event Type"
        ),
        "gross_event": Column(
            float,
            checks=pa.Check.greater_than_or_equal_to(0),
            coerce=True,
            default=0,
            nullable=True,
            description="Company name"
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
            description="Applicable reinsurance structure for the event.",
        ),
    },
    strict=False,
    name="man_made_overall_schema",
    description="Schema for the overal man-made events."
)

