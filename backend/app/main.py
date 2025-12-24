from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, DataError, OperationalError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.exceptions import (
    validation_exception_handler,
    integrity_error_handler,
    data_error_handler,
    operational_error_handler,
    http_exception_handler,
    global_exception_handler
)
from app.routers import (
    users_router,
    machines_routers,
    tasks_router,
    analytics_router,
    outsource_router,
    auth_router,
    planning_router,
    supervisor_router,
    units_router,
    machine_categories_router,
    user_skills_router,
    approvals_router,
    admin_router,
    subtasks_router,
    seed_router,
    performance_router,
    operator_router,
    admin_dashboard_router,
    attendance_router,
    projects_router,
    reports_router,
    unified_dashboard_router,
    operational_tasks_router,
)
from app.core.config import CORS_ORIGINS
import uvicorn

# Create FastAPI app with metadata
app = FastAPI(
    title="Workflow Tracker API",
    description="Backend API for KMT Workflow Tracker",
    version="1.0.0",
)

# Register Exception Handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(DataError, data_error_handler)
app.add_exception_handler(OperationalError, operational_error_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

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
        # from app.core.database import DEFAULT_DB_PATH
        # print(f"📂 Database Path: {DEFAULT_DB_PATH}")
        print("📂 Database: Using configured DATABASE_URL")
        
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
                project_count = session.query(Project).count()
            except Exception:
                project_count = "Error querying"

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
app.include_router(admin_dashboard_router.router)
app.include_router(machines_routers.router)
app.include_router(tasks_router.router)
app.include_router(analytics_router.router)
app.include_router(outsource_router.router)
app.include_router(planning_router.router)
app.include_router(supervisor_router.router)
app.include_router(units_router.router)
app.include_router(machine_categories_router.router)
app.include_router(user_skills_router.router)
app.include_router(approvals_router.router)
app.include_router(subtasks_router.router)
app.include_router(seed_router.router)
app.include_router(performance_router.router)
app.include_router(operator_router.router)
app.include_router(attendance_router.router)
app.include_router(projects_router.router)
app.include_router(reports_router.router)
app.include_router(unified_dashboard_router.router)
app.include_router(operational_tasks_router.router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
