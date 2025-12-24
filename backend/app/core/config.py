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
# Include all frontend deployment URLs (production, preview, and local development)
default_origins = [
    # Local development
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5174",
    # Production Vercel URLs
    "https://kmt-workflow-tracker.vercel.app",
    "https://kmt-workflow-tracker2.vercel.app",
    "https://kmt-backend.onrender.com",
    # Vercel preview/staging URLs
    "https://kmt-workflow-tracker-qayt.vercel.app",
    "https://kmt-workflow-tracker-qayt-l7ytc60vt.vercel.app",
]

# Combined list with normalization
CORS_ORIGINS = list(set([o.rstrip("/") for o in CORS_ORIGINS + default_origins]))

# Allow wildcard for vercel preview branches if they match a pattern
# But CORSMiddleware doesn't support regex in allow_origins, we'd need a custom middleware for that.
# For now, we rely on specific URLs provided by the user.

