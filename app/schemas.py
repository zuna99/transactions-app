import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TransactionCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    account_number: str = Field(min_length=1, max_length=30)
    statement_period: str = Field(min_length=7, max_length=7)
    transaction_date: date
    booking_date: date
    reference_number: str = Field(min_length=1, max_length=50)
    transaction_type: str = Field(min_length=1, max_length=50)
    amount: Decimal = Field(max_digits=14, decimal_places=2)
    currency: str = Field(min_length=3, max_length=3)
    counterparty_name: str = Field(min_length=1, max_length=255)
    category: str = Field(min_length=1, max_length=100)

    @field_validator("statement_period")
    @classmethod
    def validate_statement_period(cls, value: str) -> str:
        if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", value):
            raise ValueError(
                "statement_period must use YYYY-MM format"
            )

        return value

    @field_validator(
        "transaction_date",
        "booking_date",
        mode="before",
    )
    @classmethod
    def validate_date(cls, value: object) -> date:
        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        if not isinstance(value, str):
            raise ValueError(
                "date must be a string in YYYY-MM-DD format"
            )

        try:
            return date.fromisoformat(value)
        except ValueError as error:
            raise ValueError(
                "date must be a valid YYYY-MM-DD date"
            ) from error

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, value: object) -> Decimal:
        if value is None or isinstance(value, bool):
            raise ValueError("amount must be a valid number")

        try:
            amount = Decimal(str(value))
        except (InvalidOperation, ValueError) as error:
            raise ValueError(
                "amount must be a valid number"
            ) from error

        if not amount.is_finite():
            raise ValueError("amount must be finite")

        return amount

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        normalized = value.upper()

        if not re.fullmatch(r"[A-Z]{3}", normalized):
            raise ValueError(
                "currency must contain exactly three letters"
            )

        return normalized

    @field_validator("transaction_type")
    @classmethod
    def normalize_transaction_type(cls, value: str) -> str:
        return value.lower()


class TransactionRead(TransactionCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime

class TransactionUpdate(TransactionCreate):
    pass


class TransactionListResponse(BaseModel):
    items: list[TransactionRead]
    total: int
    limit: int
    offset: int