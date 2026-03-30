from datetime import datetime
from pathlib import Path
import zipfile

from sqlalchemy.orm import Session

from app.core.config import BASE_DIR
from app.models.entities import Backup
from app.services.audit_service import log_event


class BackupService:
    def __init__(self) -> None:
        self.backup_dir = BASE_DIR / "backups"
        self.config_dir = BASE_DIR / "generated_configs"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, db: Session) -> Backup:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        archive_name = f"configs_backup_{ts}.zip"
        archive_path = self.backup_dir / archive_name
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in self.config_dir.glob("*.conf"):
                zf.write(file, arcname=file.name)
            for file in self.config_dir.glob("*.png"):
                zf.write(file, arcname=file.name)
        rec = Backup(filename=archive_name, path=str(archive_path))
        db.add(rec)
        db.commit()
        db.refresh(rec)
        log_event(db, "backup_create", f"Создан backup {archive_name}")
        return rec

    def restore_backup(self, db: Session, backup: Backup) -> None:
        with zipfile.ZipFile(backup.path, "r") as zf:
            zf.extractall(self.config_dir)
        log_event(db, "backup_restore", f"Восстановление из {backup.filename}")
