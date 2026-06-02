import jwt
import time
from config import CLIENT_ID, JWT_SECRET

def fake_login(user_id: str) -> str:
    payload = {
        "sub":       user_id,
        "client_id": CLIENT_ID,
        "iat":       int(time.time()),
        "exp":       int(time.time()) + 3600,
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    print(f"[AUTH] Token issued for {user_id}")
    return token

def validate_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        print(f"[AUTH] Valid — user: {payload['sub']}, client: {payload['client_id']}")
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")
