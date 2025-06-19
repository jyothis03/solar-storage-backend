from fastapi import FastAPI
from random import uniform
from schemas import SolarStorage

app = FastAPI()

@app.get("/")
def root():
    return{"message":"welcome to chainfly"}

@app.get("/simulate",response_model=SolarStorage)
def simulate_storage():
    panel_output_kw=round(uniform(2.0,6.0),2)
    storage_kw=round(uniform(1.0,5.0),2)
    charge_percent = round((storage_kw / 5.0) * 100, 1)
    return {"panel_output_kw":panel_output_kw,
            "storage_kw":storage_kw,
            "charge_percent":charge_percent}
