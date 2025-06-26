from pydantic import BaseModel
from datetime import datetime

class SolarStorage(BaseModel):
    panel_output_kw:float
    storage_kw:float
    charge_percent:float
    timestamp: datetime

class Config:
        orm_mode = True 
