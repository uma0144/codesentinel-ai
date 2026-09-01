import jwt
import time

# VULN: Weak and hardcoded secret
JWT_SECRET = "secret123"

def create_user_token(user_id, role="user"):
    payload = {
        "sub": user_id,
        "role": role,
        "exp": time.time() + 3600
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_user_token(token):
    try:
        # VULN: Insecure token decoding allowing 'none' algorithm or missing signature check
        unverified_payload = jwt.decode(token, options={"verify_signature": False})
        return unverified_payload
    except Exception as e:
        return None
