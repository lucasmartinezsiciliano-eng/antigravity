"""
Tests for reference photo API endpoints.
"""

import pytest
from io import BytesIO


@pytest.mark.asyncio
async def test_get_reference_photos_empty(client, sample_barber):
    """Test getting reference photos for barber with none."""
    response = await client.get(f"/api/v1/barbers/{sample_barber.id}/reference-photos")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_get_reference_photos_with_filters(client, sample_barber):
    """Test filtering reference photos by haircut type and status."""
    response = await client.get(
        f"/api/v1/barbers/{sample_barber.id}/reference-photos"
        "?haircut_type=fade&validation_status=approved"
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_upload_reference_photo_missing_file(client, sample_barber):
    """Test upload without file fails."""
    response = await client.post(
        f"/api/v1/barbers/{sample_barber.id}/reference-photos",
        data={
            "haircut_type": "fade",
            "photo_angle": "frontal",
        },
    )
    # Should fail because file is required
    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_upload_reference_photo_invalid_format(client, sample_barber):
    """Test upload with non-image file fails."""
    # Create a fake text file
    response = await client.post(
        f"/api/v1/barbers/{sample_barber.id}/reference-photos",
        data={
            "haircut_type": "fade",
            "photo_angle": "frontal",
        },
        files={
            "file": ("test.txt", BytesIO(b"not an image"), "text/plain"),
        },
    )
    # Should fail because file is not an image
    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_delete_reference_photo_not_found(client, sample_barber):
    """Test deleting non-existent photo."""
    response = await client.delete(
        f"/api/v1/barbers/{sample_barber.id}/reference-photos/nonexistent"
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_reference_photo_validation_status(client, sample_barber):
    """Test that photos have proper validation status."""
    response = await client.get(
        f"/api/v1/barbers/{sample_barber.id}/reference-photos"
    )
    assert response.status_code == 200

    for photo in response.json():
        assert "validation_status" in photo
        assert photo["validation_status"] in ["pending", "approved", "rejected"]
