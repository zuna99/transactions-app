from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.database import SessionLocal
from app.models import Transaction
from app.schemas import TransactionCreate


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON_PATH = PROJECT_ROOT / "data" / "sample.json"


@dataclass
class ImportSummary:
    total_records: int
    inserted_records: int
    duplicate_records: int
    invalid_records: int


def load_json_file(file_path: Path) -> list[dict[str, Any]]:
    if not file_path.exists():
        raise FileNotFoundError(
            f"JSON file was not found: {file_path}"
        )

    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            "The JSON root must be a list of transaction records."
        )

    if not all(isinstance(record, dict) for record in data):
        raise ValueError(
            "Every item in the JSON list must be an object."
        )

    return data


def make_source_key(
    transaction: TransactionCreate,
) -> tuple[str, str, str]:
    return (
        transaction.account_number,
        transaction.statement_period,
        transaction.reference_number,
    )


def print_validation_error(
    record_number: int,
    raw_record: dict[str, Any],
    error: ValidationError,
) -> None:
    account_number = raw_record.get(
        "account_number",
        "unknown",
    )
    reference_number = raw_record.get(
        "reference_number",
        "unknown",
    )

    print(
        f"\nInvalid record #{record_number} "
        f"({account_number}, {reference_number}):"
    )

    for validation_error in error.errors(
        include_url=False,
    ):
        location = ".".join(
            str(part)
            for part in validation_error["loc"]
        )

        print(
            f"  - {location}: "
            f"{validation_error['msg']}"
        )


def import_transactions(
    file_path: Path,
) -> ImportSummary:
    raw_records = load_json_file(file_path)

    inserted_records = 0
    duplicate_records = 0
    invalid_records = 0

    with SessionLocal() as database:
        existing_rows = database.execute(
            select(
                Transaction.account_number,
                Transaction.statement_period,
                Transaction.reference_number,
            )
        ).all()

        existing_keys = {
            tuple(row)
            for row in existing_rows
        }

        pending_keys: set[
            tuple[str, str, str]
        ] = set()

        transactions_to_insert: list[
            Transaction
        ] = []

        for record_number, raw_record in enumerate(
            raw_records,
            start=1,
        ):
            try:
                validated_record = (
                    TransactionCreate.model_validate(
                        raw_record
                    )
                )
            except ValidationError as error:
                invalid_records += 1

                print_validation_error(
                    record_number,
                    raw_record,
                    error,
                )

                continue

            source_key = make_source_key(
                validated_record
            )

            if (
                source_key in existing_keys
                or source_key in pending_keys
            ):
                duplicate_records += 1
                continue

            transaction = Transaction(
                **validated_record.model_dump()
            )

            transactions_to_insert.append(
                transaction
            )
            pending_keys.add(source_key)

        try:
            database.add_all(
                transactions_to_insert
            )
            database.commit()
        except SQLAlchemyError:
            database.rollback()
            raise

        inserted_records = len(
            transactions_to_insert
        )

    return ImportSummary(
        total_records=len(raw_records),
        inserted_records=inserted_records,
        duplicate_records=duplicate_records,
        invalid_records=invalid_records,
    )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Import transaction records "
            "from JSON into PostgreSQL."
        )
    )

    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_JSON_PATH,
        help=(
            "Path to the JSON file. "
            "Defaults to data/sample.json."
        ),
    )

    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()

    try:
        summary = import_transactions(
            arguments.file
        )
    except (
        FileNotFoundError,
        ValueError,
        json.JSONDecodeError,
    ) as error:
        print(f"Import failed: {error}")
        raise SystemExit(1) from error
    except SQLAlchemyError as error:
        print(
            "Import failed because of "
            f"a database error: {error}"
        )
        raise SystemExit(1) from error

    print("\nImport completed")
    print("----------------")
    print(
        f"Total records:      "
        f"{summary.total_records}"
    )
    print(
        f"Inserted records:   "
        f"{summary.inserted_records}"
    )
    print(
        f"Duplicates skipped: "
        f"{summary.duplicate_records}"
    )
    print(
        f"Invalid skipped:    "
        f"{summary.invalid_records}"
    )


if __name__ == "__main__":
    main()