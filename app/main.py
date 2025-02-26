from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.routes.auth import router as auth_router
from app.routes.password import router as password_router
from app.routes.referrals import router as referrals_router
from app.config import limiter  # ✅ Use the limiter from config
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded 

app = FastAPI(title="VomyChat Referral System")

# ✅ Add Rate Limiting Middleware
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)  # ✅ Add middleware

# ✅ Proper Rate Limit Exception Handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"message": "Too many requests, please try again later."}
    )

# Include Routes
app.include_router(auth_router)
app.include_router(password_router)
app.include_router(referrals_router)

@app.get("/")
def root():
    return {"message": "VomyChat Referral API is running!"}
