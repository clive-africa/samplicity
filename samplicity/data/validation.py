import pandas as pd
import numpy as np
import datetime
import logging

# from pydantic import BaseModel

from typing import Literal
from pydantic import BaseModel, ValidationInfo, field_validator, ValidationError, Field

logger = logging.getLogger(__name__)


class divsion(BaseModel):
    divsion: str | int


class product(BaseModel):
    product: str | int


class division_detail(BaseModel):
    level_1: Optional[str | int] = None
    level_2: Optional[str | int] = None
    level_3: Optional[str | int] = None
    tax_percent: float = None
    max_lacdt: float = None
    scr_cover_ratio: float = None
    lapse_risk: float = None

    @field_validator(
        "scr_cover_ratio", "lapse_risk", "tax_percent", "max_lacdt", mode="before"
    )
    @classmethod
    def default_zero(cls, v, info: ValidationInfo):
        if v is None:
            print(f"Set a default value of 0.0 for {info.field_name}")
            return 0.0
        else:
            return v


class counterparty(BaseModel):
    id: str | int
    counterparty_name: str
    counterparty_cqs: float = Field(None, ge=0, le=19)
    counterparty_equivalent: Literal["Y", "N"]
    counterparty_group: Optional[str | int] = None
    counterparty_group_cqs: Optional[float] = None
    counterparty_collateral: float = None

    @field_validator(
        "counterparty_cqs",
        "counterparty_collateral",
        "counterparty_equivalent",
        mode="before",
    )
    @classmethod
    def default_zero(cls, v, info: ValidationInfo):
        if v is None and info.field_name == "counterparty_cqs":
            print(f"Set a default value of 19 for {info.field_name}")
            return 19.0
        elif v is None and info.field_name == "counterparty_collateral":
            print(f"Set a default value of 0 for {info.field_name}")
            return 0.0
        elif v is None and info.field_name == "counterparty_equivalent":
            print(f"Set a default value of N for {info.field_name}")
            return "N"
        elif info.field_name == "counterparty_equivalent":
            return v.upper()
        else:
            return v

    @field_validator("counterparty_group")
    @classmethod  # Optional, but your linter may like it.
    def check_counterparty_group(cls, v, info: ValidationInfo):
        c_party = np.unique(sam_data.output["data"]["asset_data"]["id"])
        if v is not None and v not in c_party:
            raise ValueError("Not a valid counterparty group")
        return v


class asset_shocks(BaseModel):
    asset_type: str
    shock: Literal[
        "concentration",
        "concentration_government",
        "credit_type_3",
        "default_type_1",
        "default_type_2",
        "default_type_2_overdue",
        "equity_sa",
        "interest_rate",
        "spread",
        "spread_risk",
    ]


class asset_data(BaseModel):
    id: str | int
    asset_description: str
    level_1: Optional[str | int] = None
    level_2: Optional[str | int] = None
    level_3: Optional[str | int] = None
    asset_type: str
    counterparty_id: str | int
    asset_cqs: float = Field(None, ge=0, le=19)
    lgd_adj: float
    mod_duration: float
    market_value: float
    nominal_value: float
    collateral: float = None
    # bond_type_old: str
    maturity_date: datetime.date
    coupon: float
    spread: float
    coupon_freq: float
    bond_type: str
    equity_volatility_shock: float
    spread_credit_up_shock: float
    spread_credit_down_shock: float

    @field_validator("asset_type", "counterparty_id")
    @classmethod  # Optional, but your linter may like it.
    def check_asset_type(cls, v, info: ValidationInfo):
        asset_type = np.unique(sam_data.output["data"]["asset_shocks"]["asset_type"])
        if v not in asset_type:
            raise ValueError("Not a valid asset type.")
        return v

    @field_validator("counterparty_id")
    @classmethod  # Optional, but your linter may like it.
    def check_counterparty(cls, v, info: ValidationInfo):
        counterparty = np.unique(sam_data.output["data"]["counterparty"]["id"])
        if v not in counterparty:
            raise ValueError("Not a valid counterparty.")
        return v


