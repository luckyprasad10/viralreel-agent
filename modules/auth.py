import hmac
import hashlib
import time
from typing import Optional
from config import (
    SESSION_SECRET_KEY, SESSION_MAX_AGE_SECONDS,
    DASHBOARD_USERNAME, DASHBOARD_PASSWORD
)

COOKIE_NAME = "viralreel_auth_session"

def _sign_payload(payload: str) -> str:
    return hmac.new(SESSION_SECRET_KEY.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()

def create_session_token(username: str) -> str:
    """Creates a cryptographically signed session token."""
    timestamp = int(time.time())
    payload = f"{username.strip()}:{timestamp}"
    sig = _sign_payload(payload)
    return f"{payload}:{sig}"

def verify_session_token(token: Optional[str]) -> bool:
    """Verifies that a session token is untampered and unexpired."""
    if not token or not isinstance(token, str):
        return False
    try:
        parts = token.split(":")
        if len(parts) != 3:
            return False
        username, timestamp_str, sig = parts
        timestamp = int(timestamp_str)
        
        # Check expiry
        if time.time() - timestamp > SESSION_MAX_AGE_SECONDS:
            return False
        
        # Constant-time comparison to prevent timing attacks
        expected_sig = _sign_payload(f"{username}:{timestamp}")
        return hmac.compare_digest(sig, expected_sig)
    except Exception:
        return False

def verify_credentials(username: str, password: str) -> bool:
    """
    Authenticates admin credentials.
    Supports master password check with user's configured handle or admin.
    """
    if not username or not password:
        return False

    valid_usernames = {
        DASHBOARD_USERNAME.lower().strip(),
        "admin",
        "lucky",
        "1lucky_24",
        "@1lucky_24"
    }

    user_match = username.lower().strip() in valid_usernames
    pass_match = hmac.compare_digest(password.strip(), DASHBOARD_PASSWORD.strip())
    return user_match and pass_match
