from fastapi import APIRouter, Response, Cookie, HTTPException
from typing import Optional
from app.core.auth import verify_jwt_token, create_access_token, create_refresh_token

router = APIRouter()

@router.post("/refresh")
def refresh_token(response: Response, refresh_token: Optional[str] = Cookie(None)):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    try:
        payload = verify_jwt_token(refresh_token, refresh=True)
        email = payload["email"]
        name = payload.get("name", "")
        new_access_token = create_access_token({"email": email, "name": name})
        new_refresh_token = create_refresh_token({"email": email, "name": name})
        response.set_cookie(key="refresh_token", value=new_refresh_token, httponly=True, secure=True, samesite="lax", max_age=2*60)
        return {"accessToken": new_access_token}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
