import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")

engine = create_engine(DATABASE_URL, echo=True)

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT NOW();"))
        for row in result:
            print("Current database time:", row[0])
except Exception as e:
    print("Connection failed:", e)
finally:
    engine.dispose()
