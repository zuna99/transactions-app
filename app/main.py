from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db


app = FastAPI(
    title="Business Transactions Application",
    description="Application for importing and managing business transactions.",
    version="1.0.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/db-health")
def database_health_check(
    db: Session = Depends(get_db),
) -> dict[str, str]:
    db.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "database": "connected",
    }