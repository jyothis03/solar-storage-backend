from pydantic import BaseModel

class SolarStorage(BaseModel):
    panel_output_kw:float
    storage_kw:float
    charge_percent:float

    