from sqlalchemy import Column, Float, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class SolarStorageModel(Base):
    __tablename__ = "solar_storage" # Change this to your actual table name if different
    id = Column(Integer, primary_key=True, index=True)
    panel_output_kw = Column(Float)
    storage_kw = Column(Float)
    charge_percent = Column(Float)



    # If your table has more columns, add them here to match your actual DB structure

    # --- Developer Notes ---
# . If you already have a database and table:
#    - Make sure __tablename__ matches your table name.
#    - Ensure the column names and types match your existing schema.
#
# . If using a different database (PostgreSQL, MySQL, etc.):
#    - Update your SQLAlchemy database URL accordingly in your main app.
#    - Install the appropriate DB driver (e.g., psycopg2 for PostgreSQL).