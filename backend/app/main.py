from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import (
    users_router,
    machines_routers,
    tasks_router,
    analytics_router,
    outsource_router,
    auth_router,
    planning_router,
    units_router,
    machine_categories_router,
    user_skills_router,
    approvals_router,
    admin_router,
    subtasks_router,
    seed_router,
)
from app.core.config import CORS_ORIGINS
import uvicorn

# Create FastAPI app with metadata
app = FastAPI(
    title="Workflow Tracker API",
    description="Backend API for KMT Workflow Tracker",
    version="1.0.0",
)

# CORS configuration - Use centralized config
# Note: Wildcard patterns don't work with credentials, so we list all origins explicitly
print(f"🔒 CORS Origins configured: {CORS_ORIGINS}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Startup event – create tables and demo users
@app.on_event("startup")
async def startup_event():
    from app.core.database import Base, engine
    from app.models.models_db import Subtask  # Import to ensure table is registered
    from create_demo_users import create_demo_users
    
    try:
        print("🚀 Running startup tasks...")
        
        # Create all database tables (including new Subtask table)
        print("📊 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created/verified")
        
        # Create demo users
        print("👥 Creating demo users...")
        create_demo_users()
        print("✅ Demo users created/verified")
        
        print("✅ Startup complete")
    except Exception as e:
        print(f"❌ Error during startup: {e}")

# Root endpoint
@app.get("/")
def root():
    return {
        "message": "Workflow Tracker API running",
        "version": "1.0.0",
        "status": "healthy"
    }

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "ok"}

# Include routers (NO /api prefix - routes are already prefixed)
app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(admin_router.router)
app.include_router(machines_routers.router)
app.include_router(tasks_router.router)
app.include_router(analytics_router.router)
app.include_router(outsource_router.router)
app.include_router(planning_router.router)
app.include_router(units_router.router)
app.include_router(machine_categories_router.router)
app.include_router(user_skills_router.router)
app.include_router(approvals_router.router)
app.include_router(subtasks_router.router)
app.include_router(seed_router.router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
