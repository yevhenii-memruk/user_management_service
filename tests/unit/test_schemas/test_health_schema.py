from src.schemas.health import HealthCheckResponse
from src.schemas.root import RootResponse


class TestHealthCheckResponse:
    def test_health_check_response(self) -> None:
        data = {"message": "Service is healthy"}
        response = HealthCheckResponse(**data)
        assert response.message == data["message"]


class TestRootResponse:
    def test_root_response(self) -> None:
        data = {
            "message": "Welcome to API",
            "docs": "/docs",
            "redoc": "/redoc",
        }
        response = RootResponse(**data)
        assert response.message == data["message"]
        assert response.docs == data["docs"]
        assert response.redoc == data["redoc"]