class ri_contract(BaseModel):
    id: str | int
    contract_type: Literal["prop", "xol"]
    ri_share: float = Field(None, ge=0.0, le=1.0)
    excess: float | None
    layer_size: float | None = Field(None, ge=0)
    reinstate_count: int | None = Field(None, ge=0)
    reinstate_rate: float | None = Field(None, ge=0)


class ri_share(BaseModel):
    reinsurance_id: str | int
    counterparty_id: str | int
    counterparty_share: float = Field(None, ge=0.0, le=1.0)

    @field_validator("reinsurance_id")
    @classmethod
    def check_reinsurance(cls, v, info: ValidationInfo):
        ri = np.unique(sam_data.output["data"]["ri_contract"].index)
        if v not in ri:
            raise ValueError("Not a valid reinsurance contract.")
        return v

    @field_validator("counterparty_id")
    @classmethod
    def check_counterparty(cls, v, info: ValidationInfo):
        counterparty = np.unique(sam_data.output["data"]["counterparty"]["id"])
        if v not in counterparty:
            raise ValueError("Not a valid counterparty.")
        return v


class prem_res(BaseModel):
    level_1: Optional[str | int] = None
    level_2: Optional[str | int] = None
    level_3: Optional[str | int] = None
    lob_type: Literal["D", "P", "NP", "O", "FP", "FNP", "FO"]
    lob: Literal[
        "1a",
        "1b",
        "2a",
        "2b",
        "3i",
        "3ii",
        "3iii",
        "4i",
        "4ii",
        "5i",
        "5ii",
        "6i",
        "6ii",
        "7i",
        "7ii",
        "8i",
        "8ii",
        "9",
        "10i",
        "10ii",
        "10iii",
        "10iv",
        "10v",
        "10vi",
        "10vii",
        "11",
        "12",
        "13",
        "14",
        "15",
        "16i",
        "16ii",
        "16iii",
        "17i",
        "17ii",
        "17iii",
        "17iv",
        "18b",
        "18c",
    ]
    gross_p: float = None
    gross_p_last: float = None
    gross_p_last_24: float = None
    gross_fp_existing: float = None
    gross_fp_future: float = None
    gross_claim: float = None
    gross_other: float = None
    net_p: float = None
    net_p_last: float = None
    net_p_last_24: float = None
    net_fp_existing: float = None
    net_fp_future: float = None
    net_claim: float = None
    net_other: float = None
    include_factor_cat: Literal["Y", "N"]
    include_non_prop_cat: Literal["Y", "N"]
    reinsurance_id: Optional[str | int]
    ri_structure: Optional[str | int]

    @field_validator(
        "gross_p",
        "gross_p_last",
        "gross_p_last_24",
        "gross_fp_existing",
        "gross_fp_future",
        "gross_claim",
        "gross_other",
        "net_p",
        "net_p_last",
        "net_p_last_24",
        "net_fp_existing",
        "net_fp_future",
        "net_claim",
        "net_other",
        mode="before",
    )
    @classmethod
    def default_zero(cls, v, info: ValidationInfo):
        if v is None:
            print(f"Set a default value of 0.0 for {info.field_name}")
            return 0.0
        else:
            return v

    @field_validator("include_factor_cat", "include_non_prop_cat", mode="before")
    @classmethod
    def upper_case(cls, v, info: ValidationInfo):
        return v if v is None else v.upper()

    @field_validator("reinsurance_id", "ri_structure")
    @classmethod
    def check_reinsurance(cls, v, info: ValidationInfo):
        # ri=np.unique(sam_data.output["data"]['ri_contract'].index)
        # if v not in ri:
        #    raise ValueError("Not a valid reinsurance contract.")
        return v


