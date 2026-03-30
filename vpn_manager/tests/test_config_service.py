from app.core.database import Base, SessionLocal, engine
from app.models.entities import VPNServer
from app.services.config_service import ConfigService


def test_create_server_and_client() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    service = ConfigService()
    server = service.create_server(db, "pytest-server", "127.0.0.1:51820", "10.99.0.1/24", "wg9", "DEMO")
    assert server.id is not None
    client = service.create_client(db, server, "pytest-client", "", "0.0.0.0/0")
    assert client.ip_address.startswith("10.99.0.")
    db.delete(client)
    db.delete(server)
    db.commit()
    db.close()
