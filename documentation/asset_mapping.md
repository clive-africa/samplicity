# Asset Mapping
The assets inputs are detailed in the input files:

* *asset_inputs:* Which provides all the detail on the different asset inputs.
* *asset_mapping:* Whcih maps the different *asset_types* to the different asset shcoks.

This document details the different values that are accepted for the two files.

## Asset Shocks 
As noted previously, different asset types must be mapped to shocks. This is done in the asset_mapping files. The shocks are used by the package to calculate market risk. The following asset shocks are acceptable and used by the package:

* equity_global
* equity_sa
* equity_infrastructure
* equity_other
* property
* currency
* spread_credit
* concentration
* concentration_bank
* concentration_government
* default_type_1
* default_type_2
* default_type_2_overdue
* default_type_3
* spread_interest
* spread_interest_infastructure
* Interest_rate

## LGD Adjustments (lgd_adj)
The values that can be used for the different LGD adjustments:
* cash_covered
* over_collateralised
* fully_collateralised
* partially_collateralised
* unsecured
* less_50_collateral
* more_50_collateral
* sub_ordinated

## Bond Type (bond_type)
* fixed
* floating_3_0

## LGD Classification 
* cash_covered
* over_collateralised
* fully_collateralised
* partially_collateralised
* unsecured
* less_50_collateral
* more_50_collateral
* sub_ordinated


[Go Home](https://bitbucket.org/omi-it/samplicity/src/main/documentation/main.md)
