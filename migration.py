# destructive_migration.py
import sqlalchemy as sa
from sqlalchemy import create_engine, MetaData, Table, Column
from sqlalchemy.dialects.postgresql import insert
from urllib.parse import quote_plus

# --- SQLite Source (truth) ---
SQLITE_URL = "sqlite:///fitaccess.db"
sqlite_engine = create_engine(SQLITE_URL)
sqlite_metadata = MetaData()
sqlite_metadata.reflect(bind=sqlite_engine)

# --- Supabase (Postgres) Target ---
password = quote_plus("Kels09037066684@$")
PG_URL = f"postgresql+psycopg2://postgres.ixvfzpvbpkdjlotwjelp:{password}@aws-1-eu-north-1.pooler.supabase.com:6543/postgres"
pg_engine = create_engine(PG_URL)
pg_metadata = MetaData()
pg_metadata.reflect(bind=pg_engine)

print("🔄 Starting DESTRUCTIVE migration...")

# --- Patch types (SQLite DATETIME -> Postgres TIMESTAMP) ---
type_map = {
    sa.DATETIME: sa.TIMESTAMP,
    sa.DateTime: sa.TIMESTAMP,
}

def patch_column_type(col):
    """Map SQLite types to Postgres-compatible types"""
    for src_type, target_type in type_map.items():
        if isinstance(col.type, src_type):
            return Column(col.name, target_type, primary_key=col.primary_key)
    return Column(col.name, col.type, primary_key=col.primary_key)


# --- Drop extra tables in Postgres ---
for table_name in list(pg_metadata.tables.keys()):
    if table_name not in sqlite_metadata.tables:
        print(f"⚠️ Dropping extra table in Postgres: {table_name}")
        pg_metadata.tables[table_name].drop(pg_engine, checkfirst=True)
        pg_metadata.remove(pg_metadata.tables[table_name])

# --- Sync each SQLite table into Postgres ---
for table_name, sqlite_table in sqlite_metadata.tables.items():
    if table_name in pg_metadata.tables:
        # Drop table completely for destructive sync
        print(f"⚠️ Dropping & recreating table: {table_name}")
        pg_metadata.tables[table_name].drop(pg_engine, checkfirst=True)
        pg_metadata.remove(pg_metadata.tables[table_name])

    # Recreate with patched column types
    pg_table = Table(
        table_name,
        pg_metadata,
        *(patch_column_type(c) for c in sqlite_table.columns),
    )
    pg_table.create(pg_engine)
    print(f"✅ Created table: {table_name}")


# --- Data migration with UPSERT ---
sqlite_conn = sqlite_engine.connect()
pg_conn = pg_engine.connect()

for table_name, sqlite_table in sqlite_metadata.tables.items():
    pg_table = pg_metadata.tables[table_name]

    rows = sqlite_conn.execute(sqlite_table.select()).fetchall()
    if not rows:
        continue

    for row in rows:
        row_dict = dict(row._mapping)

        stmt = insert(pg_table).values(**row_dict)
        if pg_table.primary_key:
            pk_cols = [c.name for c in pg_table.primary_key.columns]
            non_pk_cols = [k for k in row_dict if k not in pk_cols]

            if non_pk_cols:
                stmt = stmt.on_conflict_do_update(
                    index_elements=pk_cols,
                    set_={k: stmt.excluded[k] for k in non_pk_cols}
                )
            else:
                stmt = stmt.on_conflict_do_nothing(index_elements=pk_cols)

        pg_conn.execute(stmt)

    pg_conn.commit()
    print(f"📤 Migrated {len(rows)} rows into {table_name}")

sqlite_conn.close()
pg_conn.close()
print("🎉 DESTRUCTIVE Migration complete!")
