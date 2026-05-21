"""
Tests for parental consent API endpoints.
"""

import pytest
from datetime import datetime, timezone, timedelta


@pytest.mark.asyncio
async def test_request_parental_consent(client):
    """Test requesting parental consent for minor."""
    response = await client.post(
        "/api/v1/parental-consent/request",
        json={
            "analysis_id": "analysis-001",
            "child_age": 14,
            "parent_email": "parent@example.com",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "authorization_url" in data
    assert "request_id" in data
    assert "token_expires_at" in data


@pytest.mark.asyncio
async def test_request_parental_consent_adult(client):
    """Test that adult age skips consent requirement."""
    response = await client.post(
        "/api/v1/parental-consent/request",
        json={
            "analysis_id": "analysis-002",
            "child_age": 25,
            "parent_email": "parent@example.com",
        },
    )
    # Should succeed but might indicate no consent needed
    assert response.status_code in [200, 201]


@pytest.mark.asyncio
async def test_request_parental_consent_invalid_email(client):
    """Test that invalid email is rejected."""
    response = await client.post(
        "/api/v1/parental-consent/request",
        json={
            "analysis_id": "analysis-003",
            "child_age": 14,
            "parent_email": "not-an-email",
        },
    )
    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_authorize_parental_consent_invalid_token(client):
    """Test authorizing with invalid token."""
    response = await client.get(
        "/api/v1/parental-consent/authorize?token=invalid-token"
    )
    # Should fail because token doesn't exist
    assert response.status_code in [400, 404]


@pytest.mark.asyncio
async def test_get_parental_consent_status(client):
    """Test checking parental consent status."""
    response = await client.get(
        "/api/v1/parental-consent/invalid-token/status"
    )
    # Should return 404 for non-existent token
    assert response.status_code in [400, 404]


@pytest.mark.asyncio
async def test_parental_consent_token_format(client):
    """Test that consent tokens are properly formatted."""
    response = await client.post(
        "/api/v1/parental-consent/request",
        json={
            "analysis_id": "analysis-004",
            "child_age": 12,
            "parent_email": "parent@example.com",
        },
    )
    assert response.status_code == 201
    data = response.json()

    # Token should be in the authorization URL
    assert "token=" in data.get("authorization_url", "")


@pytest.mark.asyncio
async def test_parental_consent_expiry(client):
    """Test that consent tokens expire after 72 hours."""
    response = await client.post(
        "/api/v1/parental-consent/request",
        json={
            "analysis_id": "analysis-005",
            "child_age": 15,
            "parent_email": "parent@example.com",
        },
    )
    assert response.status_code == 201
    data = response.json()

    # Token expires_at should be ~72 hours from now
    expires_at = datetime.fromisoformat(data["token_expires_at"].replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    delta = expires_at - now

    # Should be approximately 72 hours (allow 1 hour margin for test execution)
    assert 71 * 3600 <= delta.total_seconds() <= 73 * 3600
