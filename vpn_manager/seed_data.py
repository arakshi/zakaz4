from app.core.database import SessionLocal
from app.models.entities import Subnet, VPNPeer, VPNServer
from app.services.config_service import ConfigService
from app.services.mode_service import detect_mode


def seed() -> None:
    db = SessionLocal()
    service = ConfigService()
    try:
        if db.query(VPNServer).count() > 0:
            return
        hq = service.create_server(db, "hq", "203.0.113.10:51820", "10.10.0.1/24", "wg0", detect_mode())
        for i in range(1, 6):
            service.create_client(db, hq, f"employee{i}", "", "0.0.0.0/0")
        db.add_all([
            Subnet(name="Центральный офис", cidr="10.10.0.0/24", node_name="hq"),
            Subnet(name="Филиал-1", cidr="10.20.0.0/24", node_name="branch1"),
            Subnet(name="Филиал-2", cidr="10.30.0.0/24", node_name="branch2"),
            VPNPeer(source_node="hq", target_node="branch1", link_type="site-to-site", notes="Основной туннель"),
            VPNPeer(source_node="hq", target_node="branch2", link_type="site-to-site", notes="Резервный маршрут"),
        ])
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
    print("Seed done")
