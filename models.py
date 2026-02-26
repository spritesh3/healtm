from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from database import Base


# ================= USER MODEL =================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="patient")  # patient / doctor / admin

    created_at = Column(DateTime, default=datetime.utcnow)


# ================= CONSULTATION MODEL =================
class Consultation(Base):
    __tablename__ = "consultations"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False, index=True)
    question = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)


# ================= LONGITUDINAL PATIENT MEMORY =================
class PatientMemory(Base):
    __tablename__ = "patient_memory"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)

    medical_summary = Column(Text, default="")
    symptoms = Column(Text, default="")
    risk_flags = Column(String(20), default="Low")

    last_updated = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow  # Auto update when record changes
    )
