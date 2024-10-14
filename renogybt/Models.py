from pydantic import BaseModel

class DeviceModel(BaseModel):
    adapter: str
    mac_addr: str
    alias: str
    type: str
    device_id: int