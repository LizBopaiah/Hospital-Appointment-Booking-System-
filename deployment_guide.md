# Deployment & Setup Guide - MediBook Hospital System

This document explains how to set up, run, and deploy the Hospital Appointment Booking System.

## 1. Local Setup
### Prerequisites
- Python 3.8 or higher (Tested on 3.13)
- Pip

### Installation
1. Clone or download the project files.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python app.py
   ```
4. Open your browser and go to `http://localhost:8000`.

## 2. Environment Variables
For production, you should create a `.env` file or set environment variables for:
- `SECRET_KEY`: A long random string for JWT signing.

## 3. Database
The system uses **SQLite** (`hospital.db`), which is a single-file database. 
- For local development, no setup is needed.
- For production (e.g., GCP), you can stick with SQLite if traffic is low, or migrate to PostgreSQL by updating the `SQLALCHEMY_DATABASE_URL` in `database.py`.

## 4. Cloud Deployment (GCP & Cloud Functions)
Since this is a FastAPI app, it can be deployed as:
- **Google Cloud Run**: (Recommended) Package it into a Docker container and deploy.
- **Cloud Functions**: Wrap the FastAPI app with `mangum` or use the standard Python runtime.

### Steps for Cloud Run:
1. Create a `Dockerfile`:
   ```dockerfile
   FROM python:3.13-slim
   WORKDIR /app
   COPY . .
   RUN pip install -r requirements.txt
   CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
   ```
2. Build and push to Artifact Registry.
3. Deploy to Cloud Run.

## 5. Technology Stack Summary
- **Frontend**: Vanilla HTML5, CSS3, JavaScript (Fetch API).
- **Backend**: FastAPI (Python).
- **Database**: SQLite (SQLAlchemy ORM).
- **Authentication**: JWT (JSON Web Tokens) with Cookie storage.
- **Security**: Password hashing with `bcrypt`.

