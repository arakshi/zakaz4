from pathlib import Path
from ipaddress import ip_network
from sqlalchemy.orm import Session

from app.core.config import BASE_DIR
from app.models.entities import VPNClient, VPNServer
from app.services.audit_service import log_event
from app.utils.wireguard_utils import generate_preshared_key, generate_wg_keypair

try:
    import qrcode
except ModuleNotFoundError:  # optional dependency for simple launch
    qrcode = None


class ConfigService:
    def __init__(self) -> None:
        self.output_dir = BASE_DIR / "generated_configs"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _next_ip(self, db: Session, server: VPNServer) -> str:
        net = ip_network(server.address, strict=False)
        used = {c.ip_address for c in server.clients}
        for host in net.hosts():
            ip = str(host)
            if ip != str(net.network_address + 1) and ip not in used:
                return ip
        raise ValueError("IP-пул исчерпан")

    def create_server(self, db: Session, name: str, endpoint: str, address: str, interface_name: str, mode: str) -> VPNServer:
        private_key, public_key = generate_wg_keypair()
        server = VPNServer(
            name=name,
            endpoint=endpoint,
            address=address,
            interface_name=interface_name,
            private_key=private_key,
            public_key=public_key,
            mode=mode,
        )
        db.add(server)
        db.commit()
        db.refresh(server)
        self.write_server_config(server)
        log_event(db, "create_server", f"Создан сервер {name}")
        return server

    def create_client(self, db: Session, server: VPNServer, name: str, endpoint: str, allowed_ips: str) -> VPNClient:
        private_key, public_key = generate_wg_keypair()
        ip_addr = self._next_ip(db, server)
        client = VPNClient(
            server_id=server.id,
            name=name,
            ip_address=ip_addr,
            private_key=private_key,
            public_key=public_key,
            preshared_key=generate_preshared_key(),
            endpoint=endpoint,
            allowed_ips=allowed_ips,
        )
        db.add(client)
        db.commit()
        db.refresh(client)
        self.write_client_config(server, client)
        self.write_server_config(server)
        self.generate_qr(client)
        log_event(db, "create_client", f"Создан клиент {name}")
        return client

    def write_server_config(self, server: VPNServer) -> Path:
        path = self.output_dir / f"server_{server.name}.conf"
        peer_lines = []
        for client in server.clients:
            peer_lines.append(
                f"\n[Peer]\n# {client.name}\nPublicKey = {client.public_key}\nPresharedKey = {client.preshared_key}\nAllowedIPs = {client.ip_address}/32\n"
            )
        content = (
            f"[Interface]\nAddress = {server.address}\nListenPort = {server.listen_port}\nPrivateKey = {server.private_key}\n"
            + "".join(peer_lines)
        )
        path.write_text(content, encoding="utf-8")
        return path

    def write_client_config(self, server: VPNServer, client: VPNClient) -> Path:
        path = self.output_dir / f"client_{client.name}.conf"
        content = (
            f"[Interface]\nPrivateKey = {client.private_key}\nAddress = {client.ip_address}/32\nDNS = 1.1.1.1\n\n"
            f"[Peer]\nPublicKey = {server.public_key}\nPresharedKey = {client.preshared_key}\nAllowedIPs = {client.allowed_ips}\nEndpoint = {server.endpoint}\nPersistentKeepalive = 25\n"
        )
        path.write_text(content, encoding="utf-8")
        return path

    def generate_qr(self, client: VPNClient) -> Path:
        """Generate PNG QR if qrcode is installed, else create a text note with same base name."""
        conf_path = self.output_dir / f"client_{client.name}.conf"
        qr_path = self.output_dir / f"client_{client.name}.png"
        if qrcode is not None:
            qr = qrcode.make(conf_path.read_text(encoding="utf-8"))
            qr.save(qr_path)
            return qr_path
        fallback = self.output_dir / f"client_{client.name}_qr_unavailable.txt"
        fallback.write_text(
            "Пакет qrcode не установлен. Установите зависимости из requirements.txt для генерации PNG QR.",
            encoding="utf-8",
        )
        return fallback
