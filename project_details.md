# Hospital Appointment Booking System - Project Details

## 1. Introduction
The Hospital Appointment Booking System is a comprehensive web-based application designed to bridge the gap between patients and healthcare professionals. The primary goal of the system is to digitize and streamline the process of scheduling medical appointments, reducing wait times, and improving the overall patient experience. 

The system features two main user roles:
- **Patients**: Can register, browse available doctors by specialization, view doctor availability, and book or cancel appointments seamlessly.
- **Doctors**: Can register with their credentials, manage their daily availability schedules, and monitor their upcoming patient appointments.

By providing a centralized platform, the application ensures that healthcare services are more accessible and manageable for both providers and receivers.

## 2. Methodology & Architecture
The project is built using a monolithic architecture that tightly integrates the backend API with server-side rendered frontend templates. 

### 2.1 Backend Design
- **RESTful API**: The backend exposes RESTful endpoints built with FastAPI, ensuring high performance and fast request processing.
- **ORM Integration**: The system uses SQLAlchemy as an Object-Relational Mapper (ORM) to interact with the relational database. This abstracts raw SQL queries into Python objects, improving code maintainability and security against SQL injection.
- **Authentication & Authorization**: The application utilizes JSON Web Tokens (JWT) for secure authentication. Upon successful login, a JWT is generated and stored in an `HttpOnly` cookie to protect against Cross-Site Scripting (XSS) attacks. Passwords are never stored in plain text; they are hashed using `bcrypt` before being saved to the database.
- **Password Recovery**: A security question mechanism is implemented to allow users to reset their passwords securely without relying on an external email service.

### 2.2 Frontend Design
- **Server-Side Rendering**: The UI is rendered dynamically on the server using Jinja2 templates. This approach allows the backend to inject contextual data (like user profiles or doctor lists) directly into the HTML before sending it to the client.
- **Responsive Layouts**: The frontend utilizes HTML and CSS to create responsive dashboards tailored to the specific needs of patients and doctors.

## 3. Technology Stack

### Backend
- **Python**: The core programming language used for backend logic.
- **FastAPI**: A modern, fast (high-performance) web framework for building APIs with Python based on standard Python type hints.
- **Uvicorn**: An ASGI web server implementation for Python used to run the FastAPI application.

### Database
- **SQLite**: A lightweight, disk-based database used for persistent data storage (`hospital.db`).
- **SQLAlchemy**: The Python SQL toolkit and Object Relational Mapper.

### Security & Authentication
- **python-jose[cryptography]**: Used for generating and verifying JSON Web Tokens (JWT).
- **bcrypt**: A password-hashing function used to securely store user passwords.

### Frontend
- **Jinja2**: A modern and designer-friendly templating language for Python used to render HTML pages.
- **HTML5 & CSS3**: Core technologies for structuring and styling the user interfaces.
- **JavaScript (Vanilla)**: Used for client-side interactivity and asynchronous API calls.

## 4. Key Features
1. **Role-Based Access Control (RBAC)**: Secure routing and data access based on whether the logged-in user is a patient or a doctor.
2. **Doctor Availability Management**: Doctors can dynamically open 15-minute time slots for specific dates.
3. **Smart Scheduling**: The system automatically calculates available 15-minute slots based on the doctor's start and end times, filtering out already booked slots to prevent double-booking.
4. **File Handling**: Support for uploading and storing doctor profile images locally.
5. **Session Management**: Secure session management using HTTP-only cookies to handle user states across the application seamlessly.
