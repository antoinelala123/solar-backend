import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client():
    """TestClient avec DB et dispatcher mockés — aucune connexion réelle requise."""
    with patch("sqlalchemy.schema.MetaData.create_all"):
        from backend.api.main import app
        from backend.infrastructure.database import get_db
        from backend.api.routes.projects import get_dispatcher

        def override_get_db():
            yield MagicMock()

        def override_get_dispatcher():
            return MagicMock()

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_dispatcher] = override_get_dispatcher
        yield TestClient(app)
        app.dependency_overrides.clear()
