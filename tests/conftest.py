import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import create_app
from db import Base, engine, SessionLocal
from models.employee import Employee
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(scope="session")
def test_engine():
    # Force SQLite test DB before anything else
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    test_engine = create_engine(os.environ["DATABASE_URL"], echo=False, future=True)
    SessionLocal.configure(bind=test_engine)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def SessionForTests(test_engine):
    return sessionmaker(bind=test_engine, autoflush=False, autocommit=False)


@pytest.fixture(scope="session")
def test_app(SessionForTests):
    app = create_app()
    app.config["TESTING"] = True
    app.config["JWT_SECRET_KEY"] = "test-secret-key"

    # Override global SessionLocal used by routes
    from db import SessionLocal
    SessionLocal.configure(bind=SessionForTests.kw["bind"])

    return app


@pytest.fixture
def db_session(SessionForTests):
    session = SessionForTests()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def test_client(test_app):
    return test_app.test_client()


@pytest.fixture
def admin_user(db_session):
    user = Employee(email="super_admin@test.com", is_admin=True)
    user.set_password("admin123")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def create_test_user():
    def _create_test_user(email="test@example.com", password="testpass", is_admin=False):
        session = SessionLocal()
        user = Employee(
            email=email,
            password_hash=generate_password_hash(password),
            is_admin=is_admin
        )
        session.add(user)
        session.commit()
        return user
    return _create_test_user


@pytest.fixture
def admin_token(test_app, admin_user):
    with test_app.app_context():
        token = create_access_token(
            identity=str(admin_user.id),
            additional_claims={"is_admin": True}
        )
        return token

@pytest.fixture
def make_token(test_client):
    def _make(user_id, is_admin=False):
        with test_client.application.app_context():
            return create_access_token(
                identity=str(user_id),
                additional_claims={"is_admin": is_admin}
            )
    return _make