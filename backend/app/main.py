from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from sqlalchemy.exc import IntegrityError, DataError, OperationalError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.exceptions import (
    validation_exception_handler,
    response_validation_exception_handler,
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
    dropdowns_router,
)
import uvicorn
from app.core.config import CORS_ORIGINS

# Create FastAPI app with metadata
app = FastAPI(
    title="Workflow Tracker API",
    description="Backend API for KMT Workflow Tracker",
    version="1.0.0",
    redirect_slashes=False, # Prevent 307 redirects breaking CORS
)

# CORS configuration - MUST be defined immediately after app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex="https://.*\.vercel\.app",  # Support all Vercel subdomains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Exception Handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ResponseValidationError, response_validation_exception_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(DataError, data_error_handler)
app.add_exception_handler(OperationalError, operational_error_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)



@app.on_event("startup")
async def startup_event():
    """
    Run startup tasks with exponential backoff and retries for database connection.
    This ensures the app doesn't crash if the DB is temporarily unreachable.
    """
    import time
    from app.core.database import Base, engine
    from create_demo_users import create_demo_users
    from app.core.init_data import init_db_data
    
    max_retries = 7
    retry_delay = 3  # Start with 3 seconds
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"🚀 Running startup tasks (Attempt {attempt}/{max_retries})...")
            
            # Dispose any previous poisoned connections in the pool
            if attempt > 1:
                engine.dispose()
                
            # 1. Verify Connection and Create tables
            with engine.connect() as conn:
                print("🔗 Database connection established")
                print("📊 Synchronizing schema (create_all)...")
                Base.metadata.create_all(bind=engine)
            
            # 2. Demo Users
            print("👥 Checking/Creating demo users...")
            create_demo_users()
            
            # 3. Init Data (Schema Check + Seeding)
            print("🌱 Initializing additional data...")
            init_db_data()
            
            print("✅ Startup tasks completed successfully")
            break  # Success!
            
        except Exception as e:
            print(f"⚠️ Startup attempt {attempt} failed: {e}")
            if attempt < max_retries:
                # Force pool clear before next attempt
                engine.dispose()
                print(f"🔄 Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)  # Caps at 60s
            else:
                print("❌ CRITICAL: Startup failed after maximum retries.")
                import traceback
                traceback.print_exc()


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
app.include_router(dropdowns_router.router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
