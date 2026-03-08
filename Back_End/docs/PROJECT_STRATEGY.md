# TimeWeaver — Full Project Strategy

> Prioritized roadmap of everything that needs to be fixed and built, ordered by dependency and impact.

---

## Phase 0: Critical Fixes (Do First — 1-2 days)

> [!CAUTION]
> These are security and correctness issues that should be resolved before any new feature work.

| # | Task | Repo | File(s) | Status |
|---|------|------|---------|--------|
| 0.1 | **Remove hardcoded DB password from test fixtures** | Backend | `tests/conftest.py` | ✅ Uses `os.getenv("TEST_DATABASE_URL")` |
| 0.2 | **Remove hardcoded password from `.env`** | Backend | `.env` | ✅ Password replaced, `.env` in `.gitignore` |
| 0.3 | **Change `SECRET_KEY` from dev value** | Backend | `.env` | ✅ Rotated to 64-byte random key |
| 0.4 | **Remove reset token from API response** | Backend | `auth.py` | ✅ Token no longer leaked in response |
| 0.5 | **Fix `datetime.utcnow()` deprecation** | Backend | `security.py`, models | ✅ 5 files → `datetime.now(timezone.utc)` |
| 0.6 | **Remove duplicate import** | Backend | `conftest.py` | ✅ Done |
| 0.7 | **Fix broken docstring** | Backend | `audit_middleware.py` | ✅ Done |
| 0.8 | **Delete or rewrite `Dashboard.test.jsx`** | Frontend | `tests/pages/faculty/` | ⬜ Pending |
| 0.9 | **Fix directory typo** | Frontend | `student_dashbord/` | ✅ Already fixed |

---

## Phase 1: Frontend-Backend Integration (Top Priority — 3-5 days)

> [!IMPORTANT]
> The two repos currently run independently. This is the #1 blocker for the project being functional end-to-end.

### 1A. Auth Migration (Day 1-2)

| # | Task | Details |
|---|------|---------|
| 1.1 | **Update login page to call backend API** | `login.html` → call `POST /api/v1/auth/login`, store JWT in localStorage |
| 1.2 | **Remove Express auth routes** from `server.js` | Delete `/api/auth/login`, `/api/auth/register`, `/api/admin/create-user` routes |
| 1.3 | **Remove direct `pg` connection** from `server.js` | Remove `pg` and `bcrypt` deps from `src/package.json` |
| 1.4 | **Delete `src/db/schema.sql`** | Backend owns the schema via Alembic |
| 1.5 | **Add `.env.example`** to frontend repo | Document `PORT` and `API_BASE_URL` |
| 1.6 | **Fix module system conflict** | Either convert `server.js` to ES modules or add a bundler for `api.js`/`facultyService.js` |

### 1B. Dashboard API Integration (Day 2-4)

| # | Dashboard | Current State | Connect To |
|---|-----------|--------------|------------|
| 1.7 | **Admin dashboard** | Reads/writes `localStorage` | `GET/POST /api/v1/timetables`, `GET /api/v1/faculty`, rooms, rules |
| 1.8 | **Faculty dashboard** | Reads `localStorage` + dropdown login | `GET /api/v1/faculty/{id}/workload`, `GET /timetables/{id}/view?faculty_id=X` |
| 1.9 | **Student dashboard** | Reads `localStorage` | `GET /api/v1/timetables/{id}/view?section_id=X` |
| 1.10 | **Conflict dashboard** | Copy-paste of admin dashboard | Build real UI using `GET /api/v1/timetables/{id}/conflicts` |
| 1.11 | **Academic setup pages** | Already have `api.js` client | Wire up to semester, room, time-slot, section CRUD endpoints |

### 1C. Cleanup (Day 4-5)

| # | Task |
|---|------|
| 1.12 | Delete `src/legacy/app.js` (mock data, localStorage-only) |
| 1.13 | Clean up empty dirs: `src/utils/`, `src/pages/admin/` |
| 1.14 | Deduplicate conflict dashboard (currently identical to admin dashboard) |
| 1.15 | Consolidate to single `package.json` (currently split between root and `src/`) |

---

## Phase 2: Missing Frontend Pages (3-5 days)

These backend APIs exist but have **no frontend UI at all**:

| # | Page | Backend Endpoints | Priority |
|---|------|------------------|----------|
| 2.1 | **User Management** (admin) | `GET/POST/PUT/DELETE /users` (8 endpoints) | 🔴 High — needed for admin to manage accounts |
| 2.2 | **Semester Setup** | `GET/POST/PUT/DELETE /semesters` (5 endpoints) | 🔴 High — prerequisite for timetable generation |
| 2.3 | **Room Management** | `GET/POST/PUT/DELETE /rooms` (5 endpoints) | 🔴 High — prerequisite for timetable generation |
| 2.4 | **Time Slot Config** | `GET/POST/PUT/DELETE /time-slots` (5 endpoints) | 🔴 High — prerequisite for timetable generation |
| 2.5 | **Section Management** | `GET/POST/PUT/DELETE /sections` (5 endpoints) | 🔴 High — prerequisite for timetable generation |
| 2.6 | **Institutional Rules** | `GET/POST/PUT/DELETE /rules`, toggle (6 endpoints) | 🟡 Medium — enhances generation quality |
| 2.7 | **Constraint Editor** | `GET/POST/PUT/DELETE /constraints` (6 endpoints) | 🟡 Medium |
| 2.8 | **Curriculum Builder** | `GET/POST/PUT/DELETE /curriculums` (7 endpoints) | 🟡 Medium |
| 2.9 | **Faculty Leave Management** | `GET/POST /faculty-leaves`, analyze (6 endpoints) | 🟡 Medium |
| 2.10 | **Substitute Recommendations** | `GET /faculty-leaves/{id}/substitutes` (2 endpoints) | 🟠 Low |
| 2.11 | **Audit Log Viewer** (admin) | `GET /audit-logs` (2 endpoints) | 🟠 Low |
| 2.12 | **Slot Locking UI** | `POST/GET/DELETE /slot-locks` (3 endpoints) | 🟠 Low — feature on timetable viewer |

