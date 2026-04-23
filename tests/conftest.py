import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client():
    """TestClient avec DB mockée — aucune connexion réelle requise."""
    with patch("sqlalchemy.schema.MetaData.create_all"):
        from backend.api.main import app
        from backend.infrastructure.database import get_db

        def override_get_db():
            yield MagicMock()

        app.dependency_overrides[get_db] = override_get_db
        yield TestClient(app)
        app.dependency_overrides.clear()
