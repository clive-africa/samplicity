=====================
Samplicity Inputs
=====================
*samplicity* requires numerous inputs to accurately calculate the SAM non-life SCR. This document provides a high-level description of the *tables* and *fields* that are required by *samplicity*.

Input Tables
=====================
In the table below a high level description of all the input tables is provided.

Table | Description
------ | ------
base_inputs   | Various high level *configuration* inputs that are used in the model and apply to the overall SCR calculation.
division_detail | Details the different 'divisions' used in the calculation. Divisions are used primarily to allocate diversification benefits and calculate SCR figures by 'division'.
counterparty | Details the various counterparties used in the SCR calculation.
reinsurance | Captures the different reinsurance contracts that are used in the calculation.
reinsurance_share | Details the participation of each counterparty in each reinsurance contract.
reinsurance_programme | Captures the struture of reinsurance contracts. The values in the table detail the 'order' in which the contracts are applied.
asset_mapping | Captures the mapping of different *asset_types* to the shocks defines in *Samplicity*.
asset_data | Captures all the assets and their respective details that are needed in the market risk calculation.
man_made_overall | Details the man-made catastrophe events for the overall entity.
man_made_division_event | Captures the gross man-made events for each division in the calculation.
man_made_division_reinsurance | Captures the reinsurance structure applicable for each man made event for each division.

other_balances | This is still under development. It is intended to capture all the other balance sheet shocks not calculated in the tool.
nat_cat | Captures the sum insured for use in the natural catastrophe shock.
prem_res | Capture all of th premuium, claim and reinsurance information for used in the premium and reserve calculatiion - as well at the factors based catastrophe calculation.
asset_mapping | Captures that shocks that should be applied to the various 'asset types' in the asset_data information.

Field Definitions
=====================

base_inputs
-------------
This table contains the high-level configuration inputs that are used in the SCR calculation. Most of the fields are self-explanatory but some should be explained in further detail.

**diversification_level**
*samplicity* allows for up to 3 levels of diversification to be captured. Importantly:
* The different levels (1,2,3) have no heirachy whatsoever.
* They do not all have to be populated for the calcualtion to run.
The functionality was developed within *Samplicity* to try encourage teams to apply a more scientific approach to capital allocation. The different diversification levels also have use for cell captive and group SCR calculations. Effectively the different *divisions* and *levels* can be seen as a grouping and filtering mechanism within *Samplicity*.

Field | Description
------ | ------
valuation_date | The date at which the SCR calculation is performed.
company_name | The name of the company for which the SCR calculation is performed.
diversification_level | Which field shold be used for the diversification allocation. It should be either of *level_1, level_2, level_3*.
calculation_level | This should be the granularity at whch calculations are performed. It should be either of *diversification, individual, overall*.
investment_division | This is the 'division' which is used to store all common assets. *This feature is still under development*.
tax_percent | The tax percentage that should be used in the LACDT calculation for the overall company.
max_lacdt | The maximum LACDT asset that should be created.
lapse_risk | The lapse risk needs to be manually calculated and captured in this version of the tool.

division_detail
-----------------
Field | Description
------ | ------
level_1	| The name of the division for level 1 calculations.
level_2	| The name of the division for level 2 calculations.
level_3	| The name of the division for level 3 calculations.
tax_percent	| The tax percentage that should be used for each division in their individual calcualtions.
max_lacdt | The maximum tax asset that can be created for each division.
scr_cover_ratio	| The SCR cover ratio that is targetted for eahc division. *This feature is still under development*.
lapse_risk | The manually calculated lapse risk for each division. Samplicity will simply add lapse risk for all combinations of divisions.

counterparty
-----------------
Field | Description
------ | ------
id | This is a short (unique) name - or integer value - for each counterparty. This will be used as a *foreign* key in tables where required.
counterparty_name | This is the name fo the counterparty
counterparty_cqs | The CQS fo the (individual) counterparty.
counterparty_equivalent | This denotes if the counterparty is equivalent. *Currentky ignored by the application*.
counterparty_group | This is the *id* of the group to whcih the counterparty belongs. If left blank it will be populated wit the id of the counterparty.
counterparty_group_cqs | This should be populated for the main *group* counterparty. The CQS for the group. If this is not populated then *Samplicity* will attempt to estimate the group CQS.
counterparty_collateral | The counterparty held for the counterparty. This should be additional collateral held in addition to any asset specific collateral.


