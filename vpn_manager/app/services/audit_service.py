import logging
from sqlalchemy.orm import Session

from app.models.entities import AuditLog

logger = logging.getLogger(__name__)


def log_event(db: Session, action: str, details: str, level: str = "INFO") -> None:
    logger.info("%s | %s", action, details)
    row = AuditLog(action=action, details=details, level=level)
    db.add(row)
    db.commit()
