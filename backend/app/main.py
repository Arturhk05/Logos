from fastapi import FastAPI

from app.api.routes import health
from app.core.config import get_settings

API_PREFIX = "/api"


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Logos API",
        version="0.1.0",
        debug=settings.is_development,
        docs_url=f"{API_PREFIX}/docs",
        openapi_url=f"{API_PREFIX}/openapi.json",
        redoc_url=None,
    )
    app.include_router(health.router, prefix=API_PREFIX)
    return app


app = create_app()
