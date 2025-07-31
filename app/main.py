from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from firebase_admin import credentials
from app.core.config import settings
from app.routes import auth, bio, refresh, health

# Initialize Firebase Admin
if not firebase_admin._apps:
    cred = credentials.Certificate(settings.FIREBASE_CREDS)
    firebase_admin.initialize_app(cred)

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://firebase-baseauth-frontend-144895597889.europe-west1.run.app",
        "https://firebase-baseauth-frontend-4nj5tumfhq-ew.a.run.app",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Health check with DB status
app.include_router(health.router)

# Routers
app.include_router(auth.router)
app.include_router(bio.router)
app.include_router(refresh.router)