import os
from dotenv import load_dotenv
from slowapi import Limiter
from slowapi.util import get_remote_address

# Load environment variables from .env file
load_dotenv()

# Database Configuration
MONGO_URI = os.getenv("MONGO_URI")

# Security Configuration
SECRET_KEY = os.getenv("5f8a26311a7ee2105dc184b0735382ab9665409e8e5299cc3c69996d29d11e3f")  # Fix the incorrect env key retrieval
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# ✅ Global Rate Limiter Instance
limiter = Limiter(key_func=get_remote_address)
