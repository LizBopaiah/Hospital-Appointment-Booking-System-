import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from app import app
import models
import auth

# Use a file-based SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_hospital.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def run_around_tests():
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop tables
    Base.metadata.drop_all(bind=engine)
    # Remove file
    if os.path.exists("./test_hospital.db"):
        try:
            os.remove("./test_hospital.db")
        except Exception:
            pass

client = TestClient(app)

def test_register_patient_redirects_to_dashboard():
    # 1. Register Patient
    payload = {
        "email": "patient@test.com",
        "password": "password123",
        "confirm_password": "password123",
        "security_question": "food",
        "security_answer": "pizza",
        "full_name": "John Doe",
        "gender": "male",
        "age": 30,
        "blood_group": "O+",
        "phone": "1234567890"
    }
    response = client.post("/api/register/patient", data=payload, follow_redirects=False)
    
    # Check redirect status code
    assert response.status_code == 303
    assert response.headers["location"] == "/patient/dashboard"
    
    # Check if access_token cookie is set
    cookies = response.cookies
    assert "access_token" in cookies
    token = cookies["access_token"]
    if token.startswith('"') and token.endswith('"'):
        token = token[1:-1]
    assert token.startswith("Bearer ")

def test_register_doctor_redirects_to_dashboard():
    # 2. Register Doctor
    payload = {
        "email": "doctor@test.com",
        "password": "password123",
        "confirm_password": "password123",
        "security_question": "school",
        "security_answer": "high school",
        "full_name": "Dr. Smith",
        "gender": "female",
        "doctor_id": "DOC001",
        "specialization": "Cardiology",
        "experience": 10,
        "qualification": "MD",
        "phone": "9876543210"
    }
    response = client.post("/api/register/doctor", data=payload, follow_redirects=False)
    
    assert response.status_code == 303
    assert response.headers["location"] == "/doctor/dashboard"
    
    cookies = response.cookies
    assert "access_token" in cookies
    token = cookies["access_token"]
    if token.startswith('"') and token.endswith('"'):
        token = token[1:-1]
    assert token.startswith("Bearer ")

def test_login_redirects_to_dashboard():
    # First register a patient and a doctor
    # Patient registration
    client.post("/api/register/patient", data={
        "email": "patient@test.com",
        "password": "password123",
        "confirm_password": "password123",
        "security_question": "food",
        "security_answer": "pizza",
        "full_name": "John Doe",
        "gender": "male",
        "age": 30,
        "blood_group": "O+",
        "phone": "1234567890"
    })
    
    # Doctor registration
    client.post("/api/register/doctor", data={
        "email": "doctor@test.com",
        "password": "password123",
        "confirm_password": "password123",
        "security_question": "school",
        "security_answer": "high school",
        "full_name": "Dr. Smith",
        "gender": "female",
        "doctor_id": "DOC001",
        "specialization": "Cardiology",
        "experience": 10,
        "qualification": "MD",
        "phone": "9876543210"
    })
    
    # Log in as patient
    response = client.post("/api/login", data={
        "email": "patient@test.com",
        "password": "password123"
    }, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/patient/dashboard"
    assert "access_token" in response.cookies
    
    # Log in as doctor
    response = client.post("/api/login", data={
        "email": "doctor@test.com",
        "password": "password123"
    }, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/doctor/dashboard"
    assert "access_token" in response.cookies

def test_dashboard_access_control():
    # 1. Patient client
    patient_client = TestClient(app)
    patient_client.post("/api/register/patient", data={
        "email": "patient@test.com",
        "password": "password123",
        "confirm_password": "password123",
        "security_question": "food",
        "security_answer": "pizza",
        "full_name": "John Doe",
        "gender": "male",
        "age": 30,
        "blood_group": "O+",
        "phone": "1234567890"
    })

    # 2. Doctor client
    doctor_client = TestClient(app)
    doctor_client.post("/api/register/doctor", data={
        "email": "doctor@test.com",
        "password": "password123",
        "confirm_password": "password123",
        "security_question": "school",
        "security_answer": "high school",
        "full_name": "Dr. Smith",
        "gender": "female",
        "doctor_id": "DOC001",
        "specialization": "Cardiology",
        "experience": 10,
        "qualification": "MD",
        "phone": "9876543210"
    })

    # 3. Guest client (no authentication)
    guest_client = TestClient(app)

    # 1. Patient dashboard with patient client -> 200 OK
    response = patient_client.get("/patient/dashboard", follow_redirects=False)
    print("Patient dashboard with patient client status:", response.status_code)
    assert response.status_code == 200

    # 2. Patient dashboard with doctor client -> Redirect to /login
    response = doctor_client.get("/patient/dashboard", follow_redirects=False)
    print("Patient dashboard with doctor client status:", response.status_code)
    assert response.status_code in [302, 303, 307]
    assert response.headers["location"] == "/login"

    # 3. Patient dashboard with guest client -> Redirect to /login
    response = guest_client.get("/patient/dashboard", follow_redirects=False)
    print("Patient dashboard with guest client status:", response.status_code)
    assert response.status_code in [302, 303, 307]
    assert response.headers["location"] == "/login"

    # 4. Doctor dashboard with doctor client -> 200 OK
    response = doctor_client.get("/doctor/dashboard", follow_redirects=False)
    print("Doctor dashboard with doctor client status:", response.status_code)
    assert response.status_code == 200

    # 5. Doctor dashboard with patient client -> Redirect to /login
    response = patient_client.get("/doctor/dashboard", follow_redirects=False)
    print("Doctor dashboard with patient client status:", response.status_code)
    assert response.status_code in [302, 303, 307]
    assert response.headers["location"] == "/login"

    # 6. Doctor dashboard with guest client -> Redirect to /login
    response = guest_client.get("/doctor/dashboard", follow_redirects=False)
    print("Doctor dashboard with guest client status:", response.status_code)
    assert response.status_code in [302, 303, 307]
    assert response.headers["location"] == "/login"

def test_dashboard_with_invalid_cookie_redirects():
    invalid_client = TestClient(app)
    invalid_client.cookies.set("access_token", "Bearer invalidtoken12345", domain="testserver")
    
    # Try accessing patient dashboard
    response = invalid_client.get("/patient/dashboard", follow_redirects=False)
    print("Invalid token response:", response.status_code)
    
    assert response.status_code in [302, 303, 307]
    assert response.headers["location"] == "/login"
