import pytest
import mongomock

from app import create_app
from extensions import set_db, init_indexes


@pytest.fixture
def mock_db():
    """Create an in-memory mongomock database and override extensions.db."""
    client = mongomock.MongoClient()
    db = client["test_jwt_auth_db"]
    set_db(db)
    init_indexes()
    yield db
    # Reset after test
    set_db(None)


@pytest.fixture
def app(mock_db):
    """Flask application instance initialized with mock_db."""
    app = create_app()
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key-12345"
    return app


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()
