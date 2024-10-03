from typing import Literal, Optional
from pydantic import BaseModel, ValidationInfo, field_validator, ValidationError, Field, model_validator, validator
import datetime

# Something weird ahppesn between Excel, xlwings and Pandas.
from pandas._libs.tslibs.nattype import NaTType

# A generic function that will be used across multiple data models
def convert_none_to_value(data: dict, field_mapping: dict, info) -> dict:
    
    # Get the information we need from the context
    context = info.context
    record_id = context.get('record_id', None) if context else None
    data_conversions=info.context.get('data_conversions', None) if context else None
    
    for fld, val in field_mapping.items():
        if fld in data and data[fld] is None:
            data_conversions.append({
                'table': 'division_detail',
                'row': record_id,
                'field': fld,
                'old_value': None,
                'new_value': val                    
            })
            data[fld] = val
    return data

# The data model for division_detai

class division_detail(BaseModel):
    level_1: Optional[str | int] = None
    level_2: Optional[str | int] = None
    level_3: Optional[str | int] = None
    tax_percent: float = 0.0
    max_lacdt: float = 0.0
    scr_cover_ratio: float = 0.0
    lapse_risk: float = 0.0
    
    @model_validator(mode='before')
    @classmethod
    def convert_none(cls, data: dict, info) -> dict:
        
        field_mapping = {"scr_cover_ratio": 0, "lapse_risk": 0, "tax_percent": 0, "max_lacdt": 0}
        data=convert_none_to_value(data, field_mapping, info)
        return data

# The data model for counterparty

class counterparty(BaseModel):
    id: str | int
    counterparty_name: str
    counterparty_cqs: float = Field(None, ge=0, le=19)
    counterparty_equivalent: Literal["Y", "N"]
    counterparty_group: Optional[str | int] = None
    counterparty_group_cqs: Optional[float] = None
    counterparty_collateral: float = None

    @model_validator(mode='before')
    @classmethod
    def convert_none(cls, data: dict, info) -> dict:
        
        field_mapping = {"counterparty_cqs": 19, "counterparty_equivalent": 'N', "counterparty_collateral": 0}
        data=convert_none_to_value(data, field_mapping, info)
        return data

# The data model for the table asset shocks

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

# The data model for asset_data

class asset_data(BaseModel):
    id: str | float
    asset_description: Optional[str]
    level_1: Optional[str | int] = None
    level_2: Optional[str | int] = None
    level_3: Optional[str | int] = None
    asset_type: str
    counterparty_id: str | float
    asset_cqs: float = Field(None, ge=0.0, le=19.0)
    lgd_adj: float = None
    mod_duration: float
    market_value: float
    nominal_value: float
    collateral: float = None
    maturity_date: Optional[datetime.date] = None
    coupon: float
    spread: float
    coupon_freq: float
    bond_type: Optional[str] = None
    equity_volatility_shock: float
    spread_credit_up_shock: float
    spread_credit_down_shock: float

    @model_validator(mode='before')
    @classmethod
    def convert_none(cls, data: dict, info) -> dict:
        
        field_mapping = {"lgd_adj": 0.45, "collateral": 0.0, "equity_volatility_shock": 0.0, 
                         "spread_credit_up_shock": 0.0, "spread_credit_down_shock": 0.0}
        data=convert_none_to_value(data, field_mapping, info)
        return data

    @validator('maturity_date', pre=True)
    def parse_maturity_date(cls, value):
        # Need to hanlde a weird issue that crashes Pydantic here.
        if value == '' or value is None or isinstance(value, NaTType):
            return None
        if isinstance(value, datetime.date):
            return value
        try:
            return datetime.datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            raise ValueError('Invalid date format. Use YYYY-MM-DD')


# The data model for reinsurance

class reinsurance(BaseModel):
    # Will change this in future but we import this as an index.
    # Must change this.
    #id: str | int
    contract_type: Literal["prop", "xol"]
    ri_share: float = Field(None, ge=0.0, le=1.0)
    excess: float | None
    layer_size: float | None = Field(None, ge=0)
    reinstate_count: int | None = Field(None, ge=0)
    reinstate_rate: float | None = Field(None, ge=0)

# The data model for reinsurance_share

class reinsurance_share(BaseModel):
    reinsurance_id: str | int
    counterparty_id: str | int
    counterparty_share: float = Field(None, ge=0.0, le=1.0)

# The data model for prem_res

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

    @model_validator(mode='before')
    @classmethod
    def convert_none(cls, data: dict, info) -> dict:
        
        field_mapping = {"gross_p": 0.0, "gross_p_last": 0.0, "gross_p_last_24": 0.0, 
                         "gross_fp_existing": 0.0, "gross_fp_future": 0.0, "gross_claim": 0.0,
                         "gross_other": 0.0, "net_p": 0.0, "net_p_last": 0.0, "net_p_last_24": 0.0, 
                         "net_fp_existing": 0.0, "net_fp_future": 0.0, "net_claim": 0.0,
                         "net_other": 0.0}
        data=convert_none_to_value(data, field_mapping, info)
        return data

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

    @model_validator(mode='before')
    @classmethod
    def convert_none(cls, data: dict, info) -> dict:
        
        field_mapping = {"res_buildings": 0.0, "comm_buildings": 0.0, "contents": 0.0, 
                         "engineering": 0.0, "motor": 0.0}
        data=convert_none_to_value(data, field_mapping, info)
        return data

