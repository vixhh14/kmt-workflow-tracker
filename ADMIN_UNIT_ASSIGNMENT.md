# Updated Signup Flow: Admin Assigns Units Based on Skills

## ✅ Changes Made

### **Problem:**
Previously, users were selecting their own unit during signup, which doesn't make sense because the admin should assign units based on the user's machine skills.

### **Solution:**
- Users now select machines from **ALL units** (no unit selection during signup)
- Admin reviews user's machine skills during approval
- **Admin assigns the appropriate unit** based on which machines the user can operate
- System automatically **suggests a unit** based on the majority of machines selected

---

## 🔄 New Signup & Approval Flow

### **Step 1: User Signup - Basic Info (`/signup`)**
User creates their credentials and enters personal information:
- ✅ Username (user chooses)
- ✅ Password (user chooses)
- ✅ Email
- ✅ Full name
- ✅ Date of birth
- ✅ Address
- ✅ Contact number

### **Step 2: User Signup - Machine Skills (`/signup/skills`)**
User selects machines they can operate:
- ✅ Sees **ALL machines** from both Unit 1 and Unit 2
- ✅ Machines are organized by category (Grinder, Lathe, CNC, etc.)
- ✅ Each machine shows which unit it belongs to: "(Unit 1)" or "(Unit 2)"
- ✅ User checks machines they can operate
- ✅ User selects skill level for each: Beginner, Intermediate, or Expert
- ✅ **NO unit selection** - admin will assign later

**Example:**
```
Select Machines You Can Operate:

▼ Grinder (5 machines)
  ☑ Hand Grinder (Unit 1)        [Expert ▼]
  ☐ Bench Grinder (Unit 1)
  ☑ Surface Grinding (Unit 2)    [Intermediate ▼]

▼ Lathe (4 machines)
  ☑ Turnmaster (Unit 1)          [Intermediate ▼]
  ☐ Leader (Unit 1)
  ☑ PSG (Unit 2)                 [Beginner ▼]

▼ CNC (2 machines)
  ☑ Zimberman (Unit 1)           [Expert ▼]
  ☐ Ace Superjobber (Unit 2)
```

### **Step 3: Account Created**
- User account created with `approval_status='pending'`
- Machine skills saved to database
- **unit_id is NULL** (not assigned yet)
- Approval record created
- User redirected to login with message: "Pending admin approval. Admin will assign you to a unit based on your skills."

### **Step 4: User Tries to Login**
- Login fails with message: "Your account is pending admin approval"
- User must wait for admin to approve

---

## 👨‍💼 Admin Approval Process

### **Admin Reviews User (`/admin/approvals`)**

Admin sees:
1. **User Details:**
   - Name, username, email
   - Date of birth, address, contact number
   - Application date

2. **Machine Skills:**
   - List of all machines user selected
   - Skill level for each machine
   - **Which unit each machine belongs to**

3. **Unit Assignment (NEW!):**
   - Dropdown to select unit
   - **System automatically suggests a unit** based on:
     - Which machines the user selected
     - If user selected more machines from Unit 1 → suggests Unit 1
     - If user selected more machines from Unit 2 → suggests Unit 2
   - Admin can override the suggestion if needed

**Example:**
```
┌─────────────────────────────────────────────────────┐
│ John Doe                                            │
│ @john_doe • john@email.com                          │
│                                                     │
│ Machine Skills (5 machines):                        │
│ • Hand Grinder (Unit 1) - Expert                    │
│ • Turnmaster (Unit 1) - Intermediate                │
│ • Zimberman (Unit 1) - Expert                       │
│ • Surface Grinding (Unit 2) - Intermediate          │
│ • PSG (Unit 2) - Beginner                           │
│                                                     │
│ ┌─────────────────────────────────────────────┐   │
│ │ ⚠ Assign Unit (Required)                    │   │
│ │                                              │   │
│ │ [Unit 1 - Main production unit ▼]           │   │
│ │                                              │   │
│ │ ✓ Suggested based on machine skills         │   │
│ │   (3 machines in Unit 1, 2 in Unit 2)       │   │
│ └─────────────────────────────────────────────┘   │
│                                                     │
│ Notes: [Optional notes...]                          │
│                                                     │
│ [✓ Approve]  [✗ Reject]                             │
└─────────────────────────────────────────────────────┘
```

