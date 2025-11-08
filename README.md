add first user

python
from werkzeug.security import generate_password_hash
from db import SessionLocal
from models.employee import Employee

session = SessionLocal()

email = "admin@example.com"
plain_password = "AdminPass123!"

existing = session.query(Employee).filter_by(email=email).first()
if existing:
    print("User already exists:", existing.id, existing.email)
else:
    hashed = generate_password_hash(plain_password)
    user = Employee(email=email, password_hash=hashed, is_admin=True)
    session.add(user)
    session.commit()
    print("Created user id:", user.id, "email:", user.email)

session.close()