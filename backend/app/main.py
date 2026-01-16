
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import CORS_ORIGINS
from app.routers import (
    auth_router, users_router, tasks_router, projects_router,
    attendance_router, machines_routers, operational_tasks_router,
    unified_dashboard_router, admin_router, supervisor_router,
    planning_router, approvals_router, dropdowns_router,
    reports_router, analytics_router, operator_router,
    seed_router, subtasks_router, outsource_router,
    machine_categories_router, units_router, user_skills_router
)

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging
import traceback

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="KMT Workflow Tracker API", version="2.0.0")

# Global Exception Handler (Backend Safety Guarantee)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"❌ UNHANDLED EXCEPTION: {str(exc)}")
    logger.error(traceback.format_exc())
    
    # Ensure CORS headers are present even on errors
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "message": str(exc),
            "path": request.url.path
        },
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(tasks_router.router)
app.include_router(projects_router.router)
app.include_router(attendance_router.router)
app.include_router(machines_routers.router)
app.include_router(operational_tasks_router.router)
app.include_router(unified_dashboard_router.router)
app.include_router(admin_router.router)
app.include_router(supervisor_router.router)
app.include_router(planning_router.router)
app.include_router(approvals_router.router)
app.include_router(dropdowns_router.router)
app.include_router(reports_router.router)
app.include_router(analytics_router.router)
app.include_router(operator_router.router)
app.include_router(seed_router.router)
app.include_router(subtasks_router.router)
app.include_router(outsource_router.router)
app.include_router(machine_categories_router.router)
app.include_router(units_router.router)
app.include_router(user_skills_router.router)

@app.get("/")
async def root():
    return {"message": "Welcome to KMT Workflow Tracker API (Google Sheets Backend)", "status": "online"}

@app.on_event("startup")
async def startup_event():
    """
    Startup tasks for Google Sheets backend.
    """
    print("🚀 App starting with Google Sheets Backend")
    print(f"📊 Using Spreadsheet ID: {os.getenv('GOOGLE_SHEET_ID')}")
    print("✅ Startup completed")
