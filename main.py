from fastapi import FastAPI, Query, Depends
from random import uniform
from schemas import SolarStorage
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, SolarStorageModel
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime,timezone
from sqlalchemy.orm import Session
from geopy.geocoders import Nominatim
import random
import requests

app = FastAPI()
DEMO_MODE = True #set to false when going live

DATABASE_URL = "postgresql://jyothis:jCJCnWNjuZLglDpts98mP4AUzHhAiAjF@dpg-d1declm3jp1c73f10470-a.singapore-postgres.render.com/solar_storage"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.add_middleware(
    CORSMiddleware,
       allow_origins=["*"],  
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )

@app.get("/")
def root():
    return{"message":"welcome to chainfly"}

def get_lat_lon(location_name):
    geolocator = Nominatim(user_agent="solar_sim")
    loc = geolocator.geocode(location_name)
    if loc:
        return loc.latitude, loc.longitude
    else:
        print(f"[WARN] Could not geocode location '{location_name}'. Using fallback coordinates (10.0, 76.0).")
        return 10.0, 76.0

def fetch_irradiance(lat,lon):
    url = f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters=ALLSKY_SFC_SW_DWN&community=RE&longitude={lon}&latitude={lat}&format=JSON&start=2022&end=2022"
    res=requests.get(url)
    data=res.json()
    try:
        values = list(data['properties']['parameter']['ALLSKY_SFC_SW_DWN'].values())
        avg = sum(values) / len(values)
        return avg / 5.0
    except Exception as e:
        print(f"[WARN] NASA API failed for coordinates ({lat}, {lon}). Error: {e}. Using fallback factor 1.0.")
        return 1.0

def scenario_factor(scenario):
    if scenario == "Clear":
        return 1.0
    elif scenario == "Cloudy":
        return 0.6
    elif scenario == "Monsoon":
        return 0.4
    else:
        return 1.0
    
def add_noise(value, enabled):
    if enabled:
        noise_factor = random.uniform(0.9, 1.1)
        return value * noise_factor
    return value

def get_solar_storage(specific_id: int = None,location="Default", scenario="Clear", noise=False, db : Session = None):
    if DEMO_MODE:
        panel_output_kw = 5.0
        storage_kw = round(uniform(1.0, 5.0), 2)
        charge_percent = round((storage_kw / 5.0) * 100, 1)

        lat,lon = get_lat_lon(location)
        irradiance_factor = fetch_irradiance(lat,lon)
        scen_factor = scenario_factor(scenario)
        adjusted_output = panel_output_kw * irradiance_factor * scen_factor
        adjusted_output = round(add_noise(adjusted_output, noise),2)

        return SolarStorage(
            panel_output_kw=adjusted_output,
            storage_kw=storage_kw,
            charge_percent=charge_percent,
            timestamp=datetime.now(timezone.utc)
        )
    else:
        if specific_id is not None:
            result = db.query(SolarStorageModel).filter(SolarStorageModel.id == specific_id).first()
        else:
            result = db.query(SolarStorageModel).order_by(SolarStorageModel.id.desc()).first()
        

        if result:
            return SolarStorage(
                panel_output_kw=result.panel_output_kw,
                storage_kw=result.storage_kw,
                charge_percent=result.charge_percent,
                timestamp=datetime.now(timezone.utc)
        
        )
        else:
            return SolarStorage(
                panel_output_kw=0.0,
                storage_kw=0.0,
                charge_percent=0.0
        )
        
@app.get("/simulate", response_model=SolarStorage)
def simulate_storage(
    id: int = Query(default=None, description="Fetch by specific id if provided"),
    location: str = Query(default="Default", description="Location to simulate irradiance"),
    battery_size: float = Query(default=5.0, description="Battery size in kWh"),
    loss_factor: float = Query(default=10.0, description="System loss percentage"),
    scenario: str = Query(default="Clear", description="Scenario: Clear, Cloudy, Monsoon"),
    noise: bool = Query(default=False, description="Add random noise toggle"),
    db: Session = Depends(get_db)
):
    if DEMO_MODE:
        data = get_solar_storage(location=location, scenario=scenario, noise=noise, db=db)
        adjusted_panel_output = data.panel_output_kw * ((100 - loss_factor) / 100)

        base_battery = 5.0
        scaled_storage_kw = data.storage_kw * (battery_size / base_battery)
        new_charge_percent = round((scaled_storage_kw / battery_size) * 100, 1)

        data.panel_output_kw = round(adjusted_panel_output, 2)
        data.storage_kw = round(scaled_storage_kw, 2)
        data.charge_percent = new_charge_percent

        record = SolarStorageModel(
            panel_output_kw=data.panel_output_kw,
            storage_kw=data.storage_kw,
            charge_percent=data.charge_percent,
            timestamp=data.timestamp
        )
        db.add(record)
        db.commit()

        return data
    else:
        data = get_solar_storage(db=db,specific_id=id)
        return data


@app.get("/charts")
def last10records(
    db:Session= Depends(get_db)
):
    records=(db.query(SolarStorageModel)
             .order_by(SolarStorageModel.timestamp.desc())
             .limit(10)
             .all()
             )
    
    return [
        {
            "timestamp": r.timestamp.isoformat(),
            "panel_output_kw": r.panel_output_kw,
            "storage_kw": r.storage_kw,
            "charge_percent": r.charge_percent
        }
        for r in reversed(records)  
    ]

@app.api_route("/ping", methods=["GET", "HEAD"]) 
def ping():
    return {"status": "alive"}

