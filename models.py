from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
    role = Column(String)  # patient / doctor / admin


class Consultation(Base):
    __tablename__ = "consultations"

    id = Column(Integer, primary_key=True)
    username = Column(String)
    question = Column(Text)
    ai_response = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class PatientMemory(Base):
    __tablename__ = "patient_memory"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    medical_summary = Column(Text)
    symptoms = Column(Text)
    risk_flags = Column(String)
    last_updated = Column(DateTime, default=datetime.utcnow)
