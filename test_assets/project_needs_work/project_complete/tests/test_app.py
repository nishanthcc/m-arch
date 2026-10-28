"""
Unit & Integration Test Suite for User Management Gateway
Verifies endpoints, error handling, parameter validation, and boundary conditions.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from src.app import app

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_get_user_success():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/users/usr_001")
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "jane_dev"
        assert data["role"] == "admin"

@pytest.mark.asyncio
async def test_get_user_not_found():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/users/usr_nonexistent")
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_safe_calculate_divide_by_zero():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {"operand_a": 10.0, "operand_b": 0.0, "operation": "divide"}
        response = await client.post("/api/v1/math/calculate", json=payload)
        assert response.status_code == 400
        assert "Division by zero" in response.json()["detail"]
