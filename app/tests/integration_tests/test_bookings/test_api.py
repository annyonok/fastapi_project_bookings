import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    "room_id, date_from, date_to, status_code",
    [
        *[(4, "2030-05-01", "2030-05-15", 200)] * 8,
        # (4, "2030-05-01", "2030-05-15", 409),
        # (4, "2030-05-01", "2030-05-15", 409),
    ],
)
def test_add_and_get_booking(room_id, date_from, date_to, status_code, authenticated_client: TestClient):
    response = authenticated_client.post(
        "/bookings",
        params={
            "room_id": room_id,
            "date_from": date_from,
            "date_to": date_to,
        },
    )

    assert response.status_code == status_code
