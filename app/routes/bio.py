from fastapi import APIRouter, Request, HTTPException
from app.models.user import BioRequest
from app.core.auth import verify_jwt_token
from app.core.database import get_db_conn

router = APIRouter()

def get_current_user(request: Request):
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = auth_header.split(" ", 1)[1]
    payload = verify_jwt_token(token)
    return payload

@router.get("/bio")
def get_bio(request: Request):
    user = get_current_user(request)
    email = user["email"]
    name = user.get("name", "")
    conn = get_db_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT bio FROM users WHERE email=%s", (email,))
            row = cursor.fetchone()
            return {
                "bio": row["bio"] if row and row["bio"] else "",
                "email": email,
                "name": name
            }
    finally:
        conn.close()

@router.post("/bio")
def set_bio(request: Request, bio_req: BioRequest):
    user = get_current_user(request)
    email = user["email"]
    conn = get_db_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE users SET bio=%s WHERE email=%s", (bio_req.bio, email))
            conn.commit()
        return {"bio": bio_req.bio}
    finally:
        conn.close()
