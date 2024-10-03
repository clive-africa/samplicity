import pandas as pd


# Allows us to read and write data to a database
import pyodbc
import urllib
import sqlalchemy as sa
from tqdm import tqdm

import numpy as np

#from ..helper import log_decorator

#@log_decorator
def f_odbc_import(dat, conn_string, import_table, dict_param=None):
    #logger.debug("Function start")
    # We get a connection to the database, we will use the same connection for all our queries.
    sql_conn = pyodbc.connect(conn_string)

    # We provide a row count for the user to help with any potential rror checking
    df_val = dat.output["data_validation"]

    table_mapping = dat.f_odbc_table_import(sql_conn, import_table, dict_param)

    df_val.loc[len(df_val.index)] = [
        "import_row_count",
        None,
        "import_table",
        len(table_mapping),
    ]

    # Make sure that we can provide the data to the user for audit queries.
    dat.output["sql_mapping"] = table_mapping

    data = {}

    # Now we will loop through the table to attach our resources to our import data
    for row in table_mapping.iterrows():
        if row["transformation"] == None:
            data[row["python_variable"]] = self.f_odbc_table_import(
                row["sql_query"], None, sql_conn, dict_param
            )
        else:
            data[row["python_variable"]] = self.f_odbc_table_import(
                row["sql_query"], row["transformation"], sql_conn, dict_param
            )

        df_val.loc[len(df_val.index)] = [
            "import_row_count",
            None,
            row["python_variable"],
            len(data[row["python_variable"]]),
        ]

    self.output["data"] = data

    return True

#@log_decorator
def f_odbc_table_import(sql_conn, sql_query, dict_param=None):
    #logger.debug("Function start")

    for key, value in dict_param.items():
        sql_query = sql_query.replace(key, value)

    curs = sql_conn.cursor()
    curs.execute(sql_query)
    data_sql = pd.DataFrame.from_records(
        curs.fetchall(), columns=[col[0] for col in curs.description]
    )
    # data_sql = pd.read_sql_query(sql_query, sql_conn)

    return data_sql

#@log_decorator
def f_odbc_export(self, result_set, conn_string, export_id=None):
    """Export results using ODBC connection."""
    
    if '.accdb' in conn_string:
        conn_string = ( 
            r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
            r"DBQ="+conn_string+";"
            r"ExtendedAnsiSQL=1;" )

        # Rather frustratingly, we need sqlalchemy as well to access
        connection_url = sa.engine.URL.create(
            "access+pyodbc",
            query={"odbc_connect": conn_string}
        )
        engine = sa.create_engine(connection_url)
    else:
        engine = pyodbc.connect(conn_string)

    # First thing we need to get is create a datafrmae of all possible division combinations
    # We will populate this to a table with the export id
    res_combination=self.sam_scr.f_data('scr','list_combinations')

    # We need to get this into a normalised format of the type
    # run_id    combination_id      level       division_id
    res_combination.reset_index(inplace=True)
    # We store the mapping table seperately
    # Once we explode the ield, i won't exist
    mapper=res_combination.rename(columns={'index': 'combination_id'}, inplace=False)
    res_combination['level']=res_combination['combinations'].apply(lambda x: len(x))
    #res_combination['combination_identifier']=res_combination['combinations']
    res_combination=res_combination.explode('combinations')
    res_combination=res_combination.rename(columns={'index': 'combination_id','combinations': 'division_id'})
    res_combination['run_id']=export_id

    # We upload this data to our 'results_combination' table
    # Thsi takes foreever to run given the numbr of records we create here.
    insert_with_progress (engine, res_combination[['run_id','combination_id', 'level', 'division_id']], 'results_combination')
    #res_combination[['run_id','combination_id', 'level', 'division_id']].to_sql('results_combination', engine, index=False, if_exists='append', chunksize=10000)


    result_set=pd.DataFrame.from_dict({'metric': ['gross_scr','net_scr','net_prem_res','calc_net_prem_res'],
                                        'module': ['scr','scr','prem_res','prem_res'], 
                                       'data': ['scr','scr','net','calc_net'], 
                                       'sub_data': ['gross','net',None, None], 
                                       'transformation': ['merge','merge','merge','merge']})

    # We need to loop through all of our export data to input it into the database
    with tqdm(total=len(result_set)) as pbar:
        for row in result_set.iterrows():
            try:
                df_export = self.scr.f_data(row.module, row.data, row.sub_data)
                if row["transformation"] == "merge":
                    df_export=df_export.merge(mapper, left_on='index',right_on='combinations',how='left').drop(['combinations'], axis=1)
                    # Need to create an error here as well
                    if sum(df_export['combination_id'].isna())>0:
                        logger.critical("Errror")
                        df_export['combination_id'].fillna(-1, inplace=True)
                    #Transform our data
                    df_export=df_export.melt(id_vars=['combination_id'])
                    df_export[['run_id','metric']]=[export_id,row.metric]
                    #df_export['metric']=row['metric']
                    df_export.rename(columns={'variable': 'sub_metric', 'value': 'value_numeric'}, inplace=True)
                    df_export=df_export[['run_id','combination_id','metric','sub_metric', 'value_numeric']]
            except:
                df_export=pd.DataFrame(data=f'Error: {row["module"]} - {row["data"]} - {row["sub_data"]}',columns=['value_text'])
                df_export[['run_id','combination_id','metric','sub_metric', 'value_numeric']]=[export_id,-1,row['metric'],np.Nan,np.Nan]
                df_export=df_export[['run_id','combination_id','metric','sub_metric', 'value_text','value_numeric']]
            
            finally:
                insert_with_progress(engine, df_export, 'result_value')
                #df_export.to_sql('results_value', con=engine, if_exists="append", index=False)
        # Give the user a progress update on all the insert operations
        # Won't be overly accurate but better than nothing.
        pbar.update(1)
        tqdm._instances.clear()

    return True

def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))

def insert_with_progress(engine, df, table):
    
    chunksize = int(len(df) / 10)
    chunksize=max(100000,chunksize)
    if chunksize == 0:
        df.to_sql(name="result_value", con=engine, if_exists="append", index=False)
    else:
        with tqdm(total=len(df)) as pbar:
            for i, cdf in enumerate(chunker(df, chunksize)):
                #replace = "replace" if i == 0 else "append"
                cdf.to_sql(name=table, con=engine, if_exists='append', index=False) 
                pbar.update(chunksize)
                tqdm._instances.clear()


        