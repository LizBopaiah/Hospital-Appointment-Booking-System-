import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def login(email, password):
    print(f"Logging in as {email}...")
    data = {"email": email, "password": password}
    response = requests.post(f"{BASE_URL}/api/login", data=data)
    if response.status_code == 200 or response.history:
        print("Login Successful")
        return response.cookies.get_dict()
    else:
        print(f"Login Failed: {response.text}")
        return None

def register_doctor():
    print("Registering Doctor...")
    data = {
        "full_name": "Dr. Smith",
        "gender": "Male",
        "doctor_id": "DOC001",
        "specialization": "Cardiologist",
        "experience": 10,
        "qualification": "MBBS, MD",
        "phone": "1234567890",
        "email": "drsmith@example.com",
        "password": "password123",
        "confirm_password": "password123",
        "security_question": "nickname",
        "security_answer": "Smithy"
    }
    response = requests.post(f"{BASE_URL}/api/register/doctor", data=data)
    if response.status_code == 200 or response.history:
        print("Doctor Registration Successful")
        return response.cookies.get_dict()
    else:
        print(f"Doctor Registration Failed: {response.text}")
        return None

def add_availability(cookies):
    print("\nAdding Availability...")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    data = {
        "date": tomorrow,
        "start_time": "09:00",
        "end_time": "12:00"
    }
    response = requests.post(f"{BASE_URL}/api/doctor/availability", json=data, cookies=cookies)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    return tomorrow

def register_patient():
    print("\nRegistering Patient...")
    data = {
        "full_name": "Alice Doe",
        "gender": "Female",
        "age": 25,
        "blood_group": "A+",
        "phone": "9876543210",
        "email": "alice@example.com",
        "password": "password123",
        "confirm_password": "password123",
        "security_question": "food",
        "security_answer": "Pizza"
    }
    response = requests.post(f"{BASE_URL}/api/register/patient", data=data)
    if response.status_code == 200 or response.history:
        print("Patient Registration Successful")
        return response.cookies.get_dict()
    else:
        print(f"Patient Registration Failed: {response.text}")
        # Try login if already registered
        return login("alice@example.com", "password123")

def book_appointment(patient_cookies, date):
    print("\nBooking Appointment...")
    # Get doctor ID first
    resp = requests.get(f"{BASE_URL}/api/doctors", cookies=patient_cookies)
    doctors = resp.json()
    doctor_id = None
    for d in doctors:
        if d['full_name'] == "Dr. Smith":
            doctor_id = d['id']
            break
    
    if not doctor_id:
        print("Doctor not found!")
        return

    # Get available slots
    resp = requests.get(f"{BASE_URL}/api/doctor/{doctor_id}/slots?date={date}", cookies=patient_cookies)
    slots = resp.json()
    if not slots:
        print(f"No slots available for {date}")
        return
    
    slot = slots[0]
    print(f"Booking slot {slot} on {date} with Doctor ID {doctor_id}")
    
    data = {
        "doctor_id": doctor_id,
        "date": date,
        "time_slot": slot
    }
    response = requests.post(f"{BASE_URL}/api/appointments/book", json=data, cookies=patient_cookies)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    # Doctor Flow
    doctor_cookies = login("drsmith@example.com", "password123")
    if not doctor_cookies:
        doctor_cookies = register_doctor()
    
    if doctor_cookies:
        date = add_availability(doctor_cookies)
        
        # Patient Flow
        patient_cookies = register_patient()
        if patient_cookies:
            book_appointment(patient_cookies, date)
