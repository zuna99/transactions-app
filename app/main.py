from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
    status,
)
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.raw_sql import list_transactions_raw
from app.schemas import (
    TransactionCreate,
    TransactionListResponse,
    TransactionRead,
    TransactionUpdate,
)

from pathlib import Path

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from typing import Literal


app = FastAPI(
    title="Business Transactions Application",
    description=(
        "Application for importing and managing "
        "business transactions."
    ),
    version="1.0.0",
)


BASE_DIR = Path(__file__).resolve().parent

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)

@app.get(
    "/",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/db-health")
def database_health_check(
    database: Session = Depends(get_db),
) -> dict[str, str]:
    database.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "database": "connected",
    }


@app.get(
    "/api/transactions",
    response_model=TransactionListResponse,
)
def list_transactions(
    limit: int = 25,
    offset: int = 0,
    account_number: str | None = None,
    currency: str | None = None,
    transaction_type: str | None = None,
    category: str | None = None,
    search: str | None = None,
    sort_by: Literal[
        "id",
        "date",
        "category",
    ] = "date",
    sort_order: Literal[
        "asc",
        "desc",
    ] = "desc",
    database: Session = Depends(get_db),
) -> TransactionListResponse:
    items, total = list_transactions_raw(
        database=database,
        limit=limit,
        offset=offset,
        account_number=account_number,
        currency=currency,
        transaction_type=transaction_type,
        category=category,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return TransactionListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@app.get(
    "/api/transactions/{transaction_id}",
    response_model=TransactionRead,
)
def get_transaction(
    transaction_id: int,
    database: Session = Depends(get_db),
) -> TransactionRead:
    transaction = crud.get_transaction(
        database,
        transaction_id,
    )

    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction was not found.",
        )

    return transaction


@app.post(
    "/api/transactions",
    response_model=TransactionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_transaction(
    transaction_data: TransactionCreate,
    database: Session = Depends(get_db),
) -> TransactionRead:
    duplicate = crud.get_transaction_by_source_key(
        database=database,
        account_number=transaction_data.account_number,
        statement_period=transaction_data.statement_period,
        reference_number=transaction_data.reference_number,
    )

    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A transaction with the same account, "
                "statement period and reference number "
                "already exists."
            ),
        )

    try:
        return crud.create_transaction(
            database,
            transaction_data,
        )
    except IntegrityError as error:
        database.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Transaction already exists.",
        ) from error


@app.put(
    "/api/transactions/{transaction_id}",
    response_model=TransactionRead,
)
def update_transaction(
    transaction_id: int,
    transaction_data: TransactionUpdate,
    database: Session = Depends(get_db),
) -> TransactionRead:
    transaction = crud.get_transaction(
        database,
        transaction_id,
    )

    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction was not found.",
        )

    duplicate = crud.get_transaction_by_source_key(
        database=database,
        account_number=transaction_data.account_number,
        statement_period=transaction_data.statement_period,
        reference_number=transaction_data.reference_number,
    )

    if (
        duplicate is not None
        and duplicate.id != transaction_id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Another transaction with the same "
                "source key already exists."
            ),
        )

    try:
        return crud.update_transaction(
            database=database,
            transaction=transaction,
            transaction_data=transaction_data,
        )
    except IntegrityError as error:
        database.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "The updated transaction conflicts "
                "with an existing record."
            ),
        ) from error