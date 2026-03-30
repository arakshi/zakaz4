from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default="admin")


class VPNServer(Base):
    __tablename__ = "vpn_servers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    interface_name: Mapped[str] = mapped_column(String(64), default="wg0")
    endpoint: Mapped[str] = mapped_column(String(120), default="")
    address: Mapped[str] = mapped_column(String(64), default="10.0.0.1/24")
    public_key: Mapped[str] = mapped_column(String(255), default="")
    private_key: Mapped[str] = mapped_column(String(255), default="")
    listen_port: Mapped[int] = mapped_column(Integer, default=51820)
    mode: Mapped[str] = mapped_column(String(16), default="DEMO")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    clients: Mapped[list["VPNClient"]] = relationship(back_populates="server", cascade="all, delete-orphan")


class VPNClient(Base):
    __tablename__ = "vpn_clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    server_id: Mapped[int] = mapped_column(ForeignKey("vpn_servers.id"))
    name: Mapped[str] = mapped_column(String(120), unique=True)
    ip_address: Mapped[str] = mapped_column(String(64))
    public_key: Mapped[str] = mapped_column(String(255), default="")
    private_key: Mapped[str] = mapped_column(String(255), default="")
    preshared_key: Mapped[str] = mapped_column(String(255), default="")
    endpoint: Mapped[str] = mapped_column(String(120), default="")
    allowed_ips: Mapped[str] = mapped_column(String(120), default="0.0.0.0/0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    server: Mapped[VPNServer] = relationship(back_populates="clients")


class VPNPeer(Base):
    __tablename__ = "vpn_peers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_node: Mapped[str] = mapped_column(String(120))
    target_node: Mapped[str] = mapped_column(String(120))
    link_type: Mapped[str] = mapped_column(String(32), default="site-to-site")
    notes: Mapped[str] = mapped_column(Text, default="")


class Subnet(Base):
    __tablename__ = "subnets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    cidr: Mapped[str] = mapped_column(String(64), unique=True)
    node_name: Mapped[str] = mapped_column(String(120))


class Backup(Base):
    __tablename__ = "backups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), unique=True)
    path: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    action: Mapped[str] = mapped_column(String(120))
    details: Mapped[str] = mapped_column(Text, default="")
    level: Mapped[str] = mapped_column(String(16), default="INFO")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MonitoringSnapshot(Base):
    __tablename__ = "monitoring_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    peer_name: Mapped[str] = mapped_column(String(120))
    endpoint: Mapped[str] = mapped_column(String(120), default="")
    latest_handshake: Mapped[str] = mapped_column(String(120), default="never")
    received_bytes: Mapped[int] = mapped_column(Integer, default=0)
    sent_bytes: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="offline")
    ping_latency_ms: Mapped[int] = mapped_column(Integer, default=-1)
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Setting(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(120), unique=True)
    value: Mapped[str] = mapped_column(Text, default="")