---

## Phase 3: Backend Hardening (2-3 days, can run in parallel with Phase 2)

### 3A. Security

| # | Task | Effort |
|---|------|--------|
| 3.1 | **Add token blacklist for logout** — currently JWT stays valid after logout | 2-3 hrs |
| 3.2 | **Stop trusting `X-Forwarded-For`** without reverse proxy validation | 30 min |
| 3.3 | **Add rate limiting** on auth endpoints (brute force protection) | 1-2 hrs |
| 3.4 | **Move JWT storage to httpOnly cookie** (or document XSS risk of localStorage) | 2-3 hrs |
| 3.5 | **Remove duplicate `hash_password`/`get_password_hash`** functions | 15 min |

### 3B. Performance

| # | Task | Effort |
|---|------|--------|
| 3.6 | **Make timetable generation async** — run GA in background task (Celery/ARQ) | 4-6 hrs |
| 3.7 | **Add generation progress tracking** — WebSocket or polling endpoint | 2-3 hrs |
| 3.8 | **Add request timeout** for `/timetables/generate` | 30 min |

### 3C. Code Quality

| # | Task | Effort |
|---|------|--------|
| 3.9 | **Move manual migration scripts into Alembic** (`scripts/create_faculty_leaves_table.py`) | 1 hr |
| 3.10 | **Add input validation middleware** to frontend `server.js` routes (while they still exist) | 1 hr |

---

## Phase 4: Testing (2-3 days, can run in parallel)

### 4A. Fix Existing Tests

| # | Task | Effort |
|---|------|--------|
| 4.1 | Fill in 7 empty test stubs in `test_faculty.py` | 1-2 hrs |
| 4.2 | Move test DB URL to env var (remove hardcoded password from `conftest.py`) | 10 min |
| 4.3 | Add `pytest-cov` and configure coverage reporting | 10 min |
| 4.4 | Extract hardcoded API URL from frontend tests to a constant | 10 min |

### 4B. Write Missing Tests (Priority Order)

| # | What to Test | Type | Effort |
|---|-------------|------|--------|
| 4.5 | **Auth endpoints** (login, register, token expiry, invalid creds, logout) | Integration | 2-3 hrs |
| 4.6 | **JWT token handling** (creation, validation, expiry, tampered tokens) | Unit | 1-2 hrs |
| 4.7 | **GA algorithm** (crossover, mutation, fitness function, constraint checking) | Unit | 3-4 hrs |
| 4.8 | **RBAC across all endpoints** (admin vs faculty vs student access) | Integration | 2-3 hrs |
| 4.9 | **Entity CRUD** (users, semesters, courses, rooms, sections, time-slots) | Integration | 3-4 hrs |
| 4.10 | **Frontend login flow** | Jest + DOM | 1-2 hrs |
| 4.11 | **Frontend dashboard rendering** | Jest + DOM | 2-3 hrs |

### 4C. Future Testing (Post-Integration)

| # | What | Tool |
|---|------|------|
| 4.12 | End-to-end tests (login → create semester → generate timetable → view) | Playwright |
| 4.13 | Load testing on timetable generation | Locust / k6 |

---

## Phase 5: DevOps & Deployment (2-3 days)

| # | Task | Effort |
|---|------|--------|
| 5.1 | **Create `Dockerfile`** for backend (FastAPI + uvicorn) | 1-2 hrs |
| 5.2 | **Create `Dockerfile`** for frontend (Node + Express or static serve) | 1 hr |
| 5.3 | **Create `docker-compose.yml`** (backend + frontend + PostgreSQL) | 1-2 hrs |
| 5.4 | **Set up CI/CD** (GitHub Actions: lint → test → build → deploy) | 2-3 hrs |
| 5.5 | **Add health check endpoints** | 30 min (backend already has `/health`) |
| 5.6 | **Configure HTTPS** (TLS certificates) | 1-2 hrs |
| 5.7 | **Add monitoring/logging** (structured logging, Sentry or similar) | 2-3 hrs |

---

## Dependency Graph

```
Phase 0 (Critical Fixes)
    │
    ▼
Phase 1 (Integration)     Phase 3 (Backend Hardening)     Phase 4 (Testing)
    │                            │                              │
    ▼                            │                              │
Phase 2 (Missing Pages)         │                              │
    │                            │                              │
    └────────────┬───────────────┘──────────────────────────────┘
                 ▼
         Phase 5 (DevOps)
```

**Phases 1, 3, and 4 can run in parallel** if you have multiple team members. Phase 2 depends on Phase 1 (integration must be done first). Phase 5 comes last.

---

## Effort Summary

| Phase | Effort | Can Parallelize? |
|-------|--------|-----------------|
| Phase 0: Critical Fixes | **1-2 days** (1 person) | No — do first |
| Phase 1: Integration | **3-5 days** (1-2 people) | No — blocks Phase 2 |
| Phase 2: Missing Pages | **3-5 days** (2-3 people) | Yes — pages are independent |
| Phase 3: Backend Hardening | **2-3 days** (1 person) | Yes — parallel with Phase 2 |
| Phase 4: Testing | **2-3 days** (1-2 people) | Yes — parallel with Phases 2-3 |
| Phase 5: DevOps | **2-3 days** (1 person) | After everything else |
| **Total** | **~2-3 weeks** with 2-3 people | |
