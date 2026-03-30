from sqlalchemy.orm import Session

from app.models.entities import MonitoringSnapshot, VPNClient, VPNPeer, VPNServer, Subnet


def get_servers(db: Session) -> list[VPNServer]:
    return db.query(VPNServer).order_by(VPNServer.id.desc()).all()


def get_clients(db: Session) -> list[VPNClient]:
    return db.query(VPNClient).order_by(VPNClient.id.desc()).all()


def get_topology(db: Session) -> tuple[list[Subnet], list[VPNPeer]]:
    return db.query(Subnet).all(), db.query(VPNPeer).all()


def latest_snapshots(db: Session, limit: int = 30) -> list[MonitoringSnapshot]:
    return db.query(MonitoringSnapshot).order_by(MonitoringSnapshot.checked_at.desc()).limit(limit).all()
