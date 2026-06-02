from fastapi import FastAPI, Depends, HTTPException, status, Request, Form, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
import models, database, auth, schemas
import os
import shutil
from datetime import datetime, timedelta

app = FastAPI()

# Create database tables
models.Base.metadata.create_all(bind=database.engine)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates setup
templates = Jinja2Templates(directory="templates")

# --- UI ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html")

@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    return templates.TemplateResponse(request, "forgot_password.html")

# Helper to get the user for UI routes, catching any credentials exception and returning None to trigger a redirect
def get_current_user_ui(request: Request, db: Session = Depends(database.get_db)):
    try:
        return auth.get_current_user(request, db)
    except HTTPException:
        return None

@app.get("/patient/dashboard", response_class=HTMLResponse)
async def patient_dashboard(request: Request, user: models.User = Depends(get_current_user_ui)):
    if not user or user.role != "patient":
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request, "patient_dashboard.html", {"user": user})

@app.get("/doctor/dashboard", response_class=HTMLResponse)
async def doctor_dashboard(request: Request, user: models.User = Depends(get_current_user_ui)):
    if not user or user.role != "doctor":
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request, "doctor_dashboard.html", {"user": user})

# --- API ROUTES ---

@app.post("/api/register/doctor")
async def register_doctor(
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    security_question: str = Form(...),
    security_answer: str = Form(...),
    full_name: str = Form(...),
    gender: str = Form(...),
    doctor_id: str = Form(...),
    specialization: str = Form(...),
    experience: int = Form(...),
    qualification: str = Form(...),
    phone: str = Form(...),
    profile_image: UploadFile = File(None),
    db: Session = Depends(database.get_db)
):
    if password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    # Check if user exists
    existing_user = db.query(models.User).filter(models.User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create User
    hashed_pw = auth.get_password_hash(password)
    new_user = models.User(
        email=email,
        hashed_password=hashed_pw,
        role="doctor",
        security_question=security_question,
        security_answer=security_answer
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Handle image upload
    image_path = None
    if profile_image and profile_image.filename:
        file_ext = profile_image.filename.split(".")[-1]
        file_name = f"doctor_{new_user.id}.{file_ext}"
        image_path = f"uploads/{file_name}"
        with open(f"static/{image_path}", "wb") as buffer:
            shutil.copyfileobj(profile_image.file, buffer)
    else:
        # Default avatars
        if gender.lower() == "male":
            image_path = "img/male_avatar.png"
        else:
            image_path = "img/female_avatar.png"

    # Create Doctor Profile
    new_doctor = models.Doctor(
        user_id=new_user.id,
        full_name=full_name,
        gender=gender,
        doctor_id=doctor_id,
        specialization=specialization,
        experience=experience,
        qualification=qualification,
        phone=phone,
        profile_image=image_path
    )
    db.add(new_doctor)
    db.commit()

    # Auto-login: Create token
    access_token = auth.create_access_token(data={"sub": email})
    response = RedirectResponse(url="/doctor/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

@app.post("/api/register/patient")
async def register_patient(
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    security_question: str = Form(...),
    security_answer: str = Form(...),
    full_name: str = Form(...),
    gender: str = Form(...),
    age: int = Form(...),
    blood_group: str = Form(...),
    phone: str = Form(...),
    db: Session = Depends(database.get_db)
):
    if password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    # Check if user exists
    existing_user = db.query(models.User).filter(models.User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create User
    hashed_pw = auth.get_password_hash(password)
    new_user = models.User(
        email=email,
        hashed_password=hashed_pw,
        role="patient",
        security_question=security_question,
        security_answer=security_answer
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create Patient Profile
    new_patient = models.Patient(
        user_id=new_user.id,
        full_name=full_name,
        gender=gender,
        age=age,
        blood_group=blood_group,
        phone=phone
    )
    db.add(new_patient)
    db.commit()

    # Auto-login: Create token
    access_token = auth.create_access_token(data={"sub": email})
    response = RedirectResponse(url="/patient/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

@app.post("/api/login")
async def login(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(database.get_db)
):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not auth.verify_password(password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = auth.create_access_token(data={"sub": email})
    
    # Redirect based on role
    target_url = "/doctor/dashboard" if user.role == "doctor" else "/patient/dashboard"
    response = RedirectResponse(url=target_url, status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response

# --- FORGOT PASSWORD APIs ---

@app.get("/api/forgot-password/question")
async def get_security_question(email: str, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    questions_map = {
        "nickname": "What is your childhood nickname?",
        "school": "What was your first school name?",
        "food": "What is your favorite food?",
        "pet": "What is your pet’s name?",
        "mother": "What is your mother’s maiden name?"
    }
    question_text = questions_map.get(user.security_question, "Security Question")
    return {"question": question_text}

@app.post("/api/forgot-password/verify")
async def verify_security_answer(data: dict, db: Session = Depends(database.get_db)):
    email = data.get("email")
    answer = data.get("answer")
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or user.security_answer.lower() != answer.lower():
        raise HTTPException(status_code=400, detail="Incorrect answer")
    return {"status": "success"}

@app.post("/api/forgot-password/reset")
async def reset_password(data: dict, db: Session = Depends(database.get_db)):
    email = data.get("email")
    new_password = data.get("new_password")
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.hashed_password = auth.get_password_hash(new_password)
    db.commit()
    return {"status": "success"}

# --- PATIENT & DOCTOR SHARED APIs ---

@app.get("/api/user/me")
async def get_me(user: models.User = Depends(auth.get_current_user)):
    if not user: raise HTTPException(status_code=401)
    
    profile = user.patient_profile if user.role == 'patient' else user.doctor_profile
    data = {
        "email": user.email,
        "role": user.role,
        "full_name": profile.full_name,
        "phone": profile.phone
    }
    if user.role == 'patient':
        data["age"] = profile.age
        data["blood_group"] = profile.blood_group
        data["gender"] = profile.gender
    else:
        data["specialization"] = profile.specialization
        data["experience"] = profile.experience
        data["qualification"] = profile.qualification
        data["gender"] = profile.gender
        data["profile_image"] = profile.profile_image
    return data

@app.get("/api/doctors")
async def list_doctors(query: str = "", specialization: str = "", db: Session = Depends(database.get_db)):
    doctors = db.query(models.Doctor)
    if query:
        doctors = doctors.filter(models.Doctor.full_name.contains(query))
    if specialization:
        doctors = doctors.filter(models.Doctor.specialization == specialization)
    return doctors.all()

@app.get("/api/doctor/{doctor_id}/slots")
async def get_doctor_slots(doctor_id: int, date: str, db: Session = Depends(database.get_db)):
    # Fetch doctor's availability for the specific date
    avail = db.query(models.DoctorAvailability).filter(
        models.DoctorAvailability.doctor_id == doctor_id,
        models.DoctorAvailability.date == datetime.strptime(date, "%Y-%m-%d").date()
    ).first()
    
    if not avail:
        return []

    # Generate 15-minute slots between start and end time
    start = datetime.strptime(avail.start_time, "%H:%M")
    end = datetime.strptime(avail.end_time, "%H:%M")
    
    slots = []
    current = start
    while current < end:
        slots.append(current.strftime("%I:%M %p"))
        current += timedelta(minutes=15)
    
    # Check booked slots
    booked = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == doctor_id,
        models.Appointment.date == datetime.strptime(date, "%Y-%m-%d").date(),
        models.Appointment.status == "scheduled"
    ).all()
    
    booked_slots = [a.time_slot for a in booked]
    available_slots = [s for s in slots if s not in booked_slots]
    return available_slots

@app.get("/api/doctor/{doctor_id}/available-dates")
async def get_available_dates(doctor_id: int, db: Session = Depends(database.get_db)):
    availabilities = db.query(models.DoctorAvailability).filter(
        models.DoctorAvailability.doctor_id == doctor_id,
        models.DoctorAvailability.date >= datetime.now().date()
    ).all()
    return [a.date.strftime("%Y-%m-%d") for a in availabilities]

@app.post("/api/appointments/book")
async def book_appointment(data: dict, user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if not user or user.role != 'patient': raise HTTPException(status_code=401)
    
    doctor = db.query(models.Doctor).filter(models.Doctor.id == data['doctor_id']).first()
    if not doctor: raise HTTPException(status_code=404)

    # Prevent double booking
    existing = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == data['doctor_id'],
        models.Appointment.date == datetime.strptime(data['date'], "%Y-%m-%d").date(),
        models.Appointment.time_slot == data['time_slot'],
        models.Appointment.status == "scheduled"
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Slot already booked")
        
    new_app = models.Appointment(
        doctor_id=data['doctor_id'],
        patient_id=user.patient_profile.id,
        date=datetime.strptime(data['date'], "%Y-%m-%d").date(),
        time_slot=data['time_slot']
    )
    db.add(new_app)
    db.commit()



    return {"status": "success"}

@app.get("/api/patient/appointments")
async def get_patient_appointments(user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if not user or user.role != 'patient': raise HTTPException(status_code=401)
    
    appointments = db.query(models.Appointment).filter(models.Appointment.patient_id == user.patient_profile.id).all()
    result = []
    for app in appointments:
        result.append({
            "id": app.id,
            "doctor_name": app.doctor.full_name,
            "date": app.date.strftime("%Y-%m-%d"),
            "time_slot": app.time_slot,
            "status": app.status
        })
    return result

@app.get("/api/doctor/appointments")
async def get_doctor_appointments(user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if not user or user.role != 'doctor': raise HTTPException(status_code=401)
    
    appointments = db.query(models.Appointment).filter(models.Appointment.doctor_id == user.doctor_profile.id).all()
    result = []
    for app in appointments:
        result.append({
            "id": app.id,
            "patient_name": app.patient.full_name,
            "patient_age": app.patient.age,
            "date": app.date.strftime("%Y-%m-%d"),
            "time_slot": app.time_slot,
            "status": app.status
        })
    return result

@app.post("/api/appointments/{app_id}/cancel")
async def cancel_appointment(app_id: int, user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if not user: raise HTTPException(status_code=401)
    
    appointment = db.query(models.Appointment).filter(models.Appointment.id == app_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Check authorization
    if user.role == 'patient':
        if not user.patient_profile or appointment.patient_id != user.patient_profile.id:
            raise HTTPException(status_code=403, detail="Not authorized to cancel this appointment")
    elif user.role == 'doctor':
        if not user.doctor_profile or appointment.doctor_id != user.doctor_profile.id:
            raise HTTPException(status_code=403, detail="Not authorized to cancel this appointment")
            
    if appointment.status != "scheduled":
        raise HTTPException(status_code=400, detail=f"Appointment cannot be cancelled as it is already {appointment.status}")

    appointment.status = "cancelled"
    db.commit()
    return {"status": "success"}

# --- DOCTOR AVAILABILITY APIs ---

@app.post("/api/doctor/availability")
async def add_availability(data: dict, user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if not user or user.role != 'doctor': raise HTTPException(status_code=401)
    
    new_avail = models.DoctorAvailability(
        doctor_id=user.doctor_profile.id,
        date=datetime.strptime(data['date'], "%Y-%m-%d").date(),
        start_time=data['start_time'],
        end_time=data['end_time']
    )
    db.add(new_avail)
    db.commit()
    return {"status": "success"}

@app.get("/api/doctor/availability")
async def get_my_availability(user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if not user or user.role != 'doctor': raise HTTPException(status_code=401)
    availabilities = db.query(models.DoctorAvailability).filter(models.DoctorAvailability.doctor_id == user.doctor_profile.id).order_by(models.DoctorAvailability.date).all()
    return [{"id": a.id, "date": a.date.strftime("%Y-%m-%d"), "start_time": a.start_time, "end_time": a.end_time} for a in availabilities]

@app.delete("/api/doctor/availability/{id}")
async def delete_availability(id: int, user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if not user or user.role != 'doctor': raise HTTPException(status_code=401)
    avail = db.query(models.DoctorAvailability).filter(models.DoctorAvailability.id == id, models.DoctorAvailability.doctor_id == user.doctor_profile.id).first()
    if avail:
        db.delete(avail)
        db.commit()
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    import webbrowser
    import threading
    import os

    def open_browser():
        webbrowser.open("http://127.0.0.1:8000")

    # Only open browser on initial launch, not on reload restarts
    if os.environ.get("BROWSER_OPENED") != "true":
        os.environ["BROWSER_OPENED"] = "true"
        threading.Timer(1.5, open_browser).start()

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
