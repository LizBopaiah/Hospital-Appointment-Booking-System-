from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Date, Time, Float, Enum, Boolean
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String) # 'doctor' or 'patient'
    security_question = Column(String)
    security_answer = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    doctor_profile = relationship("Doctor", back_populates="user", uselist=False)
    patient_profile = relationship("Patient", back_populates="user", uselist=False)

class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    full_name = Column(String)
    gender = Column(String)
    doctor_id = Column(String, unique=True)
    specialization = Column(String)
    experience = Column(Integer)
    qualification = Column(String)
    phone = Column(String)
    profile_image = Column(String, nullable=True)
    
    user = relationship("User", back_populates="doctor_profile")
    appointments = relationship("Appointment", back_populates="doctor")
    availabilities = relationship("DoctorAvailability", back_populates="doctor")

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    full_name = Column(String)
    gender = Column(String)
    age = Column(Integer)
    blood_group = Column(String)
    phone = Column(String)

    user = relationship("User", back_populates="patient_profile")
    appointments = relationship("Appointment", back_populates="patient")

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    patient_id = Column(Integer, ForeignKey("patients.id"))
    date = Column(Date)
    time_slot = Column(String) # e.g., "10:15 AM"
    status = Column(String, default="scheduled") # scheduled, cancelled, completed
    rating = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    doctor = relationship("Doctor", back_populates="appointments")
    patient = relationship("Patient", back_populates="appointments")

class DoctorAvailability(Base):
    __tablename__ = "doctor_availability"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    date = Column(Date) # Specific date
    start_time = Column(String) # e.g., "09:00"
    end_time = Column(String) # e.g., "12:00"

    doctor = relationship("Doctor", back_populates="availabilities")
