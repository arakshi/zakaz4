from pathlib import Path
import shutil

from sqlalchemy.orm import Session

from app.core.config import BASE_DIR
from app.models.entities import VPNClient, VPNServer


class DiagnosticsService:
    def run_checks(self, db: Session) -> list[dict[str, str]]:
        results: list[dict[str, str]] = []
        wg_found = shutil.which("wg") is not None
        results.append({"name": "WireGuard binary", "status": "OK" if wg_found else "WARN", "details": "wg найден" if wg_found else "wg не найден, DEMO режим"})

        servers = db.query(VPNServer).all()
        for server in servers:
            server_conf = BASE_DIR / "generated_configs" / f"server_{server.name}.conf"
            results.append({
                "name": f"Config {server.name}",
                "status": "OK" if server_conf.exists() else "ERROR",
                "details": f"{server_conf.name} {'существует' if server_conf.exists() else 'не найден'}",
            })

        clients = db.query(VPNClient).all()
        ip_pool_ok = len(clients) < 250
        results.append({"name": "IP pool", "status": "OK" if ip_pool_ok else "WARN", "details": f"Выдано адресов: {len(clients)}"})
        return results
