from fastapi import APIRouter, HTTPException, Depends, Request, Response, status
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from bson import ObjectId
import secrets
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
from app.utils.security import hash_password, verify_password
from app.utils.jwt import create_access_token
from app.database import db

router = APIRouter(prefix="/api", tags=["Authentication & Referrals"])

# ✅ Rate limiter for security
limiter = Limiter(key_func=get_remote_address)

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"message": "Too many requests, please try again later."},
    )

# ✅ Request Models
class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    referral_code: str | None = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

# ✅ User Registration
@router.post("/register")
@limiter.limit("5/second", error_message="Too many requests")
async def register(request: Request, data: RegisterRequest):
    existing_user = await db.users.find_one({"email": data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already in use")

    hashed_password = hash_password(data.password)
    referred_by = None
    referrer_id = None

    if data.referral_code:
        referring_user = await db.users.find_one({"referral_code": data.referral_code})
        if not referring_user:
            raise HTTPException(status_code=400, detail="Invalid referral code")
        referred_by = referring_user["email"]
        referrer_id = referring_user["_id"]

    new_referral_code = f"ref-{data.email.split('@')[0]}-{secrets.token_hex(3)}"

    new_user = {
        "username": data.username,
        "email": data.email,
        "password_hash": hashed_password,
        "referral_code": new_referral_code,
        "referred_by": referred_by,
        "created_at": datetime.utcnow()
    }
    result = await db.users.insert_one(new_user)
    new_user_id = result.inserted_id

    if referrer_id:
        referral_entry = {
            "referrer_id": referrer_id,
            "referred_user_id": new_user_id,
            "date_referred": datetime.utcnow(),
            "status": "successful"
        }
        await db.referrals.insert_one(referral_entry)

    return {"message": "User registered successfully", "referral_code": new_referral_code}

# ✅ User Login
@router.post("/login")
@limiter.limit("5/second", error_message="Too many requests")
async def login(request: Request, data: LoginRequest, response: Response):
    user = await db.users.find_one({"email": data.email})
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = create_access_token({"sub": user["email"]}, expires_delta=timedelta(hours=1))

    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=3600,
    )

    return {"message": "Login successful"}

# ✅ Logout API
@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}

# ✅ Get Referrals API
@router.get("/referrals/{email}")
async def get_referrals(email: str):
    referrer = await db.users.find_one({"email": email})
    if not referrer:
        raise HTTPException(status_code=404, detail="User not found")

    referral_entries = await db.referrals.find({"referrer_id": referrer["_id"]}).to_list(length=100)
    referred_users = [await db.users.find_one({"_id": entry["referred_user_id"]}) for entry in referral_entries]
    referred_user_emails = [user["email"] for user in referred_users if user]

    return {
        "referrer": email,
        "total_referrals": len(referred_users),
        "referred_users": referred_user_emails
    }

# ✅ Referral Statistics API
@router.get("/referral-stats/{email}")
async def referral_stats(email: str):
    referrer = await db.users.find_one({"email": email})
    if not referrer:
        raise HTTPException(status_code=404, detail="User not found")

    total_referrals = await db.referrals.count_documents({"referrer_id": referrer["_id"]})
    successful_referrals = await db.referrals.count_documents({"referrer_id": referrer["_id"], "status": "successful"})

    return {
        "total_referrals": total_referrals,
        "successful_referrals": successful_referrals
    }

# ✅ Forgot Password API
@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    user = await db.users.find_one({"email": request.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    reset_token = secrets.token_urlsafe(32)
    token_expiry = datetime.utcnow() + timedelta(minutes=15)

    await db.password_resets.insert_one({
        "email": request.email,
        "token": reset_token,
        "expires_at": token_expiry
    })

    return {"message": "Password reset link sent", "reset_token": reset_token}

# ✅ Reset Password API
@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    reset_entry = await db.password_resets.find_one({"token": request.token})
    if not reset_entry or reset_entry["expires_at"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    new_hashed_password = hash_password(request.new_password)
    await db.users.update_one({"email": reset_entry["email"]}, {"$set": {"password_hash": new_hashed_password}})

    await db.password_resets.delete_one({"token": request.token})  
    return {"message": "Password reset successful"}
