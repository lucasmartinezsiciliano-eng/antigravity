"""
Tests for leaderboard API endpoints.
"""

import pytest


@pytest.mark.asyncio
async def test_get_leaderboard_empty(client):
    """Test leaderboard endpoint with no data returns empty list."""
    response = await client.get("/api/v1/leaderboard?period=all_time")
    assert response.status_code == 200
    data = response.json()
    assert data == []


@pytest.mark.asyncio
async def test_get_leaderboard_with_period(client):
    """Test leaderboard accepts valid period values."""
    for period in ["week", "month", "all_time"]:
        response = await client.get(f"/api/v1/leaderboard?period={period}")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_leaderboard_invalid_period(client):
    """Test leaderboard rejects invalid period values."""
    response = await client.get("/api/v1/leaderboard?period=invalid")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_leaderboard_with_city_filter(client):
    """Test leaderboard with city filter."""
    response = await client.get("/api/v1/leaderboard?period=all_time&city_filter=Barcelona")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_leaderboard_with_pagination(client):
    """Test leaderboard pagination returns a list."""
    response = await client.get(
        "/api/v1/leaderboard?period=all_time&limit=10&offset=0"
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_barber_stats_not_found(client):
    """Test getting individual barber stats returns 404 when not in leaderboard."""
    response = await client.get("/api/v1/leaderboard/stats/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_leaderboard_ranking_order(client, sample_leaderboard_stats):  # noqa: ARG001
    """Test that leaderboard returns entries sorted by ranking position."""
    response = await client.get("/api/v1/leaderboard?period=all_time")
    assert response.status_code == 200
    data = response.json()

    if data:
        ranks = [e.get("rank") for e in data]
        assert ranks == sorted(ranks)
