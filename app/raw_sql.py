from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def list_transactions_raw(
    database: Session,
    limit: int,
    offset: int,
    account_number: str | None = None,
    currency: str | None = None,
    transaction_type: str | None = None,
    category: str | None = None,
    search: str | None = None,
) -> tuple[list[dict[str, Any]], int]:
    conditions: list[str] = []
    parameters: dict[str, Any] = {}

    if account_number:
        conditions.append(
            "account_number = :account_number"
        )
        parameters["account_number"] = account_number

    if currency:
        conditions.append(
            "currency = :currency"
        )
        parameters["currency"] = currency.upper()

    if transaction_type:
        conditions.append(
            "transaction_type = :transaction_type"
        )
        parameters["transaction_type"] = (
            transaction_type.lower()
        )

    if category:
        conditions.append(
            "category = :category"
        )
        parameters["category"] = category

    if search:
        conditions.append(
            """
            (
                account_number ILIKE :search
                OR reference_number ILIKE :search
                OR counterparty_name ILIKE :search
                OR category ILIKE :search
            )
            """
        )
        parameters["search"] = f"%{search}%"

    where_clause = ""

    if conditions:
        where_clause = (
            "WHERE " + " AND ".join(conditions)
        )

    count_query = text(
        f"""
        SELECT COUNT(*)
        FROM transactions
        {where_clause}
        """
    )

    total = database.execute(
        count_query,
        parameters,
    ).scalar_one()

    list_parameters = {
        **parameters,
        "limit": limit,
        "offset": offset,
    }

    list_query = text(
        f"""
        SELECT
            id,
            account_number,
            statement_period,
            transaction_date,
            booking_date,
            reference_number,
            transaction_type,
            amount,
            currency,
            counterparty_name,
            category,
            created_at,
            updated_at
        FROM transactions
        {where_clause}
        ORDER BY transaction_date DESC, id DESC
        LIMIT :limit
        OFFSET :offset
        """
    )

    rows = database.execute(
        list_query,
        list_parameters,
    ).mappings().all()

    return (
        [dict(row) for row in rows],
        total,
    )