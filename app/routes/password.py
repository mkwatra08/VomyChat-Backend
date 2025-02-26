from fastapi import APIRouter, HTTPException
from app.utils.jwt import create_access_token, verify_access_token
from app.utils.security import hash_password
from app.database import db
from pydantic import BaseModel
from datetime import timedelta

router = APIRouter(prefix="/api", tags=["Password Reset"])

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    user = await db.users.find_one({"email": request.email})
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    reset_token = create_access_token({"sub": user["email"]}, expires_delta=timedelta(minutes=30))
    return {"message": "Password reset link sent to email", "reset_token": reset_token}

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    payload = verify_access_token(request.token)
    if not payload:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    email = payload["sub"]
    hashed_password = hash_password(request.new_password)
    await db.users.update_one({"email": email}, {"$set": {"password_hash": hashed_password}})
    return {"message": "Password updated successfully"}
