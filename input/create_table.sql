-- These statemetns create the valuation table as well as all the required audit trails and triggers.

CREATE TABLE valuation (
	id INTEGER PRIMARY KEY AUTOINCREMENT, 
	valuation_date DATETIME NOT NULL check(valuation_date=date(valuation_date,'start of month','+1 month','-1 day') and  date(valuation_date,'start of month','+1 month','-1 day') is not null), 
	entity TEXT NOT NULL, 
	short_description TEXT NOT NULL, 
	tax_rate REAL NOT NULL, 
	max_lacdt REAL NOT NULL, 
	level1_name TEXT NOT NULL, 
	level2_name TEXT NOT NULL, 
	level3_name TEXT NOT NULL, 
	user TEXT NOT NULL, 
	date_modified DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
	unique(valuation_date, entity, short_description)
);


-- These statemetns create the division table as well as all the required audit trails and triggers.

CREATE TABLE division1 (
	id INTEGER PRIMARY KEY AUTOINCREMENT, 
	valuation_id INTEGER NOT NULL,  
	division_name TEXT NOT NULL, 
	max_lacdt REAL NOT NULL, 
	tax_percent REAL NOT NULL, 
	scr_cover_ratio REAL NOT NULL, 
	user TEXT NOT NULL, 
	date_modified DATETIME NOT NULL,
	unique(valuation_id, division_name),
	CONSTRAINT fk_valuation_id FOREIGN KEY (valuation_id) REFERENCES valuation (id)
);

CREATE TABLE division2 (
	id INTEGER PRIMARY KEY AUTOINCREMENT, 
	valuation_id INTEGER NOT NULL, 
	division_name TEXT NOT NULL, 
	max_lacdt REAL NOT NULL, 
	tax_percent REAL NOT NULL, 
	scr_cover_ratio REAL NOT NULL, 
	user TEXT NOT NULL, 
	date_modified DATETIME NOT NULL,
	unique(valuation_id, division_name),
	CONSTRAINT fk_valuation_id FOREIGN KEY (valuation_id) REFERENCES valuation (id)
);


CREATE TABLE division3 (
	id INTEGER PRIMARY KEY AUTOINCREMENT, 
	valuation_id INTEGER NOT NULL, 
	division_name TEXT NOT NULL, 
	max_lacdt REAL NOT NULL, 
	tax_percent REAL NOT NULL, 
	scr_cover_ratio REAL NOT NULL, 
	user TEXT NOT NULL, 
	date_modified DATETIME NOT NULL,
	unique(valuation_id, division_name),
	CONSTRAINT fk_valuation_id FOREIGN KEY (valuation_id) REFERENCES valuation (id)
);


CREATE TABLE counterparty (
	id INTEGER PRIMARY KEY AUTOINCREMENT, 
	valuation_id INTEGER NOT NULL, 
	counterparty_name TEXT NOT NULL, 
	counterparty_cqs INTEGER NOT NULL check(counterparty_cqs>= 0 and counterparty_cqs<= 19), 
	counterparty_equivalent TEXT NOT NULL check(counterparty_equivalent in('Y','N')), 
	counterparty_group_id INTEGER NOT NULL, 
	counterparty_group_cqs INTEGER check(counterparty_cqs>= 0 and counterparty_cqs<= 19), 
	collateral REAL NOT NULL default 0 CHECK(collateral>=0), 
	user TEXT NOT NULL, 
	date_modified DATETIME NOT NULL,
	unique(valuation_id, counterparty_name),
	CONSTRAINT fk_valuation_id FOREIGN KEY (valuation_id) REFERENCES valuation (id),
	CONSTRAINT fk_counterparty_group_id FOREIGN KEY (counterparty_group_id) REFERENCES counterparty (id)
);

CREATE TRIGGER before_insert_counterparty
BEFORE INSERT ON counterparty
FOR EACH ROW
BEGIN
   SELECT RAISE(ABORT, 'The counterparty group is not mapped to the valuation.')
   WHERE (
       SELECT valuation_id FROM counterparty WHERE id = NEW.group_id
   ) !=  NEW.valuation_id;
END;


CREATE TABLE mapping (
	id INTEGER PRIMARY KEY AUTOINCREMENT, 
	valuation_id INTEGER NOT NULL, 
	asset_type TEXT NOT NULL, 
	user TEXT NOT NULL, 
	date_modified DATETIME NOT NULL,
	unique(asset_type),
	CONSTRAINT fk_valuation_id FOREIGN KEY (valuation_id) REFERENCES valuation (id)
);

