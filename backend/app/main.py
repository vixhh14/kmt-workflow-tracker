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



# Startup event – create tables and demo users
@app.on_event("startup")
async def startup_event():
    import asyncio
    from fastapi.concurrency import run_in_threadpool
    from app.core.database import Base, engine
    from app.models.models_db import Subtask
    from create_demo_users import create_demo_users
    from app.core.init_data import init_db_data
    
    async def run_init_tasks():
        try:
            print("🚀 Running startup tasks in background...")
            
            # 1. Create tables (Sync blocking I/O)
            print("📊 Creating database tables...")
            await run_in_threadpool(Base.metadata.create_all, bind=engine)
            print("✅ Database tables created/verified")
            
            # 2. Demo Users
            print("👥 Creating demo users...")
            await run_in_threadpool(create_demo_users)
            
            # 3. Init Data (Schema Check + Seeding)
            print("🌱 Initializing data...")
            await run_in_threadpool(init_db_data)
            print("✅ Startup tasks complete")
            
        except Exception as e:
            print(f"❌ Error during background startup: {e}")
            import traceback
            traceback.print_exc()

    # Create task to run in background so API is responsive immediately
    asyncio.create_task(run_init_tasks())


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
