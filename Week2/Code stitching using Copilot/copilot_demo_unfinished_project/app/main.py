from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(
    title="Copilot Demo Task API",
    version="1.0.0",
    description="Intentionally unfinished project for demonstrating GitHub Copilot.",
)

app.include_router(router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
