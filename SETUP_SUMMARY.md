# User Onboarding System - Setup Summary

## What Has Been Implemented

### Backend Changes

#### 1. Database Models (`backend/app/models/models_db.py`)
- ✅ Added new fields to `User` model:
  - `date_of_birth`, `address`, `contact_number`
  - `unit_id` (links to units table)
  - `approval_status` (pending/approved/rejected)

- ✅ Created new models:
  - `Unit` - Factory units (Unit 1, Unit 2)
  - `MachineCategory` - Machine categories (Grinder, Lathe, CNC, etc.)
  - `UserMachine` - Junction table for user-machine skills with skill levels
  - `UserApproval` - Tracks approval workflow

- ✅ Updated `Machine` model:
  - Added `category_id` and `unit_id` fields

#### 2. API Routers
- ✅ `units_router.py` - CRUD operations for units
- ✅ `machine_categories_router.py` - Get machine categories
- ✅ `user_skills_router.py` - Manage user-machine skill mappings
- ✅ `approvals_router.py` - Handle user approval workflow
- ✅ Updated `auth_router.py` - Added signup endpoint and approval status checks

#### 3. Database Scripts
- ✅ `migrate_onboarding_system.py` - Adds new tables and fields
- ✅ `seed_units_and_machines.py` - Populates units, categories, and 38 machines
- ✅ `setup_onboarding.py` - **NEW** - Complete setup script
- ✅ Updated `init_db.py` - Sets demo users as pre-approved

#### 4. Core Updates
- ✅ `database.py` - Added `get_db_connection()` for raw SQLite access
- ✅ `main.py` - Registered all new routers

### Frontend Changes

#### 1. Signup Pages
- ✅ `/signup` - Step 1: Basic profile information
- ✅ `/signup/skills` - Step 2: Unit and machine skills selection

#### 2. Admin Pages
- ✅ `/admin/approvals` - User approval management page

#### 3. Routing
- ✅ Updated `app.jsx` - Added signup and approval routes

## How to Set Up

### Option 1: Automated Setup (Recommended)

Run the comprehensive setup script:

```bash
cd backend
python setup_onboarding.py
```

This will automatically:
1. Initialize the database
2. Run migrations
3. Seed all data
4. Create demo users

### Option 2: Manual Setup

If you prefer step-by-step:

```bash
cd backend

# Step 1: Initialize database and create demo users
python init_db.py

# Step 2: Add onboarding tables and fields
python migrate_onboarding_system.py

# Step 3: Seed units, categories, and machines
python seed_units_and_machines.py
```

## What Gets Created

### Database Tables
- `units` (2 units)
- `machine_categories` (16 categories)
- `user_machines` (junction table)
- `user_approvals` (approval tracking)

### Seed Data
- **2 Units**: Unit 1 (27 machines), Unit 2 (11 machines)
- **16 Categories**: Grinder, Lathe, CNC, VMC, Milling, Welding, etc.
- **38 Machines**: Distributed across both units
- **5 Demo Users**: admin, operator, supervisor, planning, vendor (all pre-approved)

## Testing the System

### 1. Start the Backend
```bash
cd backend
uvicorn app.main:app --reload
```

### 2. Start the Frontend
```bash
cd frontend
npm run dev
```

### 3. Test User Registration Flow

1. **Visit Signup Page**: http://localhost:5173/signup
2. **Fill Basic Info**: Username, email, password, personal details
3. **Select Skills**: Choose unit, select machines, set skill levels
4. **Submit**: User created with "pending" status
5. **Try Login**: Should show "pending approval" message

### 4. Test Admin Approval

1. **Login as Admin**: username: `admin`, password: `admin123`
2. **Visit Approvals**: http://localhost:5173/admin/approvals
3. **Review User**: See all user details and machine skills
4. **Approve/Reject**: Click approve or reject button
5. **User Can Login**: Approved users can now log in

## User Flow Diagram

