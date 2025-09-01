# reset_alembic.py
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("SQLALCHEMY_DATABASE_URL")

engine = create_engine(url)
with engine.begin() as conn:
    conn.execute(text("DROP TABLE IF EXISTS alembic_version;"))

print("✅ Dropped alembic_version table")
