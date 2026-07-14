from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Transaction
from app.schemas import TransactionCreate, TransactionUpdate


def get_transaction(
    database: Session,
    transaction_id: int,
) -> Transaction | None:
    return database.get(Transaction, transaction_id)


def get_transaction_by_source_key(
    database: Session,
    account_number: str,
    statement_period: str,
    reference_number: str,
) -> Transaction | None:
    statement = select(Transaction).where(
        Transaction.account_number == account_number,
        Transaction.statement_period == statement_period,
        Transaction.reference_number == reference_number,
    )

    return database.scalar(statement)


def create_transaction(
    database: Session,
    transaction_data: TransactionCreate,
) -> Transaction:
    transaction = Transaction(
        **transaction_data.model_dump()
    )

    database.add(transaction)
    database.commit()
    database.refresh(transaction)

    return transaction


def update_transaction(
    database: Session,
    transaction: Transaction,
    transaction_data: TransactionUpdate,
) -> Transaction:
    updated_values = transaction_data.model_dump()

    for field, value in updated_values.items():
        setattr(transaction, field, value)

    database.commit()
    database.refresh(transaction)

    return transaction