```
New User Registration:
┌─────────────┐
│   /signup   │ → Basic Info (username, email, password, etc.)
└──────┬──────┘
       ↓
┌─────────────────┐
│ /signup/skills  │ → Select Unit & Machines
└──────┬──────────┘
       ↓
┌─────────────────┐
│  Submit Form    │ → Creates user with approval_status='pending'
└──────┬──────────┘
       ↓
┌─────────────────┐
│  Redirect to    │ → Shows "Pending approval" message
│     /login      │
└─────────────────┘

Admin Approval:
┌──────────────────┐
│ Admin logs in    │
└────────┬─────────┘
         ↓
┌──────────────────┐
│ /admin/approvals │ → View pending users
└────────┬─────────┘
         ↓
┌──────────────────┐
│ Approve/Reject   │ → Updates approval_status
└────────┬─────────┘
         ↓
┌──────────────────┐
│ User can login   │ → If approved
└──────────────────┘
```

## Demo Credentials

All demo users are pre-approved and can log in immediately:

| Username   | Password      | Role       |
|------------|---------------|------------|
| admin      | admin123      | admin      |
| operator   | operator123   | operator   |
| supervisor | supervisor123 | supervisor |
| planning   | planning123   | planning   |
| vendor     | vendor123     | vendor     |

## Key Features

✅ **Two-Step Signup**: Separates basic info from skills selection
✅ **Unit-Based Organization**: Users belong to specific units
✅ **Skill Levels**: Beginner, Intermediate, Expert for each machine
✅ **Admin Approval**: All new users must be approved
✅ **Login Protection**: Pending/rejected users cannot log in
✅ **Machine Categories**: Organized machine selection
✅ **Comprehensive UI**: Beautiful, modern signup and approval pages

## Files Modified/Created

### Backend
- ✅ `app/models/models_db.py` - Updated User, Machine models; added new models
- ✅ `app/routers/auth_router.py` - Added signup endpoint
- ✅ `app/routers/units_router.py` - NEW
- ✅ `app/routers/machine_categories_router.py` - NEW
- ✅ `app/routers/user_skills_router.py` - NEW
- ✅ `app/routers/approvals_router.py` - NEW
- ✅ `app/core/database.py` - Added get_db_connection()
- ✅ `app/main.py` - Registered new routers
- ✅ `migrate_onboarding_system.py` - NEW
- ✅ `seed_units_and_machines.py` - NEW
- ✅ `setup_onboarding.py` - NEW
- ✅ `init_db.py` - Updated

### Frontend
- ✅ `src/pages/Signup.jsx` - NEW
- ✅ `src/pages/SignupSkills.jsx` - NEW
- ✅ `src/pages/admin/UserApprovals.jsx` - NEW
- ✅ `src/app.jsx` - Added routes

### Documentation
- ✅ `ONBOARDING_SYSTEM.md` - Complete system documentation
- ✅ `SETUP_SUMMARY.md` - This file

## Next Steps

1. ✅ Run the setup script: `python backend/setup_onboarding.py`
2. ✅ Start backend and frontend servers
3. ✅ Test the signup flow with a new user
4. ✅ Test admin approval workflow
5. ✅ Verify approved user can log in

## Troubleshooting

### Issue: "Table already exists" error
**Solution**: The migration script uses `CREATE TABLE IF NOT EXISTS`, so this is safe to ignore.

### Issue: Machines not showing in signup
**Solution**: Make sure `seed_units_and_machines.py` ran successfully.

### Issue: Cannot approve users
**Solution**: Make sure you're logged in as an admin user.

### Issue: Approved user still can't login
**Solution**: Check that both `users.approval_status` and `user_approvals.status` are set to 'approved'.

## Support

For questions or issues, refer to:
- `ONBOARDING_SYSTEM.md` - Detailed system documentation
- Database schema in `migrate_onboarding_system.py`
- API endpoints in respective router files

---

**Status**: ✅ Implementation Complete
**Last Updated**: 2025-11-25
