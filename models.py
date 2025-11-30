from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "app.db")

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    password = Column(String(200), nullable=False)

    fullname = Column(String(200), nullable=True)
    email = Column(String(200), unique=True, nullable=False)
    pref_travel_type = Column(String(50), nullable=True)
    pref_budget = Column(String(50), nullable=True)

    # OTP fields
    otp = Column(String(6), nullable=True)
    otp_expiry = Column(DateTime, nullable=True)

def init_db():
    Base.metadata.create_all(bind=engine)
