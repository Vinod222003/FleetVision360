import sqlite3
import getpass
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values

SQLITE_DB = r"data\warehouse\fleetvision360.db"

TABLES = [
    "dim_depot",
    "dim_vehicle",
    "dim_driver",
    "dim_route",
    "dim_customer",
    "dim_date",
    "fact_trip",
    "fact_delivery",
    "fact_fuel",
    "fact_maintenance",
    "fact_gps",
    "fact_vehicle_telemetry",
]

def sqlite_to_postgres_type(sqlite_type):
    t = (sqlite_type or "").upper()

    if "INT" in t:
        return "BIGINT"
    if "CHAR" in t or "CLOB" in t or "TEXT" in t:
        return "TEXT"
    if "REAL" in t or "FLOA" in t or "DOUB" in t:
        return "DOUBLE PRECISION"
    if "DECIMAL" in t or "NUMERIC" in t:
        return "NUMERIC"
    if "BOOL" in t:
        return "BOOLEAN"
    if "DATE" in t:
        return "DATE"
    if "TIME" in t:
        return "TIMESTAMP"
    if "BLOB" in t:
        return "BYTEA"

    return "TEXT"


print("=" * 60)
print("FleetVision360 - SQLite to PostgreSQL Migration")
print("=" * 60)

# Connect to SQLite
sqlite_conn = sqlite3.connect(SQLITE_DB)
sqlite_cur = sqlite_conn.cursor()

print("\nSQLite connection: OK")

# Ask for PostgreSQL password
password = getpass.getpass("Enter PostgreSQL password: ")

# Connect to PostgreSQL
pg_conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="fleetvision360",
    user="postgres",
    password=password
)

pg_cur = pg_conn.cursor()

print("PostgreSQL connection: OK")

# Safety check - do not overwrite existing tables
pg_cur.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
      AND table_name = ANY(%s)
""", (TABLES,))

existing_tables = [row[0] for row in pg_cur.fetchall()]

if existing_tables:
    print("\nSTOP: These PostgreSQL tables already exist:")
    for table in existing_tables:
        print("  -", table)
    print("\nNo data was changed.")
    pg_conn.close()
    sqlite_conn.close()
    raise SystemExit(1)

total_rows = 0

try:
    for table in TABLES:

        print("\n" + "-" * 50)
        print("Migrating:", table)

        # Read SQLite column information
        sqlite_cur.execute(f'PRAGMA table_info("{table}")')
        columns_info = sqlite_cur.fetchall()

        if not columns_info:
            raise Exception(f"SQLite table not found: {table}")

        column_names = [row[1] for row in columns_info]

        # Build PostgreSQL CREATE TABLE
        column_definitions = []

        primary_key_columns = []

        for row in columns_info:
            cid, name, sqlite_type, notnull, default_value, pk = row

            pg_type = sqlite_to_postgres_type(sqlite_type)

            definition = f'"{name}" {pg_type}'

            if notnull:
                definition += " NOT NULL"

            column_definitions.append(definition)

            if pk:
                primary_key_columns.append(name)

        if primary_key_columns:
            pk_sql = ", ".join(f'"{col}"' for col in primary_key_columns)
            column_definitions.append(f"PRIMARY KEY ({pk_sql})")

        create_sql = f'''
            CREATE TABLE "{table}" (
                {", ".join(column_definitions)}
            )
        '''

        pg_cur.execute(create_sql)

        # Read SQLite rows
        sqlite_cur.execute(f'SELECT * FROM "{table}"')
        rows = sqlite_cur.fetchall()

        # Insert into PostgreSQL
        if rows:
            pg_table = sql.Identifier(table).as_string(pg_conn)
            pg_columns = ", ".join(
                sql.Identifier(col).as_string(pg_conn)
                for col in column_names
            )

            insert_sql = (
                f'INSERT INTO {pg_table} ({pg_columns}) VALUES %s'
            )

            execute_values(
                pg_cur,
                insert_sql,
                rows,
                page_size=2000
            )

        # Verify count
        pg_cur.execute(
            sql.SQL('SELECT COUNT(*) FROM {}').format(
                sql.Identifier(table)
            )
        )

        pg_count = pg_cur.fetchone()[0]
        sqlite_count = len(rows)

        if pg_count != sqlite_count:
            raise Exception(
                f"Row count mismatch for {table}: "
                f"SQLite={sqlite_count}, PostgreSQL={pg_count}"
            )

        print(f"SQLite rows     : {sqlite_count}")
        print(f"PostgreSQL rows : {pg_count}")
        print("Status          : OK")

        total_rows += pg_count

    pg_conn.commit()

    print("\n" + "=" * 60)
    print("MIGRATION COMPLETED SUCCESSFULLY")
    print("=" * 60)
    print(f"Tables migrated : {len(TABLES)}")
    print(f"Total rows      : {total_rows}")
    print("=" * 60)

except Exception as e:
    pg_conn.rollback()

    print("\n" + "=" * 60)
    print("MIGRATION FAILED")
    print("=" * 60)
    print("Error:", e)
    print("PostgreSQL changes were rolled back.")
    print("=" * 60)

    raise

finally:
    pg_cur.close()
    pg_conn.close()
    sqlite_cur.close()
    sqlite_conn.close()
