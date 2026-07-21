import pytest
from app import create_app
from extensions import db as _db


@pytest.fixture
def app():
    """Flask application instance initialized with in-memory SQLite database."""
    test_config = {
        "TESTING": True,
        "SECRET_KEY": "test-secret-key-12345",
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    }
    app = create_app(test_config=test_config)

    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """Provides access to db session during testing."""
    with app.app_context():
        yield _db.session
