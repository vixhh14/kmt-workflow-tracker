# 💸 100% Free Deployment Guide

This guide explains how to deploy your Workflow Tracker App for **FREE** using the best available cloud tiers.

## 🏗️ **The Free Stack**

1.  **Database:** **Neon** (Free Serverless PostgreSQL)
2.  **Backend:** **Render** (Free Web Service)
3.  **Frontend:** **Vercel** (Free Static Hosting)

---

## 🚀 **Step 1: Set up the Database (Neon)**

1.  Go to [neon.tech](https://neon.tech) and sign up.
2.  Create a new project (e.g., `workflow-tracker`).
3.  **Copy the Connection String:**
    *   It looks like: `postgres://user:password@ep-xyz.aws.neon.tech/neondb?sslmode=require`
    *   Save this! You will need it for the backend.

---

## ⚙️ **Step 2: Deploy Backend (Render)**

1.  Push your code to **GitHub** (if you haven't already).
2.  Go to [render.com](https://render.com) and sign up.
3.  Click **"New +"** → **"Web Service"**.
4.  Connect your GitHub repository.
5.  **Configure Settings:**
    *   **Root Directory:** `backend`
    *   **Runtime:** Python 3
    *   **Build Command:** `pip install -r requirements.txt`
    *   **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port 10000`
6.  **Environment Variables:** (Scroll down to "Advanced")
    *   Add Key: `DATABASE_URL`
    *   Add Value: Paste your **Neon Connection String** here.
7.  Click **"Create Web Service"**.
    *   Wait for it to deploy.
    *   **Copy your Backend URL:** (e.g., `https://workflow-tracker.onrender.com`)

---

## 🎨 **Step 3: Deploy Frontend (Vercel)**

1.  Go to [vercel.com](https://vercel.com) and sign up.
2.  Click **"Add New..."** → **"Project"**.
3.  Import your GitHub repository.
4.  **Configure Settings:**
    *   **Root Directory:** Click "Edit" and select `frontend`.
    *   **Framework Preset:** Vite (should auto-detect).
5.  **Environment Variables:**
    *   Add Key: `VITE_API_URL`
    *   Add Value: Paste your **Render Backend URL** (e.g., `https://workflow-tracker.onrender.com`).
    *   *Note: Do NOT add a trailing slash `/` at the end.*
6.  Click **"Deploy"**.

---

## 🔄 **Step 4: Initialize the Database**

Since this is a new database, it's empty. You need to create the tables.

1.  **Wait for Render to finish deploying.**
2.  Render has a "Shell" or "Console" tab. Open it.
3.  Run the initialization script directly on the server:
    ```bash
    python init_db.py
    python setup_onboarding.py
    ```
    *This creates the admin user and tables in your new Neon database.*

---

## ✅ **Done!**

*   **Visit your Vercel URL:** This is your live app.
*   **Mobile App:** Open the Vercel URL on your phone → "Add to Home Screen".

---

## ⚠️ **Important Limitations of Free Tier**

1.  **Render Cold Starts:** The free backend "sleeps" after 15 minutes of inactivity. The first request might take **50 seconds** to load. This is normal for free tiers.
2.  **Neon Limits:** Generous limits, but strictly for small/medium projects.