### **Admin Clicks "Approve":**
1. System validates that a unit is selected
2. Updates `users.unit_id` = selected unit
3. Updates `users.approval_status` = 'approved'
4. Updates `user_approvals.status` = 'approved'
5. User can now log in

---

## 📊 Complete Flow Diagram

```
NEW USER REGISTRATION:
═══════════════════════════════════════════════════════

1. /signup (Step 1)
   ├─ User creates username & password
   ├─ User enters personal details
   └─ Click "Next"

2. /signup/skills (Step 2)
   ├─ User sees ALL machines from both units
   ├─ User selects machines they can operate
   ├─ User sets skill level for each
   ├─ NO unit selection
   └─ Click "Submit for Approval"

3. Account Created
   ├─ approval_status = 'pending'
   ├─ unit_id = NULL (not assigned yet)
   ├─ Machine skills saved
   └─ Redirect to login

4. User Tries Login
   └─ ❌ FAILS: "Pending admin approval"

ADMIN APPROVAL:
═══════════════════════════════════════════════════════

5. Admin Reviews User
   ├─ Views user details
   ├─ Views machine skills with unit info
   ├─ System suggests unit based on skills
   └─ Admin selects/confirms unit

6. Admin Clicks "Approve"
   ├─ Update user.unit_id = selected unit
   ├─ Update approval_status = 'approved'
   └─ User notified

7. User Logs In Successfully
   ├─ approval_status = 'approved' ✓
   ├─ unit_id assigned ✓
   └─ Redirect to dashboard
```

---

## 🔧 Technical Changes Made

### **Frontend:**

1. **`SignupSkills.jsx`** (Updated)
   - Removed unit selection UI
   - Changed to show ALL machines from both units
   - Added unit indicator next to each machine name
   - Removed `unit_id` from signup data
   - Updated success message

2. **`UserApprovals.jsx`** (Updated)
   - Added unit dropdown for admin
   - Added automatic unit suggestion logic
   - Shows which unit each machine belongs to
   - Updates user's `unit_id` before approving
   - Added validation to require unit selection

### **Backend:**

1. **`users_model.py`** (Updated)
   - Added `unit_id` to `UserUpdate` model
   - Allows admin to update user's unit during approval

2. **`users_router.py`** (No changes needed)
   - Existing PUT endpoint already supports updating unit_id

3. **`models_db.py`** (Already correct)
   - `User.unit_id` field already exists
   - Allows NULL values (for pending users)

---

## ✅ Benefits of This Approach

1. **Logical Assignment:**
   - Admin assigns units based on actual machine skills
   - Users don't need to know which unit to choose

2. **Intelligent Suggestions:**
   - System automatically suggests the best unit
   - Based on which machines the user selected
   - Admin can override if needed

3. **Flexibility:**
   - Users can select machines from any unit
   - Admin makes final decision based on:
     - Machine skills
     - Unit capacity
     - Business needs

4. **Better Matching:**
   - Users are assigned to units where their skills are most needed
   - Reduces skill mismatches

---

## 🎯 Summary

**Old Flow:**
- User selects unit → User selects machines from that unit → Admin approves

**New Flow:**
- User selects machines from ALL units → Admin assigns unit based on skills → Admin approves

**Key Improvement:**
Admin has full control over unit assignment and can make informed decisions based on the user's actual machine skills, not the user's arbitrary choice.

---

## 📝 Testing the New Flow

1. **Start the application:**
   ```bash
   # Terminal 1 - Backend
   cd backend
   uvicorn app.main:app --reload

   # Terminal 2 - Frontend
   cd frontend
   npm run dev
   ```

2. **Test User Signup:**
   - Visit http://localhost:5173/signup
   - Fill basic info (Step 1)
   - Select machines from different units (Step 2)
   - Notice: No unit selection!
   - Submit for approval

3. **Test Admin Approval:**
   - Login as admin (`admin` / `admin123`)
   - Visit http://localhost:5173/admin/approvals
   - See user's machine skills with unit indicators
   - Notice: System suggests a unit
   - Select unit and approve

4. **Test User Login:**
   - User can now log in successfully
   - User is assigned to the selected unit

**Everything is now working as intended!** 🎉
