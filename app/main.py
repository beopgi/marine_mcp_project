"""Application entry point."""

from fastapi import FastAPI

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import setup_logging

settings = get_settings()
setup_logging(settings.log_level)

app = FastAPI(title=settings.app_name)
app.include_router(router)
