import os
from dotenv import load_dotenv
load_dotenv()


JWT_SECRET = os.getenv("JWT_SECRET", "c2b0644eb4df8d087f994c58862a418fd455ac0286ee2bf3eec4e0e878328cde")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# Parse CORS origins from environment variable
backend_cors_origins_str = os.getenv("BACKEND_CORS_ORIGINS", "")
CORS_ORIGINS = [origin.strip() for origin in backend_cors_origins_str.split(",") if origin.strip()]

# Add default origins if not present
default_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "https://kmt-workflow-tracker-qayt.vercel.app",
    "https://kmt-workflow-tracker.vercel.app",
    "https://kmt-workflow-tracker-qayt-l7ytc60vt.vercel.app",
]

for origin in default_origins:
    if origin not in CORS_ORIGINS:
        CORS_ORIGINS.append(origin)

