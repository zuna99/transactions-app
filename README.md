# Business Transactions Application

A small full-stack application for importing and managing business transaction records.

The application:

- imports transaction data from a JSON file;
- validates and normalizes imported data;
- stores valid records in PostgreSQL;
- generates a report for rejected and duplicate records;
- provides a REST API for viewing, creating and updating transactions;
- includes a simple web interface;
- uses both SQLAlchemy ORM and plain SQL.

## Technologies

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Pydantic
- Jinja2
- HTML, CSS and JavaScript
- Docker Compose
- Pytest

## Project structure

```text
transactions-app/
├── alembic/
├── app/
│   ├── static/
│   │   ├── app.js
│   │   └── styles.css
│   ├── templates/
│   │   └── index.html
│   ├── config.py
│   ├── crud.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── raw_sql.py
│   └── schemas.py
├── data/
│   └── sample.json
├── reports/
│   └── .gitkeep
├── scripts/
│   └── import_json.py
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   └── test_schemas.py
├── .env.example
├── .gitignore
├── alembic.ini
├── docker-compose.yml
├── requirements.txt
└── README.md

## Requirements

Before running the project, install:

- Python 3.11 or newer
- Docker Desktop
- Git

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/zuna99/transactions-app.git
cd transactions-app
```

### 2. Create a virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Create the environment configuration

Create a file named `.env` in the project root.

Use the following values:

```env
POSTGRES_DB=transactions_db
POSTGRES_USER=transactions_user
POSTGRES_PASSWORD=transactions_password
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5433
```

The PostgreSQL container uses port `5432` internally and is exposed on port `5433` on the host machine.

The `.env` file is excluded from Git and should not be committed.

## Start PostgreSQL

Make sure Docker Desktop is running.

Start the PostgreSQL container:

```powershell
docker compose up -d
```

Check its status:

```powershell
docker compose ps
```

The container should have a status similar to:

```text
Up (healthy)
```

## Apply Database Migrations

Create the database tables by running:

```powershell
python -m alembic upgrade head
```

Check the currently applied migration:

```powershell
python -m alembic current
```

The output should include:

```text
(head)
```

## Import Transaction Data

Import the provided JSON file:

```powershell
python -m scripts.import_json
```

The importer performs the following operations:

- validates each JSON record;
- converts valid date and amount values;
- converts currencies such as `eur` to `EUR`;
- removes leading and trailing whitespace;
- converts transaction types to lowercase;
- skips invalid records;
- skips duplicate records;
- prevents repeated imports from creating duplicate database rows;
- generates a rejected-record report in the `reports` directory.

For the provided `sample.json` file, the first import produces:

```text
Import completed
----------------
Total records:       226
Inserted records:    217
Already in database: 0
Source duplicates:   2
Invalid skipped:     7
```

Running the importer again does not insert the same valid records twice.

### Specify a report output path

```powershell
python -m scripts.import_json --report-file reports\custom_report.json
```

## Rejected Record Reports

Invalid and duplicate source records are written to a JSON file inside:

```text
reports/
```

Example filename:

```text
rejected_records_20260714_183500.json
```

The report includes:

- the original record number;
- the rejection status;
- validation errors;
- the original JSON record;
- the duplicate source key, when applicable;
- an import summary.

Generated JSON reports are ignored by Git.

## Run the Application

Start FastAPI:

```powershell
python -m uvicorn app.main:app --reload
```

Open the web interface:

```text
http://127.0.0.1:8000/
```

Open the Swagger API documentation:

```text
http://127.0.0.1:8000/docs
```

Open the alternative API documentation:

```text
http://127.0.0.1:8000/redoc
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check whether the application is running |
| GET | `/db-health` | Check the PostgreSQL connection |
| GET | `/api/transactions` | List, search, and filter transactions |
| GET | `/api/transactions/{transaction_id}` | Get one transaction |
| POST | `/api/transactions` | Create a new transaction |
| PUT | `/api/transactions/{transaction_id}` | Update an existing transaction |

## Listing and Filtering Transactions

The list endpoint supports pagination:

```text
/api/transactions?limit=25&offset=0
```

Filter by account number:

```text
/api/transactions?account_number=BA-1001
```

Filter by currency:

```text
/api/transactions?currency=EUR
```

Filter by transaction type:

```text
/api/transactions?transaction_type=card_payment
```

Filter by category:

```text
/api/transactions?category=Software
```

Search multiple text fields:

```text
/api/transactions?search=Software
```

Filters can be combined:

```text
/api/transactions?currency=EUR&search=Software&limit=10
```

## Example Transaction

```json
{
  "account_number": "BA-TEST-001",
  "statement_period": "2026-08",
  "transaction_date": "2026-08-10",
  "booking_date": "2026-08-11",
  "reference_number": "TEST-001",
  "transaction_type": "card_payment",
  "amount": -89.99,
  "currency": "USD",
  "counterparty_name": "Demo Software Company",
  "category": "Software"
}
```

A transaction is considered a duplicate when another transaction has the same combination of:

```text
account_number
statement_period
reference_number
```

The API returns `409 Conflict` when a duplicate is submitted.

## ORM and Plain SQL

SQLAlchemy ORM is used for:

- retrieving individual records;
- checking duplicate source keys;
- creating transactions;
- updating transactions.

Parameterized plain SQL is used in `app/raw_sql.py` for:

- listing transactions;
- counting matching records;
- pagination;
- filtering;
- text search.

User-provided values are passed as bound SQL parameters and are not directly inserted into SQL strings.

## Data Validation

The application validates:

- required fields;
- valid dates in `YYYY-MM-DD` format;
- statement periods in `YYYY-MM` format;
- decimal transaction amounts;
- three-letter currency codes;
- non-empty text fields;
- maximum field lengths.

Examples of rejected values include:

```json
{
  "amount": null
}
```

```json
{
  "amount": "not_available"
}
```

```json
{
  "transaction_date": "2026-02-30"
}
```

```json
{
  "currency": null
}
```

Invalid financial values are not silently replaced with zero or another default value.

## Automated Tests

Run all tests:

```powershell
python -m pytest -q
```

Expected result:

```text
10 passed
```

The test suite covers:

- health endpoints;
- database health endpoint;
- creating transactions;
- currency normalization;
- duplicate detection;
- listing transactions;
- retrieving one transaction;
- updating transactions;
- missing transaction handling;
- invalid date validation;
- invalid amount validation;
- whitespace normalization.

Tests use an isolated in-memory test database and do not modify the development PostgreSQL database.

A deprecation warning from the test client may appear, but it does not prevent the tests from passing.

## Stop PostgreSQL

Stop the container while preserving the stored data:

```powershell
docker compose down
```

Start it again later with:

```powershell
docker compose up -d
```

To delete both the container and the PostgreSQL volume:

```powershell
docker compose down -v
```

Warning: using `-v` permanently deletes data stored in the Docker volume.

## Useful Commands

Start PostgreSQL:

```powershell
docker compose up -d
```

Run migrations:

```powershell
python -m alembic upgrade head
```

Import data:

```powershell
python -m scripts.import_json
```

Start the application:

```powershell
python -m uvicorn app.main:app --reload
```

Run tests:

```powershell
python -m pytest -q
```

Stop PostgreSQL:

```powershell
docker compose down
```

## Author

Jovan Zunic