from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
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
REPORTS_DIRECTORY = PROJECT_ROOT / "reports"


@dataclass
class ImportSummary:
    total_records: int
    inserted_records: int
    existing_records: int
    duplicate_records: int
    invalid_records: int
    report_path: Path


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


def source_key_as_dict(
    source_key: tuple[str, str, str],
) -> dict[str, str]:
    return {
        "account_number": source_key[0],
        "statement_period": source_key[1],
        "reference_number": source_key[2],
    }


def format_validation_errors(
    error: ValidationError,
) -> list[dict[str, str]]:
    formatted_errors: list[dict[str, str]] = []

    for validation_error in error.errors(
        include_url=False,
    ):
        field = ".".join(
            str(part)
            for part in validation_error["loc"]
        )

        formatted_errors.append(
            {
                "field": field,
                "message": validation_error["msg"],
                "error_type": validation_error["type"],
            }
        )

    return formatted_errors


def print_validation_error(
    record_number: int,
    raw_record: dict[str, Any],
    errors: list[dict[str, str]],
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

    for error in errors:
        print(
            f"  - {error['field']}: "
            f"{error['message']}"
        )


def create_default_report_path() -> Path:
    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    return (
        REPORTS_DIRECTORY
        / f"rejected_records_{timestamp}.json"
    )


def write_rejection_report(
    report_path: Path,
    source_file: Path,
    summary: ImportSummary,
    rejected_records: list[dict[str, Any]],
) -> None:
    report_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    report = {
        "generated_at": datetime.now().isoformat(
            timespec="seconds"
        ),
        "source_file": str(source_file),
        "summary": {
            "total_records": summary.total_records,
            "inserted_records": summary.inserted_records,
            "already_in_database": summary.existing_records,
            "source_duplicates": summary.duplicate_records,
            "invalid_records": summary.invalid_records,
            "records_in_report": len(rejected_records),
        },
        "rejected_records": rejected_records,
    }

    with report_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2,
        )


def import_transactions(
    file_path: Path,
    report_path: Path,
) -> ImportSummary:
    raw_records = load_json_file(file_path)

    inserted_records = 0
    existing_records = 0
    duplicate_records = 0
    invalid_records = 0

    rejected_records: list[dict[str, Any]] = []

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

        # Tracks valid keys seen during this particular JSON import.
        seen_file_keys: set[
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

                formatted_errors = (
                    format_validation_errors(error)
                )

                print_validation_error(
                    record_number,
                    raw_record,
                    formatted_errors,
                )

                rejected_records.append(
                    {
                        "record_number": record_number,
                        "status": "invalid",
                        "reason": (
                            "Record failed data validation."
                        ),
                        "errors": formatted_errors,
                        "record": raw_record,
                    }
                )

                continue

            source_key = make_source_key(
                validated_record
            )

            # Check source-file duplicates before checking the DB.
            # This means the two duplicates remain visible even
            # when the importer is run multiple times.
            if source_key in seen_file_keys:
                duplicate_records += 1

                rejected_records.append(
                    {
                        "record_number": record_number,
                        "status": "duplicate",
                        "reason": (
                            "A record with the same source key "
                            "appeared earlier in the JSON file."
                        ),
                        "source_key": source_key_as_dict(
                            source_key
                        ),
                        "record": raw_record,
                    }
                )

                continue

            seen_file_keys.add(source_key)

            if source_key in existing_keys:
                existing_records += 1
                continue

            transaction = Transaction(
                **validated_record.model_dump()
            )

            transactions_to_insert.append(
                transaction
            )

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

    summary = ImportSummary(
        total_records=len(raw_records),
        inserted_records=inserted_records,
        existing_records=existing_records,
        duplicate_records=duplicate_records,
        invalid_records=invalid_records,
        report_path=report_path,
    )

    write_rejection_report(
        report_path=report_path,
        source_file=file_path,
        summary=summary,
        rejected_records=rejected_records,
    )

    return summary


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

    parser.add_argument(
        "--report-file",
        type=Path,
        default=None,
        help=(
            "Optional output path for the rejected "
            "records report."
        ),
    )

    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()

    report_path = (
        arguments.report_file
        if arguments.report_file is not None
        else create_default_report_path()
    )

    try:
        summary = import_transactions(
            file_path=arguments.file,
            report_path=report_path,
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
        f"Total records:       "
        f"{summary.total_records}"
    )
    print(
        f"Inserted records:    "
        f"{summary.inserted_records}"
    )
    print(
        f"Already in database: "
        f"{summary.existing_records}"
    )
    print(
        f"Source duplicates:   "
        f"{summary.duplicate_records}"
    )
    print(
        f"Invalid skipped:     "
        f"{summary.invalid_records}"
    )
    print(
        f"Rejected report:     "
        f"{summary.report_path}"
    )


if __name__ == "__main__":
    main()