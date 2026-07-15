from typing import Any

from fastapi.testclient import TestClient


def transaction_payload(
    **overrides: Any,
) -> dict[str, Any]:
    payload = {
        "account_number": "BA-TEST-001",
        "statement_period": "2026-08",
        "transaction_date": "2026-08-10",
        "booking_date": "2026-08-11",
        "reference_number": "TEST-001",
        "transaction_type": "card_payment",
        "amount": -89.99,
        "currency": "usd",
        "counterparty_name": "Test Company",
        "category": "Software",
    }

    payload.update(overrides)
    return payload


def test_health_endpoints(
    client: TestClient,
) -> None:
    health_response = client.get("/health")
    database_response = client.get("/db-health")

    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok"}

    assert database_response.status_code == 200
    assert database_response.json() == {
        "status": "ok",
        "database": "connected",
    }


def test_create_transaction_normalizes_currency(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/transactions",
        json=transaction_payload(),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] > 0
    assert data["currency"] == "USD"
    assert data["amount"] == "-89.99"
    assert data["account_number"] == "BA-TEST-001"


def test_duplicate_transaction_returns_conflict(
    client: TestClient,
) -> None:
    payload = transaction_payload()

    first_response = client.post(
        "/api/transactions",
        json=payload,
    )
    second_response = client.post(
        "/api/transactions",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_list_transactions(
    client: TestClient,
) -> None:
    client.post(
        "/api/transactions",
        json=transaction_payload(),
    )

    response = client.get(
        "/api/transactions?limit=10"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["limit"] == 10
    assert len(data["items"]) == 1
    assert (
        data["items"][0]["account_number"]
        == "BA-TEST-001"
    )


def test_get_transaction(
    client: TestClient,
) -> None:
    create_response = client.post(
        "/api/transactions",
        json=transaction_payload(),
    )

    transaction_id = create_response.json()["id"]

    response = client.get(
        f"/api/transactions/{transaction_id}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == transaction_id


def test_update_transaction(
    client: TestClient,
) -> None:
    create_response = client.post(
        "/api/transactions",
        json=transaction_payload(),
    )

    transaction_id = create_response.json()["id"]

    updated_payload = transaction_payload(
        amount=250.75,
        currency="eur",
        counterparty_name="Updated Company",
        category="Cloud Services",
    )

    response = client.put(
        f"/api/transactions/{transaction_id}",
        json=updated_payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["amount"] == "250.75"
    assert data["currency"] == "EUR"
    assert data["counterparty_name"] == "Updated Company"
    assert data["category"] == "Cloud Services"


def test_missing_transaction_returns_not_found(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/transactions/99999"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Transaction was not found."
    )


def test_invalid_date_returns_validation_error(
    client: TestClient,
) -> None:
    payload = transaction_payload(
        transaction_date="2026-02-30"
    )

    response = client.post(
        "/api/transactions",
        json=payload,
    )

    assert response.status_code == 422

def test_list_transactions_sorted_by_id(
    client: TestClient,
) -> None:
    first_response = client.post(
        "/api/transactions",
        json=transaction_payload(
            reference_number="SORT-001",
        ),
    )

    second_response = client.post(
        "/api/transactions",
        json=transaction_payload(
            reference_number="SORT-002",
        ),
    )

    first_id = first_response.json()["id"]
    second_id = second_response.json()["id"]

    response = client.get(
        "/api/transactions"
        "?sort_by=id"
        "&sort_order=asc"
    )

    assert response.status_code == 200

    items = response.json()["items"]

    assert items[0]["id"] == first_id
    assert items[1]["id"] == second_id