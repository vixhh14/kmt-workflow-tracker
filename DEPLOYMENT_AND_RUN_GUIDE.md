# 🚀 Project Run & Deployment Guide

This guide contains all the commands you need to run, test, and deploy your application.

## 1️⃣ Backend: Local Run Commands

### **Setup & Install**
Open a terminal in the `backend` directory.

```bash
cd backend

# Create virtual environment (if not exists)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### **Run Local Server**
Ensure your `.env` file is set up with the **EXTERNAL** Render PostgreSQL URL.

```bash
# Start the FastAPI server with hot-reload
uvicorn app.main:app --reload
```
*Server will run at: `http://localhost:8000`*

### **Database Initialization**
Since we are using `create_all` in `main.py`, tables are created automatically on startup.
To seed demo users and initial data:

```bash
python create_demo_users.py
python seed_machines.py
```

## 2️⃣ Backend: Git Commit & Push

```bash
# From project root or backend folder
git add .
git commit -m "Update backend configuration and fixes"
git push origin main
```
*This triggers a deployment on Render (if auto-deploy is enabled).*

---

## 3️⃣ Frontend: Local Run Commands

### **Setup & Install**
Open a new terminal in the `frontend` directory.

```bash
cd frontend

# Install dependencies
npm install
```

### **Run Local Development Server**
Ensure your `src/api/axios.js` or `.env` points to `http://localhost:8000` for local dev.

```bash
npm run dev
```
*Frontend will run at: `http://localhost:5173`*

### **Build for Production (Test Build)**
To verify the build passes before deploying:

```bash
npm run build
```

## 4️⃣ Frontend: Git Commit & Push

```bash
# From project root or frontend folder
git add .
git commit -m "Update frontend UI and fixes"
git push origin main
```
*This triggers a deployment on Vercel (if connected).*

---

## 5️⃣ Deployment Commands & Steps

### **Backend (Render)**
Your backend is hosted on Render.
1. **Push Code**: `git push origin main` automatically triggers a build.
2. **Environment Variables**:
   - Go to Render Dashboard -> Your Service -> **Environment**.
   - Ensure `DATABASE_URL` is set to your **INTERNAL** Render URL (ends in `/kmt_workflow_db`).
   - Ensure `PYTHON_VERSION` is set (e.g., `3.11.9`).
3. **Manual Deploy** (if needed):
   - Click **Manual Deploy** -> **Deploy latest commit** in Render dashboard.

### **Frontend (Vercel)**
Your frontend is hosted on Vercel.
1. **Push Code**: `git push origin main` automatically triggers a build.
2. **Environment Variables**:
   - Go to Vercel Dashboard -> Your Project -> **Settings** -> **Environment Variables**.
   - Set `VITE_API_URL` to your **Render Backend URL** (e.g., `https://kmt-workflow-backend.onrender.com`).
3. **Redeploy** (if env vars changed):
   - Go to **Deployments** -> Click latest deployment -> **Redeploy**.
