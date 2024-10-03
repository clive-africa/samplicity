import sqlite3
import os

# Create a SQLite database
db_file = r"C:\git_hub\sam_flask\sam.sqlite"

# Delete the file if it exists
if os.path.exists(db_file):
    os.remove(db_file)

conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Import SQL file to create tables
with open(r"C:\git_hub\sam_flask\create_table.sql", "r") as sql_file:
    sql_script = sql_file.read()
    cursor.executescript(sql_script)

# Create audit log tables for each table generated
tables_query = "SELECT name, sql FROM sqlite_master WHERE type='table' and name not like 'sqlite_%';"
cursor.execute(tables_query)
tables = cursor.fetchall()

for table in tables:
    table_name = table[0]
    # table_schema = table[1]
    audit_table_name = f"hst_{table_name}"

    cursor.execute(f"DROP TABLE IF EXISTS {audit_table_name};")

    fld_data = cursor.execute(
        f"SELECT name, type FROM pragma_table_info('{table_name}');"
    ).fetchall()
    flds_string = "".join(
        [str(field[0]) + " " + str(field[1]) + ", " for field in fld_data]
    )
    cursor.execute(
        f"CREATE TABLE IF NOT EXISTS {audit_table_name} ({flds_string} hst_id INTEGER PRIMARY KEY AUTOINCREMENT, hst_start DATETIME, hst_end DATETIME);"
    )

    table_schema = ", ".join([str(field[0]) for field in fld_data])
    value_schema = ", ".join(["NEW." + str(field[0]) for field in fld_data])
    # Create triggers to populate audit table for insert, update, and delete operations
    trigger_query = f"""
    CREATE TRIGGER IF NOT EXISTS {table_name}_insert
    AFTER INSERT ON {table_name}
    FOR EACH ROW
    BEGIN
        INSERT INTO {audit_table_name} ({table_schema}, hst_start)
        VALUES ({value_schema}, CURRENT_TIMESTAMP);
    END;
    """
    cursor.execute(trigger_query)

    trigger_query = f"""
    CREATE TRIGGER IF NOT EXISTS {table_name}_update
    AFTER UPDATE ON {table_name}
    FOR EACH ROW
    BEGIN

        UPDATE {audit_table_name}
            SET hst_end = CURRENT_TIMESTAMP
            WHERE id = NEW.id
            AND hst_end IS NULL;

        INSERT INTO {audit_table_name} ({table_schema}, hst_start)
        VALUES ({value_schema}, CURRENT_TIMESTAMP);
    END;
    """
    cursor.execute(trigger_query)

    trigger_query = f"""
    CREATE TRIGGER IF NOT EXISTS {table_name}_delete
    AFTER DELETE ON {table_name}
    FOR EACH ROW
    BEGIN
        UPDATE {audit_table_name}
            SET hst_end = CURRENT_TIMESTAMP
            WHERE id = NEW.id
            AND hst_end IS NULL;
    END;
    """
    cursor.execute(trigger_query)

# Commit changes and close connection
conn.commit()
conn.close()

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.automap import automap_base

engine = create_engine(
    "sqlite:///C:/git_hub/sam_flask/sam.sqlite"
)  # Replace with your database URL
Base = automap_base()
Base.prepare(engine, reflect=True)
