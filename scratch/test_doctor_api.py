from fastapi.testclient import TestClient
from app import app
import database, models, auth

client = TestClient(app)

db = next(database.get_db())
user = db.query(models.User).filter(models.User.email == 'teen@gmail.com').first()

def mock_get_current_user():
    return user

app.dependency_overrides[auth.get_current_user] = mock_get_current_user

res = client.get("/api/doctor/appointments")
print("Status:", res.status_code)
print("Body:", res.text)
