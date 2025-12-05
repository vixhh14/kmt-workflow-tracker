# User Signup & Login Flow - Complete Walkthrough

## ✅ **YES, Users Create Their Own Username & Password!**

Your system **already works correctly**. Here's the complete flow:

---

## 📝 **SIGNUP FLOW (New User Registration)**

### **Step 1: Visit `/signup` Page**

**What the user sees:**
```
┌─────────────────────────────────────────┐
│        Create Account - Step 1 of 2     │
├─────────────────────────────────────────┤
│                                         │
│  Username: [________________]  *        │  ← User creates their own username
│  Email:    [________________]  *        │
│  Password: [________________]  *        │  ← User creates their own password
│  Confirm:  [________________]  *        │  ← Must match password
│                                         │
│  Full Name:       [________________] *  │
│  Date of Birth:   [________________] *  │
│  Contact Number:  [________________] *  │
│  Address:         [________________] *  │
│                                         │
│  [Next: Select Skills & Machines →]    │
└─────────────────────────────────────────┘
```

**What happens:**
1. User enters **their chosen username** (e.g., "john_doe")
2. User enters **their chosen password** (e.g., "MySecurePass123")
3. User confirms password (must match)
4. User fills personal details
5. Clicks "Next: Select Skills & Machines"
6. Data stored in browser's sessionStorage (temporary)
7. Redirected to `/signup/skills`

**Validation:**
- ✅ Username required
- ✅ Email required and valid format
- ✅ Password minimum 6 characters
- ✅ Passwords must match
- ✅ All fields required

---

### **Step 2: Visit `/signup/skills` Page**

**What the user sees:**
```
┌─────────────────────────────────────────┐
│   Skills & Machines - Step 2 of 2      │
├─────────────────────────────────────────┤
│                                         │
│  Select Your Unit: *                    │
│  ○ Unit 1 (Main production unit)        │
│  ○ Unit 2 (Secondary production unit)   │
│                                         │
│  Select Machines You Can Operate: *     │
│  ┌─────────────────────────────────┐   │
│  │ ▼ Grinder (5 machines)          │   │
│  │   ☑ Hand Grinder    [Expert ▼]  │   │
│  │   ☐ Bench Grinder               │   │
│  │                                  │   │
│  │ ▼ Lathe (4 machines)            │   │
│  │   ☑ Turnmaster   [Intermediate▼]│   │
│  │   ☐ Leader                       │   │
│  │                                  │   │
│  │ ▼ CNC (2 machines)              │   │
│  │   ☑ Zimberman      [Beginner ▼] │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [← Back]  [Submit for Approval]       │
└─────────────────────────────────────────┘
```

**What happens:**
1. User selects their unit (Unit 1 or Unit 2)
2. User checks machines they can operate
3. User selects skill level for each machine
4. Clicks "Submit for Approval"
5. Frontend sends ALL data to backend (including username & password from Step 1)

---

### **Step 3: Backend Creates Account**

**Backend receives:**
```json
{
  "username": "john_doe",           ← User's chosen username
  "password": "MySecurePass123",    ← User's chosen password
  "email": "john@email.com",
  "full_name": "John Doe",
  "date_of_birth": "1990-01-01",
  "address": "123 Main St",
  "contact_number": "1234567890",
  "unit_id": 1,
  "role": "operator"
}
```

**Backend process:**
```python
# 1. Check if username already exists
existing_user = db.query(User).filter(User.username == "john_doe").first()
if existing_user:
    raise HTTPException(detail="Username already exists")

# 2. Hash the password for security
password_hash = hash_password("MySecurePass123")
# Result: "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3"

# 3. Create user account
new_user = User(
    user_id="550e8400-e29b-41d4-a716-446655440000",  # Auto-generated UUID
    username="john_doe",                              # User's chosen username
    password_hash="a665a45920422f9d...",             # Hashed password
    email="john@email.com",
    full_name="John Doe",
    date_of_birth="1990-01-01",
    address="123 Main St",
    contact_number="1234567890",
    unit_id=1,
    role="operator",
    approval_status="pending"  # ← User cannot login yet!
)

# 4. Save to database
db.add(new_user)
db.commit()

# 5. Create approval record
approval = UserApproval(
    user_id=new_user.user_id,
    status="pending"
)
db.add(approval)
db.commit()

# 6. Save machine skills
for machine in selected_machines:
    user_machine = UserMachine(
        user_id=new_user.user_id,
        machine_id=machine.id,
        skill_level=machine.skill_level
    )
    db.add(user_machine)
db.commit()
```

**Response to frontend:**
```json
{
  "message": "User registered successfully. Pending admin approval.",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe"
}
```

---

### **Step 4: User Redirected to Login**

**What the user sees:**
```
┌─────────────────────────────────────────┐
│  ✅ Registration Successful!            │
│                                         │
│  Your account is pending admin approval.│
│  You will be notified once approved.    │
│                                         │
│  [Go to Login]                          │
└─────────────────────────────────────────┘
```

User is redirected to `/login` page.

---

## 🔐 **LOGIN FLOW (Before Approval)**

### **User Tries to Login**

**What the user sees:**
```
┌─────────────────────────────────────────┐
│              Login                      │
├─────────────────────────────────────────┤
│                                         │
│  Username: [john_doe___]                │  ← Uses their chosen username
│  Password: [***********]                │  ← Uses their chosen password
│                                         │
│  [Login]                                │
└─────────────────────────────────────────┘
```

