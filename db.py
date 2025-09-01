import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")
SQLITE_URL = os.getenv("SQLITE_URL")

def create_engine_with_fallback():
    """Try connecting to Supabase first; fallback to SQLite if fails."""
    try:
        engine = create_engine(SUPABASE_URL, echo=True, future=True)
        # test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
        print("Connected to Supabase successfully!")
        return engine
    except Exception as e:
        print("Supabase connection failed:", e)
        print("Falling back to local SQLite database...")
        engine = create_engine(SQLITE_URL, echo=True, future=True)
        return engine

# Create engine and session
engine = create_engine_with_fallback()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Helper function to test connection
def test_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT NOW();") if "postgres" in str(engine.url) else text("SELECT 1;"))
            print("DB test result:", result.scalar())
    except Exception as e:
        print("Connection test failed:", e)

if __name__ == "__main__":
    test_connection()