### reinsurance
Field | Description
------ | ------
id | This is a short (unique) name - or integer value - for each reinsurance contract. This will be used as a *foreign* key in tables where required.
contract_type | This si the type of reinsurance contract. At present it should be either of *prop, xol*.
ri_share | This is the portion of the losses that are paid by the reinsurance contract.
excess | This is the excess before recovereis are made from the contract. *Not used for prop contract types*. 
layer_size | This is the maximum amount that can be recovered from the reinsurance contract. *It is used for both prop and xol contracts.*
reinstate_count | This is the number of reinstatements that can be applied. *Not used for prop contract types*.
reinstate_rate | This is additional premium paid for eahc reinstatement. *Not used for prop contract types*.


### reinsurance_share
Field | Description
------ | ------
reinsurance_id | The reinsurance contract that the row relates to. References id on table reinsurance.
counterparty_id | The counterparty that the row relates to. References counterparty-id
counterparty_share | Thsi si the share of the reinsurance contratc that belongs to the counterparty. Unless teh contract is not fully filled, all entries for a reinsurance contract should add to 100%.


### reinsurance_programme
The structure of the reinsurance_programe tables differs for the Excel and database input. This table captures the allocation of the different reinsurance contracts to the various riensurance structures. Multiple reinsurance structures form the reinsurance programme.
Field | Description
------ | ------
reinsurance_id | The reinsurance contract that the row relates to. References id on table reinsurance.
ri_structure ... | The various reinsurance structures to which the contracts belong.

The values within the table should capture the order in which the reinsurance contracts are applied - with a value rangin from 1 upward.

For xol and simialr contracts that should be applied to the same gross loss, the contracts should share the same order value. Each time the vlaue of the 'order' increases the gross loss is reduced by the reinsurance recoveries.

### asset_mapping


### asset_data
Field | Description
------ | ------
id | This is a short unique name - or integer value - for each instrument.
asset_description | This is a short description for eahc instrument.
level_1 |  The name of the division for level 1 calculations.
level_2 |  The name of the division for level 2 calculations.
level_3 |  The name of the division for level 3 calculations.
asset_type | This is the type of asset. The type of asset should match those captured in
counterparty_id | 
asset_cqs | 
lgd_adj | 
mod_duration | 
market_value | 
nominal_value | 
collateral | 
bond_type_old | 
maturity_date | 
coupon | 
spread | 
coupon_freq | 
bond_type | 
equity_volatility_shock | 
spread_credit_up_shock | 
spread_credit_down_shock | 


### prem_res
As noted previosuly this table contains the various inputs for the calcualtion of:

* Premium and Reserve Risk
* Factor Based Catastrophe Risk
* Non Proportional Catastrophe Risk
* Operational Risk

All these inputs are stored in one place to limit the volume of data capturing and limit errors.


The inputs for lob_type and lob differ a little from the standard PA workbook. This has been doen deliberately to simplify the imputs and align the various calcualtions. The different input vlaues for these fields are described below.

#### lob_type
The lob_type field captures the 'type' of prmium transaction. A couple values are accepted:

* D: Direct Business
* P: Proportional Treaty Reinsurance Inwards
* NP: Non-Proportional Treaty Reinsurance Inwards
* O: Other Insurance Risk Mitigation Treaty Reinsurance Inwards
* FP: Faculative Proportional Reinsurance Inwards
* FNP: Faculative Non-Proportional Reinsurance Inwards
* FO: Faculative Other Insurance Risk Mitigation Reinsurance Inwards

Within *Samplicity* the code will make sure that, using the lob_type and lob field, the data is mapped to the correct SAM line of business.

#### lob
Within SAM their are 