class nat_cat_si(BaseModel):
    level_1: Optional[str | int] = None
    level_2: Optional[str | int] = None
    level_3: Optional[str | int] = None
    ri_structure: Optional[str | int] = None
    postal_code: int = Field(None, gt=0, lt=10000)
    res_buildings: float = None
    comm_buildings: float = None
    contents: float = None
    engineering: float = None
    motor: float = None

    @field_validator(
        "res_buildings",
        "comm_buildings",
        "contents",
        "engineering",
        "motor",
        mode="before",
    )
    @classmethod
    def default_zero(cls, v, info: ValidationInfo):
        if v is None:
            print(f"Set a default value of 0.0 for {info.field_name}")
            return 0.0
        else:
            return v


def validate_df_data(
    df: pd.DataFrame, model: BaseModel, index_offset: int = 2
) -> tuple[list, list]:
    # Python index starts at 0, excel at 1, and 1 row for the header in Excel

    # We only want the data that our application requires
    # We drop the other data
    df = df[model.model_fields.keys()]

    # capturing our good data and our bad data
    good_data = []
    bad_data = []
    df_rows = df.to_dict(orient="records")
    for index, row in enumerate(df_rows):
        try:
            model(**row)  # unpacks our dictionary into our keyword arguments
            good_data.append(row)  # appends valid data to a new list of dictionaries
        except ValidationError as e:
            # Adds all validation error messages associated with the error
            # and adds them to the dictionary
            row["Errors"] = [error_message["msg"] for error_message in e.errors()]

            row["Error_row_num"] = index + index_offset
            bad_data.append(row)  # appends bad data to a different list of dictionaries

    return (good_data, bad_data)


data = sam_data.output["data"]["asset_shock"]
df_dict = data.to_dict("list")
good, bad = validate_df_data(data, division_detail, 0)
good, bad = validate_df_data(data, counterparty, 0)


def f_check_integrity(
    self,
    data_check,
    parent_table,
    parent_field,
    parent_meta,
    child_table,
    child_field,
    child_meta,
):
    """Ensure data provided complies with referential integrity rules."""
    logger.debug("Function start")

    # We assume that there ahs been an error
    error = True

    # Get all of the unique child values.
    if child_table == "manual":
        child_values = pd.DataFrame(child_field.split(","), columns=["manual"])
    elif child_meta:
        child_values = np.unique(self.data_meta[child_table][[child_field]])
    else:
        child_values = np.unique(self.data_files[child_table][[child_field]])

    # Get all of the parent values
    # We don't need to worry about these values being unique for the
    # comparison. We do however chekc to see if they are unique.
    if parent_table == "manual":
        parent_values = pd.DataFrame(parent_field.split(","), columns=["manual"])
    if parent_meta:
        parent_values = self.data_meta[child_table][[child_field]]
    else:
        parent_values = self.data_files[child_table][[child_field]]

    # Now we check that the length are the same
    if len(parent_values) != len(np.unique(parent_values)):
        error_values = parent_values.loc[parent_values.duplicated(), :]
        error_values = error_values.str.cat(sep=", ")
        error_values = error_values[:150]
        df = pd.Dataframe(
            [
                [data_check],
                ["Critical Failue"],
                [
                    "The values in "
                    + parent_table
                    + ":"
                    + parent_field
                    + " are not unique."
                ],
                [error_values],
            ],
            columns=self.output["data_validation"].columns,
        )

    else:
        df = pd.Dataframe(
            [
                [data_check],
                ["Pass"],
                ["The values in " + parent_table + ":" + parent_field + " are unique."],
                ["None"],
            ],
            columns=self.output["data_validation"].columns,
        )

    self.output["data_validation"].append(df, ignore_index=True)

    # Noe we chekc if the result retunrs referential integrity
    child_unique = np.unique(child_values)
    diff = child_unique.difference(parent_values)
    if len(diff) > 0:
        error_values = diff.str.cat(sep=", ")
        error_values = error_values[:150]
        df = pd.Dataframe(
            [
                [data_check],
                ["Critical Failue"],
                [
                    "The values in "
                    + child_table
                    + ":"
                    + child_field
                    + " are not found in "
                    + parent_table
                    + ":"
                    + parent_field
                    + "."
                ],
                [error_values],
            ],
            columns=self.output_error.columns,
        )
    else:
        df = pd.Dataframe(
            [
                [data_check],
                ["Pass"],
                [
                    "The values in "
                    + child_table
                    + ":"
                    + child_field
                    + " are all found in "
                    + parent_table
                    + ":"
                    + parent_field
                    + "."
                ],
                ["None"],
            ],
            columns=self.output_error.columns,
        )
    self.output["data_validation"].append(df, ignore_index=True)


