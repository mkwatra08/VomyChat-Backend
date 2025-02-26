from datetime import datetime
from pydantic import BaseModel, EmailStr

class User(BaseModel):
    username: str
    email: EmailStr
    password_hash: str
    referral_code: str
    referred_by: str | None = None
    created_at: datetime = datetime.utcnow()

class Referral(BaseModel):
    referrer_id: str
    referred_user_id: str
    date_referred: datetime = datetime.utcnow()
    status: str = "pending"
