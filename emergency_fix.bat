@echo off
REM ============================================================================
REM EMERGENCY FIX: Restore expected_completion_time Column
REM ============================================================================

echo =============================================
echo EMERGENCY FIX - Schema Mismatch
echo =============================================
echo.
echo Issue: Column tasks.expected_completion_time missing from DB
echo Fix: Restore column to match ORM definition
echo.

set DB_NAME=workflow_tracker
set DB_USER=postgres

echo Step 1: Checking PostgreSQL connection...
pg_isready -U %DB_USER% >nul 2>&1
if errorlevel 1 (
    echo [ERROR] PostgreSQL is not running!
    pause
    exit /b 1
)
echo [OK] PostgreSQL is running
echo.

echo Step 2: Applying emergency migration...
psql -U %DB_USER% -d %DB_NAME% -f backend\migrations\V20260108__restore_expected_completion_time.sql

if errorlevel 1 (
    echo [ERROR] Migration failed!
    pause
    exit /b 1
)
echo [OK] Migration applied
echo.

echo Step 3: Verifying column exists...
psql -U %DB_USER% -d %DB_NAME% -c "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'tasks' AND column_name = 'expected_completion_time';"

echo.
echo =============================================
echo MIGRATION COMPLETE!
echo =============================================
echo.
echo Next steps:
echo 1. Restart backend server
echo 2. Test dashboards
echo.
echo Restart backend with:
echo   cd backend
echo   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
echo.
pause
