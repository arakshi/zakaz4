from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import BASE_DIR, settings
from app.core.logging_config import setup_logging
from init_db import init_db
from seed_data import seed


def create_app() -> FastAPI:
    for folder in ["data", "backups", "generated_configs", "logs", "generated_configs/examples"]:
        (BASE_DIR / folder).mkdir(parents=True, exist_ok=True)

    setup_logging()
    init_db()
    seed()

    app = FastAPI(title=settings.app_name)
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")
    app.include_router(router)
    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.app_host, port=settings.app_port, reload=False)