**Backend process:**
```python
# 1. Find user by username
user = db.query(User).filter(User.username == "john_doe").first()

# 2. Check if user exists
if not user:
    raise HTTPException(detail="Incorrect username or password")

# 3. Check approval status ← IMPORTANT!
if user.approval_status == "pending":
    raise HTTPException(
        status_code=403,
        detail="Your account is pending admin approval. Please wait for approval before logging in."
    )

# 4. Verify password
is_valid = verify_password("MySecurePass123", user.password_hash)
if not is_valid:
    raise HTTPException(detail="Incorrect username or password")

# Password is correct, but user is pending approval
# Login FAILS with message
```

**User sees error:**
```
┌─────────────────────────────────────────┐
│  ❌ Login Failed                        │
│                                         │
│  Your account is pending admin approval.│
│  Please wait for approval before        │
│  logging in.                            │
│                                         │
│  [OK]                                   │
└─────────────────────────────────────────┘
```

---

## 👨‍💼 **ADMIN APPROVAL FLOW**

### **Admin Reviews User**

Admin logs in and visits `/admin/approvals`:

```
┌─────────────────────────────────────────────────────────┐
│              User Approvals                             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ▼ John Doe                                             │
│     @john_doe • john@email.com                          │
│                                                         │
│     Date of Birth:    1990-01-01                        │
│     Contact Number:   1234567890                        │
│     Address:          123 Main St                       │
│     Unit:             Unit 1                            │
│     Applied On:       2025-11-25                        │
│                                                         │
│     Machine Skills (3 machines):                        │
│     • Hand Grinder (Expert)                             │
│     • Turnmaster (Intermediate)                         │
│     • Zimberman (Beginner)                              │
│                                                         │
│     Notes: [Optional notes about approval...]           │
│                                                         │
│     [✓ Approve]  [✗ Reject]                             │
└─────────────────────────────────────────────────────────┘
```

**Admin clicks "Approve":**
```python
# Backend updates database
UPDATE users 
SET approval_status = 'approved' 
WHERE user_id = '550e8400-e29b-41d4-a716-446655440000'

UPDATE user_approvals 
SET status = 'approved', 
    approved_by = 'admin', 
    approved_at = CURRENT_TIMESTAMP
WHERE user_id = '550e8400-e29b-41d4-a716-446655440000'
```

---

## ✅ **LOGIN FLOW (After Approval)**

### **User Tries to Login Again**

**Same login form:**
```
┌─────────────────────────────────────────┐
│              Login                      │
├─────────────────────────────────────────┤
│                                         │
│  Username: [john_doe___]                │  ← Same username they created
│  Password: [***********]                │  ← Same password they created
│                                         │
│  [Login]                                │
└─────────────────────────────────────────┘
```

**Backend process:**
```python
# 1. Find user by username
user = db.query(User).filter(User.username == "john_doe").first()

# 2. Check approval status
if user.approval_status == "approved":  # ✅ NOW APPROVED!
    
    # 3. Verify password
    is_valid = verify_password("MySecurePass123", user.password_hash)
    if is_valid:
        
        # 4. Create JWT token
        token = create_access_token(
            data={
                "sub": user.username,
                "user_id": user.user_id,
                "role": user.role
            }
        )
        
        # 5. Return success
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "user_id": user.user_id,
                "username": "john_doe",
                "email": "john@email.com",
                "role": "operator",
                "full_name": "John Doe"
            }
        }
```

**User successfully logs in!**
```
Redirected to: /dashboard/operator
```

---

## 📊 **Summary: Complete Flow**

```
NEW USER JOURNEY:
═══════════════════════════════════════════════════════════

1. Visit /signup
   ├─ Create username: "john_doe"          ← USER CHOOSES
   ├─ Create password: "MySecurePass123"   ← USER CHOOSES
   ├─ Fill personal details
   └─ Click "Next"

2. Visit /signup/skills
   ├─ Select Unit 1
   ├─ Select machines & skill levels
   └─ Click "Submit for Approval"

3. Backend creates account
   ├─ Saves username: "john_doe"
   ├─ Hashes password and saves
   ├─ Sets approval_status = "pending"
   └─ Creates approval record

4. User tries to login
   ├─ Enters username: "john_doe"
   ├─ Enters password: "MySecurePass123"
   └─ ❌ FAILS: "Pending admin approval"

5. Admin approves user
   ├─ Reviews user details
   ├─ Clicks "Approve"
   └─ approval_status = "approved"

6. User logs in successfully
   ├─ Enters username: "john_doe"
   ├─ Enters password: "MySecurePass123"
   └─ ✅ SUCCESS: Redirected to dashboard
```

---

## ✅ **Confirmation: Your System is Correct!**

**YES, users create their own credentials:**
- ✅ Username is chosen by the user in Step 1
- ✅ Password is chosen by the user in Step 1
- ✅ Password is validated (min 6 chars, must match confirmation)
- ✅ Password is securely hashed before storage
- ✅ User can login with these credentials after approval
- ✅ System prevents duplicate usernames
- ✅ System prevents duplicate emails

**The flow is exactly as you described:**
1. New user creates username & password
2. User completes signup (2 steps)
3. Account created with "pending" status
4. User cannot login until approved
5. Admin approves user
6. User can now login with their chosen credentials

**Everything is working correctly! 🎉**
