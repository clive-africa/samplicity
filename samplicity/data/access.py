import pyodbc
import pandas as pd
from datetime import datetime as dt
import sqlalchemy as sa 

conn = pyodbc.connect(r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=C:\git_hub\sam_scr\.input\input_database.accdb;')
conn_string=r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=C:\git_hub\sam_scr\.input\input_database.accdb;'
cursor = conn.cursor()
cursor.execute('select * from valuation')

# Rather frustratingly, we need sqlalchemy as well to access
# We should always try avodi access
conn_string = ( 
    r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
    r"DBQ=C:\git_hub\sam_scr\.input\input_database.accdb;"
    r"ExtendedAnsiSQL=1;" )

connection_url = sa.engine.URL.create(
    "access+pyodbc",
    query={"odbc_connect": conn_string}
)
engine = sa.create_engine(connection_url)

df=pd.DataFrame.from_dict({'valuation_id': [1], 'snapshot_date': [dt.now()], 'short_description': ['Test vlauation run'], 'user': ['chogarth'], 'date_modified': [dt.now()]})

df.to_sql(name='snapshot',con=engine, if_exists='append',index=False)
for row in cursor.fetchall():
    print (row)