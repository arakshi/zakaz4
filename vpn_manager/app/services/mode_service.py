import platform
import shutil

from app.core.config import settings


def detect_mode() -> str:
    forced = settings.app_mode.strip().lower()
    if forced in {"demo", "real"}:
        return forced.upper()
    if platform.system().lower() == "linux" and shutil.which("wg"):
        return "REAL"
    return "DEMO"
