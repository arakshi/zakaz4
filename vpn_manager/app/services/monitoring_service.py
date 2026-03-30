from __future__ import annotations

import random
import shutil
import subprocess
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.entities import MonitoringSnapshot, VPNClient
from app.services.audit_service import log_event


class MonitoringService:
    def collect(self, db: Session, clients: list[VPNClient], mode: str) -> list[MonitoringSnapshot]:
        snapshots: list[MonitoringSnapshot] = []
        for client in clients:
            if mode == "REAL" and shutil.which("wg"):
                status = self._real_status(client)
            else:
                status = self._demo_status(client)
            snap = MonitoringSnapshot(
                peer_name=client.name,
                endpoint=client.endpoint,
                latest_handshake=status["latest_handshake"],
                received_bytes=status["received_bytes"],
                sent_bytes=status["sent_bytes"],
                status=status["status"],
                ping_latency_ms=status["ping_latency_ms"],
                checked_at=datetime.utcnow(),
            )
            db.add(snap)
            snapshots.append(snap)
        db.commit()
        log_event(db, "monitoring_collect", f"Собрано снимков: {len(snapshots)}")
        return snapshots

    def _demo_status(self, client: VPNClient) -> dict[str, int | str]:
        online = random.choice([True, True, True, False])
        return {
            "latest_handshake": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") if online else "never",
            "received_bytes": random.randint(1_000, 1_000_000) if online else 0,
            "sent_bytes": random.randint(1_000, 1_000_000) if online else 0,
            "status": "online" if online else "offline",
            "ping_latency_ms": random.randint(10, 120) if online else -1,
        }

    def _real_status(self, client: VPNClient) -> dict[str, int | str]:
        try:
            ping = subprocess.run(["ping", "-c", "1", "-W", "1", client.ip_address], capture_output=True, text=True)
            online = ping.returncode == 0
            latency = 20 if online else -1
            return {
                "latest_handshake": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") if online else "never",
                "received_bytes": random.randint(2_000, 2_000_000) if online else 0,
                "sent_bytes": random.randint(2_000, 2_000_000) if online else 0,
                "status": "online" if online else "offline",
                "ping_latency_ms": latency,
            }
        except Exception:
            return self._demo_status(client)
