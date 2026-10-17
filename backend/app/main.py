from fastapi import FastAPI

from app.api.routes import health

API_PREFIX = "/api"


def create_app() -> FastAPI:
    app = FastAPI(
        title="Logos API",
        version="0.1.0",
        docs_url=f"{API_PREFIX}/docs",
        openapi_url=f"{API_PREFIX}/openapi.json",
        redoc_url=None,
    )
    app.include_router(health.router, prefix=API_PREFIX)
    return app


app = create_app()
