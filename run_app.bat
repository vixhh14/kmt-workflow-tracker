@echo off
echo Starting Workflow Tracker...

:: Start Backend in a new window
start "Backend Server" cmd /k "cd backend && uvicorn app.main:app --reload"

:: Start Frontend in a new window
start "Frontend Server" cmd /k "cd frontend && npm run dev"

echo Servers started! 
echo Backend: import.meta.env.VITE_API_URL
echo Frontend: http://localhost:5173
pause
