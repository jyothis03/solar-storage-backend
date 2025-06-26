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

DATABASE_URL = "postgresql://jyothis:jCJCnWNjuZLglDpts98mP4AUzHhAiAjF@dpg-d1declm3jp1c73f10470-a/solar_storage"
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
       allow_origins=["*"],  # Update this with your allowed origins in production
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
        
@app.get("/simulate",response_model=SolarStorage)
def simulate_storage(id: int = Query(default=None,
     description="Fetch by specific id if provided"),
     db: Session = Depends(get_db)):
    
    data=get_solar_storage(specific_id=id, db=db)
    if DEMO_MODE:
        
        record=SolarStorageModel(
            panel_output_kw=data.panel_output_kw,
            storage_kw=data.storage_kw,
            charge_percent=data.charge_percent,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(record)
        db.commit()

    return data


@app.api_route("/ping", methods=["GET", "HEAD"]) # to keep the server running
def ping():
    return {"status": "alive"}


#Ensure your SolarStorageModel in models.py matches your actual table schema.
#Read all the comments in case of going live