def f_data_checks(self):
    """Perform various data checks on the input data provided."""
    logger.debug("Function start")

    # This seems odd but the data checks are being hard-coded in this code.
    # I feel this si necessary as they input could change.
    # Given their importance we want to keep the checks in the code.
    # TODO:
    # Code needs to be developed here
    # Curretnly just return True

    # #####

    # BASE INPUTS

    # #####

    # Need to chekc if our base inputs have been populated
    for test in ["valuation_date", "diversification_level", "calculation_level"]:
        tmp = self.f_data("data", test)[0]
        # We ahve to ahve a value in these fields for the calculation work
        if tmp == None:
            logger.critical(f"{test} must be populated.")
            raise ValueError
        else:
            logger.info(f"{test} was populated as required.")
    # Need to check if the valuation date is future dated
    tmp = self.f_data("data", "valuation_date")[0]
    if tmp > datetime.now():
        logger.warning("The valuation date is future dated.")
        raise ValueError
    else:
        logger.info("The valuation date is in the past.")

    # Chekc to see if the diversification level has teh correct values
    tmp = self.f_data("data", "diversification_level")[0]
    if tmp not in ("level_1", "level_2", "level_3"):
        logger.critical(
            f"The value for the diversification " f"level {tmp} is not valid."
        )
        raise ValueError
    else:
        logger.info("Diversification level is valid.")

    # Chekc to see if the calculation level has been set correctly
    tmp = self.f_data("data", "calculation_level")[0]
    if tmp not in ("diversification", "overall", "individual"):
        print(f"The value for the calculation " f"level {tmp} is not valid.")
        raise ValueError
    else:
        logger.info("Calculation level is valid.")

    # The remaining fields shold be populated but they can be blank.
    for test in ["tax_percent", "max_lacdt", "lapse_risk"]:
        tmp = self.f_data("data", test)[0]
        # We ahve to ahve a value in these fields for the calculation work
        if tmp is None:
            logger.warning(f"{tmp} was not populated and " "has been set to zero.")
        else:
            logger.warning(f"{tmp} was populated.")

    # We now set all the na values to 0
    # Teh .loc seems to be causing issues with the fillna formula
    self.output["data"]["base_inputs"].loc[
        ["tax_percent", "max_lacdt", "lapse_risk"], "base_inputs"
    ] = (
        self.output["data"]["base_inputs"]
        .loc[["tax_percent", "max_lacdt", "lapse_risk"], "base_inputs"]
        .fillna(0)
    )

    # #####

    # MAN MADE OVERALL

    # #####
    tmp = self.output["data"]["man_made_overall"]
    tmp = tmp[tmp["gross_event"].isna()]
    tmp_vals = tmp.index.values
    if len(tmp_vals) > 0:
        logger.warning(f"{tmp_vals} were not populated and " "has been set to zero.")

    # Need to add for the reinsurance arrangements

    # #####

    # COUNTERPARTY

    # #####

    counterparty = self.output["data"]["counterparty"]

    # Check the ID is populated
    tmp = counterparty["id"]
    if sum(tmp.isna()) > 0:
        logger.critical("All counterparties are required to have an ID.")
        raise ValueError

    if len(np.unique(tmp)) != len(tmp):
        logger.critical("All counterparties ID's must be unique.")
        raise ValueError

    # Check if a name has been populated
    tmp = counterparty["name"]

    return True
