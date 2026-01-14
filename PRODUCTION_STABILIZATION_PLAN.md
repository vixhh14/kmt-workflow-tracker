# PRODUCTION-GRADE STABILIZATION PLAN
## Zero-Error Contract · Full Consistency

### CRITICAL FINDINGS

**ROOT CAUSE OF "ALL ZEROS" BUG:**
- System has 3 separate task tables: `tasks`, `filing_tasks`, `fabrication_tasks`
- Dashboard analytics (`dashboard_analytics_service.py`) only queries `tasks` table
- Operational tasks (Filing/Fabrication) are invisible to overview counts
- This breaks the Single Source of Truth principle

**ARCHITECTURAL DECISION REQUIRED:**
The user must choose ONE of these approaches:

### OPTION A: UNIFIED TASK TABLE (RECOMMENDED)
**Pros:**
- Single source of truth
- Consistent aggregation
- Simpler queries
- No data duplication

**Cons:**
- Requires data migration
- One-time downtime

**Implementation:**
1. Add `task_type` column to `tasks` table ('general', 'filing', 'fabrication')
2. Migrate data from `filing_tasks` and `fabrication_tasks` to `tasks`
3. Update all CRUD endpoints to use unified table
4. Drop old tables after verification

### OPTION B: AGGREGATED VIEW (QUICK FIX)
**Pros:**
- No migration needed
- Preserves existing structure
- Faster deployment

**Cons:**
- Ongoing complexity
- Multiple query points
- Harder to maintain

**Implementation:**
1. Update `dashboard_analytics_service.py` to query all 3 tables
2. Create database VIEW for unified task counts
3. Update all dashboard endpoints to use aggregated logic

---

## IMMEDIATE FIXES (REGARDLESS OF OPTION)

### 1. SOFT DELETE CONSISTENCY
**Problem:** Inconsistent `is_deleted` checks across codebase
**Fix:** Use `or_(Model.is_deleted == False, Model.is_deleted == None)` everywhere

### 2. OPERATOR DROPDOWN EMPTY
**Problem:** Over-filtering operators by task existence
**Fix:** Load operators independently from tasks table

### 3. MACHINE DATA EMPTY  
**Problem:** Machine list depends on task joins
**Fix:** Load machines directly, calculate status separately

### 4. DROPDOWNS DON'T FILTER
**Problem:** Frontend sends filters but backend ignores them
**Fix:** Already partially fixed with UUID validation - needs frontend verification

### 5. DEADLINE TIME ALWAYS 09:00 AM
**Problem:** Frontend not preserving time component
**Fix:** Ensure `due_date` and `due_time` are combined correctly in payload

### 6. SUPERVISOR CANNOT END TASKS
**Status:** ✅ ALREADY FIXED in tasks_router.py

### 7. DELETED USERS STILL AFFECT SYSTEM
**Fix:** Exclude `is_deleted = True` users from:
- Dropdowns
- Graphs
- Counts
- Assignments

### 8. PROFILE EDIT UNRELIABLE
**Status:** ✅ ALREADY WORKING (verified in auth_router.py)

### 9. FORGOT PASSWORD "USER NOT FOUND"
**Status:** ✅ ALREADY FIXED (supports username OR email lookup)

---

## RECOMMENDED IMPLEMENTATION ORDER

### PHASE 1: IMMEDIATE STABILITY (TODAY)
1. Fix dashboard aggregation to include all 3 task tables
2. Fix operator dropdown to load independently
3. Fix machine status calculation
4. Verify dropdown filtering end-to-end

### PHASE 2: DATA CONSISTENCY (NEXT)
1. Decide on Option A or B
2. If Option A: Plan migration window
3. If Option B: Implement aggregated views

### PHASE 3: VERIFICATION
1. Test all dashboards with real data
2. Verify counts match database
3. Confirm dropdowns filter correctly
4. Validate deadline times preserve exact input

---

## QUESTIONS FOR USER

1. **Do you want to unify the 3 task tables into one?** (Recommended but requires migration)
2. **What is your preferred downtime window?** (If choosing Option A)
3. **Are there any other task types beyond general/filing/fabrication?**

---

## FILES REQUIRING CHANGES

### Backend (Option B - Quick Fix):
- `app/services/dashboard_analytics_service.py` - Aggregate all 3 tables
- `app/routers/unified_dashboard_router.py` - Update overview logic
- `app/routers/supervisor_router.py` - Fix operator dropdown query

### Frontend:
- `SupervisorDashboard.jsx` - Verify filter state management
- `OperationalDashboard.jsx` - Verify deadline time handling

### Database (Option A - If chosen):
- Migration script to unify tables
- Backup script before migration
- Rollback plan

---

**AWAITING USER DECISION ON ARCHITECTURAL APPROACH**
