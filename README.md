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