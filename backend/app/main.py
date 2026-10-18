from fastapi import FastAPI

from app.router import API_PREFIX, api_router
from app.shared.config import get_settings
from app.shared.error_handlers import register_error_handlers


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
    register_error_handlers(app)
    app.include_router(api_router)
    return app


app = create_app()
