from pydantic import BaseModel

class UserInfo(BaseModel):
    email: str
    name: str = ""
    accessToken: str

class BioRequest(BaseModel):
    bio: str

class TokenRequest(BaseModel):
    idToken: str