CREATE TABLE mapping_shock (
	id INTEGER PRIMARY KEY AUTOINCREMENT, 
	valuation_id INTEGER NOT NULL, 
	mapping_id INTEGER NOT NULL, 
	shock TEXT NOT NULL, 
	user TEXT NOT NULL, 
	date_modified DATETIME NOT NULL,
	unique(valuation_id,mapping_id,shock),
	CONSTRAINT fk_valuation_id FOREIGN KEY (valuation_id) REFERENCES valuation (id),
	CONSTRAINT fk_mapping_id FOREIGN KEY (mapping_id) REFERENCES mapping (id)
);

CREATE TRIGGER before_insert_mapping_shock
BEFORE INSERT ON mapping_shock
BEGIN
   SELECT RAISE(ABORT, 'The mapping shock is not mapped to the valuation.')
   WHERE (
       SELECT valuation_id FROM mapping WHERE id = NEW.mapping_id
   ) !=  NEW.valuation_id;
END;

CREATE TABLE asset (
	id INTEGER PRIMARY KEY AUTOINCREMENT, 
	valuation_id INTEGER NOT NULL, 
	asset_short_description TEXT NOT NULL, 
	asset_description TEXT NOT NULL, 
	common_asset_pool TEXT check(common_asset_pool IN ('Y', 'N'), 
	division1_id INTEGER NOT NULL, 
	division2_id INTEGER NOT NULL, 
	division3_id INTEGER NOT NULL, 
	mapping_id INTEGER NOT NULL, 
	counterparty_id INTEGER NOT NULL, 
	asset_cqs INTEGER CHECK(asset_cqs>=0 AND asset_cqs<=19), 
	lgd_adj TEXT NOT NULL, 
	mod_duration REAL NOT NULL, 
	market_value REAL NOT NULL, 
	nominal_value REAL NOT NULL, 
	collateral REAL NOT NULL DEFAULT 0 check(collateral>=0), 
	maturity_date DATETIME NOT NULL, 
	coupon REAL NOT NULL, 
	spread REAL NOT NULL, 
	coupon_freq INTEGER NOT NULL check(coupon_freq>=0), 
	bond_type INTEGER NOT NULL, 
	equity_volatility_shock INTEGER NOT NULL, 
	spread_credit_up_shock INTEGER NOT NULL, 
	spread_credit_down_shock INTEGER NOT NULL, 
	user TEXT NOT NULL, 
	date_modified DATETIME NOT NULL,
	unique(valuation_id, asset_short_description),
	CONSTRAINT fk_valuation_id FOREIGN KEY (valuation_id) REFERENCES valuation (id),
	CONSTRAINT fk_counterparty_id FOREIGN KEY (counterparty_id) REFERENCES counterparty (id),
	CONSTRAINT fk_mapping_id FOREIGN KEY (mapping_id) REFERENCES mapping (id),
	CONSTRAINT fk_division1_id FOREIGN KEY (division1_id) REFERENCES division1 (id),
	CONSTRAINT fk_division2_id FOREIGN KEY (division2_id) REFERENCES division2 (id),
	CONSTRAINT fk_division3_id FOREIGN KEY (division3_id) REFERENCES division3 (id)
);

CREATE TRIGGER before_insert_asset_mapping_id
BEFORE INSERT ON asset
BEGIN
   SELECT RAISE(ABORT, 'The asset mapping is not mapped to the valuation.')
   WHERE (
       SELECT valuation_id FROM mapping WHERE id = NEW.mapping_id
   ) !=  NEW.valuation_id;
END;


CREATE TRIGGER before_insert_asset_counteprarty_id
BEFORE INSERT ON asset
BEGIN
   SELECT RAISE(ABORT, 'The counterparty is not mapped to the valuation.')
   WHERE (
       SELECT valuation_id FROM counterparty WHERE id = NEW.counterparty_id
   ) !=  NEW.valuation_id;
END;

CREATE TRIGGER before_insert_asset_divsion1_id
BEFORE INSERT ON asset
BEGIN
   SELECT RAISE(ABORT, 'The division (division1_id) is not mapped to the valuation.')
   WHERE (
       SELECT valuation_id FROM division1 WHERE id = NEW.divsion1_id
   ) !=  NEW.valuation_id;
END;

CREATE TRIGGER before_insert_asset_divsion2_id
BEFORE INSERT ON asset
BEGIN
   SELECT RAISE(ABORT, 'The division (division2_id) is not mapped to the valuation.')
   WHERE (
       SELECT valuation_id FROM division2 WHERE id = NEW.divsion2_id
   ) !=  NEW.valuation_id;
END;

CREATE TRIGGER before_insert_asset_divsion3_id
BEFORE INSERT ON asset
BEGIN
   SELECT RAISE(ABORT, 'The division (division3_id) is not mapped to the valuation.')
   WHERE (
       SELECT valuation_id FROM division3 WHERE id = NEW.divsion3_id
   ) !=  NEW.valuation_id;
END;


CREATE TABLE structure (
	id INTEGER PRIMARY KEY AUTOINCREMENT, 
	valuation_id INTEGER NOT NULL, 
	structure_name TEXT NOT NULL, 
	user TEXT NOT NULL, 
	date_modified DATETIME NOT NULL,
	unique(valuation_id, structure_name),
	CONSTRAINT fk_valuation_id FOREIGN KEY (valuation_id) REFERENCES valuation (id)
);

CREATE TABLE reinsurance (
	id INTEGER PRIMARY KEY AUTOINCREMENT, 
	valuation_id INTEGER NOT NULL, 
	contract_name TEXT NOT NULL, 
	contract_type TEXT NOT NULL check (contract_type in ('PROP','XOL')), 
	ri_share REAL NOT NULL check (ri_share>=0 and ri_share<=1), 
	excess REAL, 
	layer_size REAL NOT NULL check (layer_size>=0), 
	reinstate_count INTEGER check (reinstate_count>=0),
	reinstate_rate REAL check (reinstate_rate>=0), 
	user TEXT NOT NULL, 
	date_modified DATETIME NOT NULL,
	unique(valuation_id, contract_name),
	constraint chk_reinsurance_reinstate check((contract_type='XOL' and reinstate_count is not null and reinstate_rate is not null) or (contract_type='PROP' and reinstate_count is null and reinstate_rate is null)),
	constraint chk_reinsurance_excess check((contract_type='XOL' and excess is not null) or (contract_type='PROP' and excess is null)),
	CONSTRAINT fk_valuation_id FOREIGN KEY (valuation_id) REFERENCES valuation (id)
);
  
CREATE TABLE structure_reinsurance (
	id INTEGER PRIMARY KEY AUTOINCREMENT, 
	valuation_id INTEGER NOT NULL, 
	structure_id INTEGER NOT NULL, 
	reinsurance_id INTEGER NOT NULL, 
	reinsurance_order INTEGER NOT NULL check(reinsurance_order>0), 
	user TEXT NOT NULL, 
	date_modified DATETIME NOT NULL,
	unique(valuation_id, structure_id, reinsurance_id),
	CONSTRAINT fk_valuation_id FOREIGN KEY (valuation_id) REFERENCES valuation (id),
	CONSTRAINT fk_structure_id_valuation_id FOREIGN KEY (structure_id,valuation_id) REFERENCES structure (id, valuation_id),
	CONSTRAINT fk_reinsurance_id_valuation_id FOREIGN KEY (reinsurance_id,valuation_id) REFERENCES reinsurance (id,valuation_id)
);

CREATE TRIGGER before_insert_structure_reinsurance_structure_id
BEFORE INSERT ON structure_reinsurance
BEGIN
   SELECT RAISE(ABORT, 'The reinsurance structure is not mapped to the valuation.')
   WHERE (
       SELECT valuation_id FROM structure WHERE id = NEW.structure_id
   ) !=  NEW.valuation_id;
END;


CREATE TRIGGER before_insert_structure_reinsurance_reinsurance_id
BEFORE INSERT ON structure_reinsurance
BEGIN
   SELECT RAISE(ABORT, 'The reinsurance structure is not mapped to the valuation.')
   WHERE (
       SELECT valuation_id FROM reinsurance WHERE id = NEW.reinsurance_id
   ) !=  NEW.valuation_id;
END;

CREATE TABLE reinsurance_share (
	id INTEGER PRIMARY KEY AUTOINCREMENT, 
	valuation_id INTEGER NOT NULL, 
	reinsurance_id INTEGER NOT NULL, 
	counterparty_id INTEGER NOT NULL, 
	counterparty_share REAL NOT NULL check (counterparty_share>=0 and counterparty_share<=1), 
	user TEXT NOT NULL, 
	date_modified DATETIME NOT NULL,
	unique(valuation_id, reinsurance_id, counterparty_id),
	CONSTRAINT fk_valuation_id FOREIGN KEY (valuation_id) REFERENCES valuation (id),
	CONSTRAINT fk_reinsurance_id FOREIGN KEY (reinsurance_id) REFERENCES reinsurance (id),
	CONSTRAINT fk_counterparty_id FOREIGN KEY (counterparty_id) REFERENCES counterparty (id)
);

CREATE TRIGGER before_insert_reinsurance_share_reinsurance_id
BEFORE INSERT ON reinsurance_share
BEGIN
   SELECT RAISE(ABORT, 'The reinsurance agreement is not mapped to the valuation.')
   WHERE (
       SELECT valuation_id FROM reinsurance WHERE id = NEW.reinsurance_id
   ) !=  NEW.valuation_id;
END;

CREATE TRIGGER before_insert_reinsurance_share_counterparty_id
BEFORE INSERT ON reinsurance_share
BEGIN
   SELECT RAISE(ABORT, 'The counterparty is not mapped to the valuation.')
   WHERE (
       SELECT valuation_id FROM counterparty WHERE id = NEW.counterparty_id
   ) !=  NEW.valuation_id;
END;


CREATE TABLE prem_res (
	id INTEGER PRIMARY KEY AUTOINCREMENT, 
	valuation_id INTEGER NOT NULL, 
	prem_res_desc TEXT NOT NULL, 
	division1_id INTEGER NOT NULL, 
	division2_id INTEGER NOT NULL, 
	division3_id INTEGER NOT NULL, 
	lob_type TEXT NOT NULL check(lob_type in ('D', 'P', 'NP','O','FP','FNP', 'FO')), 
	lob text not null check (lob_type in ('1a', '1b', '2a', '2b', '3i', '3ii', '3iii','4i', '4ii','5i', '5ii','6i', '6ii','7i','7ii','8i','8ii','9','10i','10ii','10iii',
											'10iv','10v','10vi','10vii','11','12','13','14','15','16i','16ii','16iii','17i','17ii','17iii','17iv','18b','18c')),
	gross_p REAL NOT NULL, 
	gross_p_last REAL NOT NULL, 
	gross_p_last_24 REAL NOT NULL, 
	gross_fp_existing REAL NOT NULL, 
	gross_fp_future REAL NOT NULL, 
	gross_claim REAL NOT NULL, 
	gross_other REAL NOT NULL, 
	net_p REAL NOT NULL, 
	net_p_last REAL NOT NULL, 
	net_p_last_24 REAL NOT NULL, 
	net_fp_existing REAL NOT NULL, 
	net_fp_future REAL NOT NULL, 
	net_claim REAL NOT NULL, 
	net_other REAL NOT NULL, 
	include_factor_cat TEXT check(include_factor_cat in ('Y','N')), 
	include_non_prop_cat TEXT check(include_non_prop_cat in ('Y','N')), 
	reinsurance_id INTEGER, 
	structure_id INTEGER, 
	user TEXT NOT NULL, 
	date_modified DATETIME NOT NULL,
	UNIQUE(valuation_id, prem_res_desc),
	CONSTRAINT fk_structure_id_valuation_id FOREIGN KEY (structure_id) REFERENCES structure (id),
	CONSTRAINT fk_reinsurance_id_valuation_id FOREIGN KEY (reinsurance_id) REFERENCES reinsurance (id),
	CONSTRAINT fk_valuation_id FOREIGN KEY (valuation_id) REFERENCES valuation (id)
	
);

CREATE TRIGGER before_insert_prem_res_divsion1_id
BEFORE INSERT ON prem_res
BEGIN
   SELECT RAISE(ABORT, 'The division (division1_id) is not mapped to the valuation.')
   WHERE (
       SELECT valuation_id FROM division1 WHERE id = NEW.divsion1_id
   ) !=  NEW.valuation_id;
END;

CREATE TRIGGER before_insert_prem_res_divsion2_id
BEFORE INSERT ON prem_res
BEGIN
   SELECT RAISE(ABORT, 'The division (division2_id) is not mapped to the valuation.')
   WHERE (
       SELECT valuation_id FROM division2 WHERE id = NEW.divsion2_id
   ) !=  NEW.valuation_id;
END;

CREATE TRIGGER before_insert_prem_res_divsion3_id
BEFORE INSERT ON prem_res
BEGIN
   SELECT RAISE(ABORT, 'The division (division3_id) is not mapped to the valuation.')
   WHERE (
       SELECT valuation_id FROM division3 WHERE id = NEW.divsion3_id
   ) !=  NEW.valuation_id;
END;

CREATE TRIGGER before_insert_prem_res_structure_id
BEFORE INSERT ON prem_res
BEGIN
   SELECT RAISE(ABORT, 'The reinsurance structure is not mapped to the valuation.')
   WHERE (
       SELECT valuation_id FROM structure WHERE id = NEW.structure_id
   ) !=  NEW.valuation_id;
END;

CREATE TRIGGER before_insert_prem_res_reinsurance_id
BEFORE INSERT ON prem_res
BEGIN
   SELECT RAISE(ABORT, 'The reinsurance agreement is not mapped to the valuation.')
   WHERE (
       SELECT valuation_id FROM reinsurance WHERE id = NEW.reinsurance_id
   ) !=  NEW.valuation_id;
END;

CREATE TABLE nat_cat (
	id INTEGER PRIMARY KEY AUTOINCREMENT, 
	valuation_id INTEGER NOT NULL, 
	division1_id INTEGER NOT NULL, 
	division2_id INTEGER NOT NULL, 
	division3_id INTEGER NOT NULL, 
	structure_id INTEGER NOT NULL, 
	lob_type TEXT check(lob_type in ('D', 'P', 'NP','O','FP','FNP', 'FO')), 
	lob text check (lob_type in ('1a', '1b', '2a', '2b', '3i', '3ii', '3iii','4i', '4ii','5i', '5ii','6i', '6ii','7i','7ii','8i','8ii','9','10i','10ii','10iii',
								'10iv','10v','10vi','10vii','11','12','13','14','15','16i','16ii','16iii','17i','17ii','17iii','17iv','18b','18c')), 
	postal_code INTEGER NOT NULL check (postal_code>0 and postal_code<10000), 
	res_buildings REAL NOT NULL check(res_buildings>=0), 
	comm_buildings REAL NOT NULL check(comm_buildings>=0), 
	contents REAL NOT NULL check(contents>=0), 
	engineering REAL NOT NULL check(engineering>=0), 
	motor REAL NOT NULL check(motor>=0), 
	user TEXT NOT NULL, 
	date_modified DATETIME NOT NULL,
	CONSTRAINT fk_valuation_id FOREIGN KEY (valuation_id) REFERENCES valuation (id)
	);

CREATE TRIGGER before_insert_nat_cat_divsion1_id
BEFORE INSERT ON nat_cat
BEGIN
   SELECT RAISE(ABORT, 'The division (division1_id) is not mapped to the valuation.')
   WHERE (
       SELECT valuation_id FROM division1 WHERE id = NEW.divsion1_id
   ) !=  NEW.valuation_id;
END;

CREATE TRIGGER before_insert_nat_cat_divsion2_id
BEFORE INSERT ON nat_cat
BEGIN
   SELECT RAISE(ABORT, 'The division (division2_id) is not mapped to the valuation.')
   WHERE (
       SELECT valuation_id FROM division2 WHERE id = NEW.divsion2_id
   ) !=  NEW.valuation_id;
END;

CREATE TRIGGER before_insert_nat_cat_divsion3_id
BEFORE INSERT ON nat_cat
BEGIN
   SELECT RAISE(ABORT, 'The division (division3_id) is not mapped to the valuation.')
   WHERE (
       SELECT valuation_id FROM division3 WHERE id = NEW.divsion3_id
   ) !=  NEW.valuation_id;
END;

CREATE TRIGGER before_insert_nat_cat_structure_id
BEFORE INSERT ON nat_cat
BEGIN
   SELECT RAISE(ABORT, 'The reinsurance structure is not mapped to the valuation.')
   WHERE (
       SELECT valuation_id FROM structure WHERE id = NEW.structure_id
   ) !=  NEW.valuation_id;
END;


CREATE TABLE valuation_other_cat (
	id INTEGER PRIMARY KEY AUTOINCREMENT, 
	valuation_id INTEGER NOT NULL, 
	event_type TEXT NOT NULL, 
	event_gross_value REAL NOT NULL, 
	structure_id INTEGER NOT NULL, 
	user TEXT NOT NULL, 
	date_modified DATETIME NOT NULL,
	CONSTRAINT fk_valuation_id FOREIGN KEY (valuation_id) REFERENCES valuation (id),
	CONSTRAINT fk_structure_id_ FOREIGN KEY (structure_id) REFERENCES structure (id)
	
);

CREATE TRIGGER before_insert_valuation_other_cat_structure_id
BEFORE INSERT ON valuation_other_cat
BEGIN
   SELECT RAISE(ABORT, 'The reinsurance structure is not mapped to the valuation.')
   WHERE (
       SELECT valuation_id FROM structure WHERE id = NEW.structure_id
   ) !=  NEW.valuation_id;
END;

CREATE TABLE division_other_cat (
	id INTEGER PRIMARY KEY AUTOINCREMENT, 
	valuation_id INTEGER NOT NULL, 
	division1_id INTEGER, 
	division2_id INTEGER, 
	division3_id INTEGER, 
	event_type TEXT NOT NULL, 
	event_gross_value REAL NOT NULL, 
	structure_id INTEGER NOT NULL, 
	user TEXT NOT NULL, date_modified DATETIME NOT NULL);

CREATE TRIGGER before_insert_division_other_cat_divsion1_id
BEFORE INSERT ON division_other_cat
BEGIN
   SELECT RAISE(ABORT, 'The division (division1_id) is not mapped to the valuation.')
   WHERE (
       SELECT valuation_id FROM division1 WHERE id = NEW.divsion1_id
   ) !=  NEW.valuation_id;
END;

CREATE TRIGGER before_insert_division_other_cat_divsion2_id
BEFORE INSERT ON division_other_cat
BEGIN
   SELECT RAISE(ABORT, 'The division (division2_id) is not mapped to the valuation.')
   WHERE (
       SELECT valuation_id FROM division2 WHERE id = NEW.divsion2_id
   ) !=  NEW.valuation_id;
END;

CREATE TRIGGER before_insert_division_other_cat_divsion3_id
BEFORE INSERT ON division_other_cat
BEGIN
   SELECT RAISE(ABORT, 'The division (division3_id) is not mapped to the valuation.')
   WHERE (
       SELECT valuation_id FROM division3 WHERE id = NEW.divsion3_id
   ) !=  NEW.valuation_id;
END;

CREATE TABLE result (
	id INTEGER PRIMARY KEY AUTOINCREMENT, 
	uuid TEXT NOT NULL, 
	valuation_id INTEGER NOT NULL, 
	run_description TEXT NOT NULL, 
	diversification_level TEXT NOT NULL, 
	calculation_level TEXT NOT NULL, 
	snapshot_id INTEGER NOT NULL, 
	risk_free TEXT NOT NULL, 
	symmetric_adjustment TEXT NOT NULL, 
	runtime DATETIME NOT NULL, 
	python_runtime DATETIME NOT NULL, 
	user TEXT NOT NULL, 
	date_modified DATETIME NOT NULL
);

CREATE TABLE result_detail (
	id INTEGER PRIMARY KEY AUTOINCREMENT, 
	result_id INTEGER NOT NULL, 
	entry_id TEXT NOT NULL, 
	result_type TEXT NOT NULL,
	result_value_number REAL NOT NULL, 
	result_value_string TEXT NOT NULL
);

CREATE TABLE setting_export (
	id INTEGER PRIMARY KEY AUTOINCREMENT, 
	table_name TEXT NOT NULL, 
	module TEXT NOT NULL, 
	data_type TEXT NOT NULL, 
	sub_data_type TEXT NOT NULL, 
	include_index TEXT NOT NULL, 
	transformation TEXT NOT NULL, 
	user TEXT NOT NULL, 
	date_modified DATETIME NOT NULL
);

CREATE TABLE setting_import (
	id INTEGER PRIMARY KEY AUTOINCREMENT, 
	python_variable TEXT NOT NULL, 
	sql_query TEXT NOT NULL, 
	transformation TEXT NOT NULL, 
	user TEXT NOT NULL, 
	date_modified DATETIME NOT NULL
);

CREATE TABLE snapshot (
	id INTEGER PRIMARY KEY AUTOINCREMENT, 
	valuation_id INTEGER NOT NULL, 
	snapshot_date DATETIME NOT NULL, 
	short_description TEXT NOT NULL, 
	user TEXT NOT NULL, 
	date_modified DATETIME NOT NULL
);











