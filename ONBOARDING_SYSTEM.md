# User Onboarding System

This document describes the user onboarding system implementation for the Workflow Tracker application.

## Overview

The onboarding system allows new users to register themselves with a two-step signup flow:
1. **Step 1**: Basic profile information (username, email, password, personal details)
2. **Step 2**: Unit selection and machine skills (select unit, choose machines they can operate, specify skill levels)

After registration, users are placed in a "pending" status and must be approved by an admin before they can log in.

## Database Schema

### New Tables

#### `units`
- `id` (INTEGER, PRIMARY KEY)
- `name` (TEXT, UNIQUE)
- `description` (TEXT)
- `created_at` (DATETIME)

#### `machine_categories`
- `id` (INTEGER, PRIMARY KEY)
- `name` (TEXT, UNIQUE)
- `description` (TEXT)
- `created_at` (DATETIME)

#### `user_machines`
Junction table linking users to machines with skill levels
- `id` (INTEGER, PRIMARY KEY)
- `user_id` (TEXT, FOREIGN KEY → users.user_id)
- `machine_id` (TEXT, FOREIGN KEY → machines.id)
- `skill_level` (TEXT: 'beginner', 'intermediate', 'expert')
- `created_at` (DATETIME)

#### `user_approvals`
- `id` (INTEGER, PRIMARY KEY)
- `user_id` (TEXT, FOREIGN KEY → users.user_id)
- `status` (TEXT: 'pending', 'approved', 'rejected')
- `approved_by` (TEXT, FOREIGN KEY → users.user_id)
- `approved_at` (DATETIME)
- `notes` (TEXT)
- `created_at` (DATETIME)

### Updated Tables

#### `users`
Added fields:
- `date_of_birth` (DATE)
- `address` (TEXT)
- `contact_number` (TEXT)
- `unit_id` (INTEGER, FOREIGN KEY → units.id)
- `approval_status` (TEXT: 'pending', 'approved', 'rejected')

#### `machines`
Added fields:
- `category_id` (INTEGER, FOREIGN KEY → machine_categories.id)
- `unit_id` (INTEGER, FOREIGN KEY → units.id)

## API Endpoints

### Units (`/api/units`)
- `GET /api/units` - Get all units
- `GET /api/units/{unit_id}` - Get unit by ID
- `POST /api/units` - Create new unit (admin only)

### Machine Categories (`/api/machine-categories`)
- `GET /api/machine-categories` - Get all machine categories

### User Skills (`/api/user-skills`)
- `GET /api/user-skills/{user_id}/machines` - Get all machines a user can operate
- `POST /api/user-skills/{user_id}/machines` - Add multiple machine skills for a user
- `DELETE /api/user-skills/{user_id}/machines/{machine_id}` - Remove a machine skill

### User Approvals (`/api/approvals`)
- `GET /api/approvals/pending` - Get all pending user approvals with user details
- `POST /api/approvals/{user_id}/approve` - Approve a user
- `POST /api/approvals/{user_id}/reject` - Reject a user

### Authentication (`/auth`)
- `POST /auth/signup` - Register new user (creates user in pending status)
- `POST /auth/login` - Login (checks approval status)

## Frontend Pages

### Signup Flow

#### `/signup` - Step 1: Basic Profile
Collects:
- Username
- Email
- Password
- Full Name
- Date of Birth
- Contact Number
- Address

Data is stored in sessionStorage and user proceeds to Step 2.

#### `/signup/skills` - Step 2: Skills & Machines
Allows user to:
- Select their unit (Unit 1 or Unit 2)
- View machines available in that unit, organized by category
- Select machines they can operate
- Specify skill level for each machine (beginner, intermediate, expert)

On submission:
1. Creates user account with `approval_status='pending'`
2. Adds machine skills to `user_machines` table
3. Creates approval record in `user_approvals` table
4. Redirects to login with success message

### Admin Pages

#### `/admin/approvals` - User Approvals
Admin-only page that shows:
- List of all pending user registrations
- User details (name, email, contact info, address, unit)
- Machine skills with skill levels
- Approve/Reject buttons
- Optional notes field

When admin approves:
- Updates `user_approvals.status` to 'approved'
- Updates `users.approval_status` to 'approved'
- User can now log in

When admin rejects:
- Updates `user_approvals.status` to 'rejected'
- Updates `users.approval_status` to 'rejected'
- User cannot log in

## Setup Instructions

### 1. Run the Setup Script

```bash
cd backend
python setup_onboarding.py
```

This will:
- Initialize the database with all tables
- Run the onboarding system migration
- Seed units, categories, and machines
- Create demo users

### 2. Manual Setup (Alternative)

If you prefer to run each step manually:

```bash
cd backend

# Step 1: Initialize database
python init_db.py

# Step 2: Run migration
python migrate_onboarding_system.py

# Step 3: Seed data
python seed_units_and_machines.py
```

## Demo Data

### Units
- **Unit 1**: Main production unit (27 machines)
- **Unit 2**: Secondary production unit (11 machines)

### Machine Categories
Grinder, Lathe, Material Cutting, VMC, Milling, Engraving, Honing, Buffing, Tooth Rounding, Lapping, Drilling, Rack Cutting, CNC, Welding, Slotting, Grinding

### Demo Users
All demo users are pre-approved:
- **admin** / admin123 (role: admin)
- **operator** / operator123 (role: operator)
- **supervisor** / supervisor123 (role: supervisor)
- **planning** / planning123 (role: planning)
- **vendor** / vendor123 (role: vendor)

## User Flow

### New User Registration
1. User visits `/signup`
2. Fills out basic profile information
3. Proceeds to `/signup/skills`
4. Selects unit and machine skills
5. Submits registration
6. Account created with `approval_status='pending'`
7. Redirected to login with message about pending approval

### Admin Approval
1. Admin logs in and visits `/admin/approvals`
2. Reviews pending user registrations
3. Views user details and machine skills
4. Approves or rejects the user
5. User receives updated status

### Approved User Login
1. User attempts to log in
2. System checks `approval_status`
3. If approved, login succeeds
4. If pending, shows "pending approval" message
5. If rejected, shows "registration rejected" message

## Security Considerations

- Passwords are hashed using SHA-256 before storage
- JWT tokens are used for authentication
- Approval status is checked on every login attempt
- Admin-only routes are protected with role-based access control

## Future Enhancements

- Email notifications for approval/rejection
- User profile editing
- Skill level verification/certification
- Machine availability tracking
- Training requirements for machines
- Bulk user approval/rejection
