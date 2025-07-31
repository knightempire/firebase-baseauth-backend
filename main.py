import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status, Request, Response, Cookie
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
import pymysql
import jwt
from datetime import datetime, timedelta
from typing import Optional
JWT_SECRET = os.environ.get("JWT_SECRET", "supersecretkey")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_SECONDS = int(os.environ.get("ACCESS_TOKEN_EXPIRE_SECONDS", 10))
REFRESH_TOKEN_EXPIRE_MINUTES = int(os.environ.get("REFRESH_TOKEN_EXPIRE_MINUTES", 2))
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(seconds=ACCESS_TOKEN_EXPIRE_SECONDS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str, refresh: bool = False):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if refresh and payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")


# Load environment variables from .env if present (force absolute path)
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

# Initialize Firebase Admin from environment variables
firebase_cred_dict = {
    "type": os.environ.get("FIREBASE_TYPE"),
    "project_id": os.environ.get("FIREBASE_PROJECT_ID"),
    "private_key_id": os.environ.get("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.environ.get("FIREBASE_PRIVATE_KEY").replace('\\n', '\n') if os.environ.get("FIREBASE_PRIVATE_KEY") else None,
    "client_email": os.environ.get("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.environ.get("FIREBASE_CLIENT_ID"),
    "auth_uri": os.environ.get("FIREBASE_AUTH_URI"),
    "token_uri": os.environ.get("FIREBASE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.environ.get("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.environ.get("FIREBASE_CLIENT_X509_CERT_URL"),
    "universe_domain": os.environ.get("FIREBASE_UNIVERSE_DOMAIN"),
}
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_cred_dict)
    firebase_admin.initialize_app(cred)



# Load environment variables from .env if present (force absolute path)
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)
missing_vars = []
for var in ["CLOUDSQL_HOST", "CLOUDSQL_USER", "CLOUDSQL_PASSWORD", "CLOUDSQL_DB"]:
    if not os.environ.get(var):
        missing_vars.append(var)
if missing_vars:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing_vars)}. Check your .env file or environment.")
DB_HOST = os.environ["CLOUDSQL_HOST"]
DB_USER = os.environ["CLOUDSQL_USER"]
DB_PASSWORD = os.environ["CLOUDSQL_PASSWORD"]
DB_NAME = os.environ["CLOUDSQL_DB"]



def get_db_conn():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )


app = FastAPI()

# Base endpoint for health check
@app.get("/")
def root():
    msg = "hi dev"
    try:
        conn = get_db_conn()
        conn.close()
        db_status = "connected"
    except Exception:
        db_status = "not connected"
    return {"message": msg, "db": db_status}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


class TokenRequest(BaseModel):
    idToken: str

class BioRequest(BaseModel):
    bio: str

class UserInfo(BaseModel):
    email: str
    name: str = ""
    accessToken: str

@app.post("/login", response_model=UserInfo)
def login(token_req: TokenRequest, response: Response):
    try:
        decoded = firebase_auth.verify_id_token(token_req.idToken)
        email = decoded.get("email")
        name = decoded.get("name", "")
        if not email:
            raise HTTPException(status_code=401, detail="Email not found in Firebase token")
        # Issue tokens
        access_token = create_access_token({"email": email, "name": name})
        refresh_token = create_refresh_token({"email": email, "name": name})
        # Set refresh token as HttpOnly cookie
        print(f"[DEBUG] Setting refresh_token cookie for user: {email}")
        response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=True, samesite="lax", max_age=REFRESH_TOKEN_EXPIRE_MINUTES*60)
        # Upsert user in DB
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
        response_data = {"email": email, "name": name, "accessToken": access_token}
        print(f"[DEBUG] /login response: {response_data}")
        return response_data
    except Exception as e:
        print(f"[DEBUG] Firebase token validation error: {e}")
        raise HTTPException(status_code=401, detail="Invalid Firebase token")


@app.get("/users")
def list_users():
    conn = get_db_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT email, name FROM users")
            return cursor.fetchall()
    finally:
        conn.close()

# --- JWT-protected endpoints ---
def get_current_user(request: Request):
    auth_header = request.headers.get("authorization")
    print(f"[DEBUG] /bio called. Authorization header: {auth_header}")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = auth_header.split(" ", 1)[1]
    print(f"[DEBUG] Access token received: {token}")
    payload = verify_jwt_token(token)
    print(f"[DEBUG] Decoded token payload: {payload}")
    return payload

@app.get("/bio")
def get_bio(request: Request):
    print("[DEBUG] /bio endpoint called")
    user = get_current_user(request)
    email = user["email"]
    name = user.get("name", "")
    print(f"[DEBUG] /bio for user: {email}")
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

@app.post("/bio")
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

@app.post("/refresh")
def refresh_token(response: Response, refresh_token: Optional[str] = Cookie(None)):
    print("[DEBUG] /refresh endpoint called")
    if not refresh_token:
        print("[DEBUG] /refresh: No refresh token provided")
        raise HTTPException(status_code=401, detail="Missing refresh token")
    try:
        payload = verify_jwt_token(refresh_token, refresh=True)
        email = payload["email"]
        name = payload.get("name", "")
        print(f"[DEBUG] /refresh for user: {email}")
        new_access_token = create_access_token({"email": email, "name": name})
        new_refresh_token = create_refresh_token({"email": email, "name": name})
        response.set_cookie(key="refresh_token", value=new_refresh_token, httponly=True, secure=True, samesite="lax", max_age=REFRESH_TOKEN_EXPIRE_MINUTES*60)
        return {"accessToken": new_access_token}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DEBUG] Refresh token error: {e}")
        raise HTTPException(status_code=401, detail="Invalid refresh token")

