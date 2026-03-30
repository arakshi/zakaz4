from pydantic import BaseModel, Field


class ServerCreate(BaseModel):
    name: str = Field(min_length=2)
    endpoint: str = "127.0.0.1:51820"
    address: str = "10.0.0.1/24"
    interface_name: str = "wg0"


class ClientCreate(BaseModel):
    server_id: int
    name: str = Field(min_length=2)
    endpoint: str = ""
    allowed_ips: str = "0.0.0.0/0"


class SubnetCreate(BaseModel):
    name: str
    cidr: str
    node_name: str
