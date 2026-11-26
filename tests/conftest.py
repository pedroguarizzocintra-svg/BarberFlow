import pytest
from src import create_app
from src.db import init_db
from src.auth import create_user

@pytest.fixture
def app(tmp_path):
    app = create_app({"TESTING": True, "SECRET_KEY":"test-only-key",
                      "DATABASE":str(tmp_path / "test.sqlite3")})
    with app.app_context():
        init_db()
        create_user("Admin","admin@example.test","test-password-123","admin")
        create_user("Barber","barber@example.test","test-password-123","barber")
    return app

@pytest.fixture
def client(app):
    return app.test_client()
