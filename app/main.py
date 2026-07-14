from fastapi import FastAPI

app = FastAPI(
    title="Business Transactions Application",
    description="Application for importing and managing business transactions.",
    version="1.0.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}