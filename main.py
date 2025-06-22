from fastapi import FastAPI, Query
from random import uniform
from schemas import SolarStorage
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, SolarStorageModel
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()
DEMO_MODE = True #set to false when going live


# 1. Change DATABASE_URL to point to your actual database.

DATABASE_URL = "sqlite:///./solar_storage.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# If you need to create the table in a new database, uncomment the next line:
# Base.metadata.create_all(bind=engine)

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

def get_solar_storage(specific_id: int = None):
    if DEMO_MODE:
        panel_output_kw = round(uniform(2.0, 6.0), 2)
        storage_kw = round(uniform(1.0, 5.0), 2)
        charge_percent = round((storage_kw / 5.0) * 100, 1)
        return SolarStorage(
            panel_output_kw=panel_output_kw,
            storage_kw=storage_kw,
            charge_percent=charge_percent
        )
    else:
        db = SessionLocal()
        if specific_id is not None:
            result = db.query(SolarStorageModel).filter(SolarStorageModel.id == specific_id).first()
        else:
            result = db.query(SolarStorageModel).order_by(SolarStorageModel.id.desc()).first()
        db.close()

        if result:
            return SolarStorage(
                panel_output_kw=result.panel_output_kw,
                storage_kw=result.storage_kw,
                charge_percent=result.charge_percent
        )
        else:
            return SolarStorage(
                panel_output_kw=0.0,
                storage_kw=0.0,
                charge_percent=0.0
        )
        
@app.get("/simulate",response_model=SolarStorage)
def simulate_storage(id: int = Query(default=None,
     description="Fetch by specific id if provided")):
    
    return get_solar_storage()

@app.get("/ping") # to keep the server running
def ping():
    return {"status": "alive"}


#Ensure your SolarStorageModel in models.py matches your actual table schema.
#Read all the comments in case of going live