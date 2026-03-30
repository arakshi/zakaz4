from collections import defaultdict
from datetime import datetime, timedelta

import psutil
from sqlalchemy.orm import Session

from app.models.entities import MonitoringSnapshot


class StatisticsService:
    """Aggregates monitoring snapshots for charts and educational analytics."""

    def get_summary(self, db: Session, hours: int = 24) -> dict:
        since = datetime.utcnow() - timedelta(hours=hours)
        rows = (
            db.query(MonitoringSnapshot)
            .filter(MonitoringSnapshot.checked_at >= since)
            .order_by(MonitoringSnapshot.checked_at.asc())
            .all()
        )

        timeline = defaultdict(lambda: {"online": 0, "offline": 0, "rx": 0, "tx": 0, "lat": []})
        total_rx = 0
        total_tx = 0

        for row in rows:
            bucket = row.checked_at.strftime("%H:%M")
            timeline[bucket][row.status] += 1
            timeline[bucket]["rx"] += row.received_bytes
            timeline[bucket]["tx"] += row.sent_bytes
            if row.ping_latency_ms >= 0:
                timeline[bucket]["lat"].append(row.ping_latency_ms)
            total_rx += row.received_bytes
            total_tx += row.sent_bytes

        labels = sorted(timeline.keys())
        online = [timeline[label]["online"] for label in labels]
        offline = [timeline[label]["offline"] for label in labels]
        avg_latency = [
            round(sum(timeline[label]["lat"]) / len(timeline[label]["lat"]), 2) if timeline[label]["lat"] else None
            for label in labels
        ]

        return {
            "labels": labels,
            "online": online,
            "offline": offline,
            "avg_latency": avg_latency,
            "total_rx": total_rx,
            "total_tx": total_tx,
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "snapshot_count": len(rows),
        }
