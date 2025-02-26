from fastapi import APIRouter, Depends
from app.database import db
from app.utils.jwt import get_current_user

router = APIRouter(prefix="/api", tags=["Referrals"])

@router.get("/referrals")
async def get_referrals(user: dict = Depends(get_current_user)):
    referrals = await db.users.find({"referred_by": user["sub"]}).to_list(100)
    return {"referrals": [{"username": ref["username"], "email": ref["email"]} for ref in referrals]}

@router.get("/referral-stats")
async def referral_stats(user: dict = Depends(get_current_user)):
    referral_count = await db.users.count_documents({"referred_by": user["sub"]})
    return {"total_referrals": referral_count}
