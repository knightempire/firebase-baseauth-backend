from fastapi import APIRouter
from app.core.database import get_db_conn

router = APIRouter()

@router.get("/")
def root():
    msg = "hi dev"
    try:
        conn = get_db_conn()
        conn.close()
        db_status = "connected"
    except Exception:
        db_status = "not connected"
    return {"message": msg, "db": db_status}
