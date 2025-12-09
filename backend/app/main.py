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
        
        # 1. Log Database Path
        from app.core.database import DEFAULT_DB_PATH
        print(f"📂 Database Path: {DEFAULT_DB_PATH}")
        
        # 2. Create all database tables
        print("📊 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created/verified")
        
        # 3. Verify Data Integrity
        from sqlalchemy.orm import Session
        session = Session(bind=engine)
        try:
            from app.models.models_db import Machine, User, Project
            machine_count = session.query(Machine).count()
            user_count = session.query(User).count()
            # Project might not exist in models_db yet if it's in planning_model, check safely
            try:
                from app.models.planning_model import Project
                project_count = session.query(Project).count()
            except ImportError:
                project_count = "N/A (Model not loaded)"

            print(f"📈 Data Status:")
            print(f"   - Machines: {machine_count}")
            print(f"   - Users:    {user_count}")
            print(f"   - Projects: {project_count}")
            
            if machine_count == 0:
                print("⚠️ WARNING: Machine table is empty! You may need to run seed_machines.py")
        except Exception as e:
            print(f"⚠️ Error checking data counts: {e}")
        finally:
            session.close()
        
        # 4. Create demo users
        print("👥 Creating demo users...")
        create_demo_users()
        print("✅ Demo users created/verified")
        
        # 5. Initialize Data (Migrations + Seeding)
        from app.core.init_data import init_db_data
        print("🌱 Initializing data...")
        init_db_data()
        print("✅ Data initialization complete")
        
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
