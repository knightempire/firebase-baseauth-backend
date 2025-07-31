from fastapi import APIRouter, Response, HTTPException
from firebase_admin import auth as firebase_auth
from app.models.user import TokenRequest, UserInfo
from app.core.auth import create_access_token, create_refresh_token
from app.core.database import get_db_conn

router = APIRouter()

@router.post("/login", response_model=UserInfo)
def login(token_req: TokenRequest, response: Response):
    try:
        decoded = firebase_auth.verify_id_token(token_req.idToken)
        email = decoded.get("email")
        name = decoded.get("name", "")
        if not email:
            raise HTTPException(status_code=401, detail="Email not found in Firebase token")
        access_token = create_access_token({"email": email, "name": name})
        refresh_token = create_refresh_token({"email": email, "name": name})
        response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=True, samesite="lax", max_age=2*60)
        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (email, name) VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE name=VALUES(name)
                """, (email, name))
                conn.commit()
        finally:
            conn.close()
        return {"email": email, "name": name, "accessToken": access_token}
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid Firebase token")
