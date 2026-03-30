from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import BASE_DIR
from app.core.database import get_db
from app.core.security import create_session_token, verify_password
from app.models.entities import AuditLog, Backup, Subnet, User, VPNClient, VPNPeer, VPNServer
from app.repositories.vpn_repository import get_clients, get_servers, get_topology, latest_snapshots
from app.services.backup_service import BackupService
from app.services.config_service import ConfigService
from app.services.diagnostics_service import DiagnosticsService
from app.services.mode_service import detect_mode
from app.services.monitoring_service import MonitoringService

templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))
router = APIRouter()
config_service = ConfigService()
backup_service = BackupService()
monitoring_service = MonitoringService()
diagnostics_service = DiagnosticsService()


def _ctx(request: Request, **kwargs):
    return {"request": request, "mode": detect_mode(), **kwargs}


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", _ctx(request))


@router.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse("login.html", _ctx(request, error="Неверный логин или пароль"))
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie("session", create_session_token(user.username), httponly=True)
    return response


@router.get("/logout")
def logout():
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie("session")
    return response


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    servers = get_servers(db)
    clients = get_clients(db)
    snaps = latest_snapshots(db, limit=20)
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(8).all()
    active = sum(1 for s in snaps if s.status == "online")
    return templates.TemplateResponse("dashboard.html", _ctx(request, servers=servers, clients=clients, snaps=snaps, logs=logs, active=active))


@router.get("/servers", response_class=HTMLResponse)
def servers_page(request: Request, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return templates.TemplateResponse("servers.html", _ctx(request, servers=get_servers(db)))


@router.post("/servers/create")
def servers_create(
    name: str = Form(...), endpoint: str = Form("127.0.0.1:51820"), address: str = Form("10.0.0.1/24"), interface_name: str = Form("wg0"),
    _: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    config_service.create_server(db, name=name, endpoint=endpoint, address=address, interface_name=interface_name, mode=detect_mode())
    return RedirectResponse("/servers", status_code=303)


@router.get("/clients", response_class=HTMLResponse)
def clients_page(request: Request, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return templates.TemplateResponse("clients.html", _ctx(request, clients=get_clients(db), servers=get_servers(db)))


@router.post("/clients/create")
def clients_create(server_id: int = Form(...), name: str = Form(...), endpoint: str = Form(""), allowed_ips: str = Form("0.0.0.0/0"), _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    server = db.query(VPNServer).filter(VPNServer.id == server_id).first()
    if server:
        config_service.create_client(db, server=server, name=name, endpoint=endpoint, allowed_ips=allowed_ips)
    return RedirectResponse("/clients", status_code=303)


@router.get("/topology", response_class=HTMLResponse)
def topology_page(request: Request, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    subnets, links = get_topology(db)
    return templates.TemplateResponse("topology.html", _ctx(request, subnets=subnets, links=links))


@router.post("/topology/subnet")
def add_subnet(name: str = Form(...), cidr: str = Form(...), node_name: str = Form(...), _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.add(Subnet(name=name, cidr=cidr, node_name=node_name))
    db.commit()
    return RedirectResponse("/topology", status_code=303)


@router.post("/topology/link")
def add_link(source_node: str = Form(...), target_node: str = Form(...), link_type: str = Form("site-to-site"), notes: str = Form(""), _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.add(VPNPeer(source_node=source_node, target_node=target_node, link_type=link_type, notes=notes))
    db.commit()
    return RedirectResponse("/topology", status_code=303)


@router.get("/monitoring", response_class=HTMLResponse)
def monitoring_page(request: Request, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    snaps = monitoring_service.collect(db, get_clients(db), detect_mode())
    return templates.TemplateResponse("monitoring.html", _ctx(request, snaps=snaps))


@router.get("/diagnostics", response_class=HTMLResponse)
def diagnostics_page(request: Request, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    results = diagnostics_service.run_checks(db)
    return templates.TemplateResponse("diagnostics.html", _ctx(request, results=results))


@router.get("/backups", response_class=HTMLResponse)
def backups_page(request: Request, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(Backup).order_by(Backup.created_at.desc()).all()
    return templates.TemplateResponse("backups.html", _ctx(request, backups=items))


@router.post("/backups/create")
def backup_create(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    backup_service.create_backup(db)
    return RedirectResponse("/backups", status_code=303)


@router.post("/backups/restore/{backup_id}")
def backup_restore(backup_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(Backup).filter(Backup.id == backup_id).first()
    if item:
        backup_service.restore_backup(db, item)
    return RedirectResponse("/backups", status_code=303)


@router.get("/logs", response_class=HTMLResponse)
def logs_page(request: Request, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(300).all()
    return templates.TemplateResponse("logs.html", _ctx(request, logs=items))


@router.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return templates.TemplateResponse("settings.html", _ctx(request, server_count=db.query(VPNServer).count()))


@router.get("/configs/{filename}")
def get_config(filename: str, _: User = Depends(get_current_user)):
    path = BASE_DIR / "generated_configs" / filename
    return FileResponse(path)
