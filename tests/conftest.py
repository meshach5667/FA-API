import re
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db import database as database_mod
from app.db.database import Base, get_db
from app.api.deps import (
    get_current_user,
    get_current_admin,
    get_current_business,
    get_current_super_admin,
)


# Use an in-memory SQLite database for tests
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def prepare_database():
    # Create tables once per test session
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Simple dummy objects for auth dependencies
class DummyUser:
    def __init__(self, email="test@user.com", is_active=True):
        self.email = email
        self.is_active = is_active


class DummyAdmin(DummyUser):
    pass


class DummyBusiness(DummyUser):
    pass


def override_current_user():
    return DummyUser()


def override_current_admin():
    return DummyAdmin()


def override_current_business():
    return DummyBusiness()


def override_current_super_admin():
    return DummyAdmin()


# Apply dependency overrides on the FastAPI app so endpoints that require auth or DB work
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[database_mod.get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_current_user
app.dependency_overrides[get_current_admin] = override_current_admin
app.dependency_overrides[get_current_business] = override_current_business
app.dependency_overrides[get_current_super_admin] = override_current_super_admin


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c
