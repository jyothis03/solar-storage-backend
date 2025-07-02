from fastapi import FastAPI, Query, Depends
from random import uniform
from schemas import SolarStorage
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, SolarStorageModel
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime,timezone
from sqlalchemy.orm import Session

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

def get_solar_storage(specific_id: int = None, db : Session = None):
    if DEMO_MODE:
        panel_output_kw = round(uniform(2.0, 6.0), 2)
        storage_kw = round(uniform(1.0, 5.0), 2)
        charge_percent = round((storage_kw / 5.0) * 100, 1)
        return SolarStorage(
            panel_output_kw=panel_output_kw,
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
    db: Session = Depends(get_db)
):
    data = get_solar_storage(specific_id=id, db=db)

    if DEMO_MODE:
        # First adjust panel output for system loss
        adjusted_panel_output = data.panel_output_kw * ((100 - loss_factor) / 100)

        # Add your location adjustment **right here**
        if location.lower() == "kerala":
            irradiance_factor = 1.05  # example: slightly higher
        elif location.lower() == "delhi":
            irradiance_factor = 0.95  # example: slightly lower
        else:
            irradiance_factor = 1.0

        adjusted_panel_output *= irradiance_factor

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
            timestamp=datetime.now(timezone.utc)
        )
        db.add(record)
        db.commit()

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

