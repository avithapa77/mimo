"""
create_test_user.py — Create a Firebase test user and print their UID

Run once:
    python create_test_user.py
"""

import firebase_admin
from firebase_admin import credentials, auth
from config import FIREBASE_SERVICE_ACCOUNT

if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT)
    firebase_admin.initialize_app(cred)

user = auth.create_user(
    email="testuser@malati.com",
    password="testpassword123",
    display_name="Hari Prasad"
)

print(f"Created user!")
print(f"UID: {user.uid}")
print(f"Email: {user.email}")
