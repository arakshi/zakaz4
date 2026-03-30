import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.config import BASE_DIR


def setup_logging() -> None:
    log_dir = BASE_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(log_dir / "app.log", maxBytes=1_000_000, backupCount=5, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    if not root.handlers:
        root.addHandler(handler)
