from typing import Any

import pytest
from pydantic import ValidationError

from app.schemas import TransactionCreate


def valid_record(
    **overrides: Any,
) -> dict[str, Any]:
    record = {
        "account_number": "BA-1001",
        "statement_period": "2026-01",
        "transaction_date": "2026-01-12",
        "booking_date": "2026-01-13",
        "reference_number": "TXN-001",
        "transaction_type": "invoice_payment",
        "amount": 100.50,
        "currency": "EUR",
        "counterparty_name": "Test Company",
        "category": "Software",
    }

    record.update(overrides)
    return record


def test_schema_normalizes_text_values() -> None:
    transaction = TransactionCreate.model_validate(
        valid_record(
            currency="eur",
            category=" Software ",
        )
    )

    assert transaction.currency == "EUR"
    assert transaction.category == "Software"


def test_schema_rejects_invalid_amount() -> None:
    with pytest.raises(ValidationError):
        TransactionCreate.model_validate(
            valid_record(amount="not_available")
        )