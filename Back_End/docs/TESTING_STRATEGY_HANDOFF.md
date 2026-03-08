# TimeWeaver - Testing Strategy Handoff Document

> **Purpose:** Everything your testing teammate needs to understand the current test state and plan the testing strategy.

> [!IMPORTANT]
> **Frontend and backend are NOT yet integrated.** Tests currently validate each repo independently. Integration/E2E tests cannot be written until the two repos are connected — see [DEVOPS_HANDOFF.md Section 13](./DEVOPS_HANDOFF.md) for the integration plan.

---

## 1. Current Test Infrastructure

### Backend (`timeweaver_backend`)

| Item | Details |
|------|---------|
| **Framework** | pytest + pytest-asyncio |
| **Test DB** | `timeweaver_test` (PostgreSQL, async via asyncpg) |
| **HTTP Client** | `httpx.AsyncClient` with ASGI transport (no real server needed) |
| **Mocking** | `unittest.mock` (AsyncMock, MagicMock) |
| **Config** | `pytest.ini` — auto async mode, strict markers, verbose output |
| **Run command** | `pytest tests/ -v` |
| **Coverage** | Not configured (no `--cov` in `pytest.ini`) |

### Frontend (`timeweaver_frontend`)

| Item | Details |
|------|---------|
| **Framework** | Jest + JSDOM |
| **Environment** | JSDOM (browser API simulation) |
| **Setup file** | `tests/setup.js` — mocks `localStorage`, `sessionStorage`, `fetch`, `alert`, `confirm` |
| **Run command** | `npm test` |
| **Coverage** | Configured in `jest.config.js` (50% threshold on branches/functions/lines/statements) |
| **Coverage paths** | `src/**/*.js`, excludes minified and legacy files |

---

## 2. Existing Test Inventory

### Backend Test Files (9 files, ~160 tests)

| File | Tests | Type | What It Covers | Quality |
|------|-------|------|----------------|---------|
| `conftest.py` | — | Fixtures | DB session, admin user, auth tokens, sample data (semester, timetable, rooms, time slots, sections) | ⚠️ Hardcoded DB password, duplicate import |
| `test_phase10_apis.py` | ~30 | Integration | Rules CRUD, timetable generation/listing, slot locking, faculty leaves | ✅ Solid — hits real DB via test client |
| `test_phase10_edge_cases.py` | ~46 | Integration | Invalid inputs, boundary conditions, SQL injection, XSS, large payloads, concurrent requests | ✅ Thorough edge coverage |
| `test_timetable_models.py` | 22 | Unit (DB) | Timetable, TimetableSlot, Conflict model creation, validation, cascade deletes | ✅ Good — tests DB constraints directly |
| `test_timetable_schemas.py` | ~34 | Unit | Pydantic schema validation for TimetableCreate, SlotLockRequest, FacultyLeaveRequest, responses | ✅ Good coverage of validation rules |
| `test_faculty.py` | 17 | Unit | Faculty CRUD, preferences, model creation, RBAC | ❌ **7 tests are empty stubs** (`pass` body) |
| `test_workload.py` | 9 | Unit | WorkloadCalculator — normal/overloaded/zero/null scenarios | ✅ Good edge cases |
| `test_preference_weighting.py` | 2 | Unit | PreferenceWeightProvider — empty DB + with preferences | ⚠️ Minimal (only 2 tests) |
| `test_substitute_recommender.py` | 2 | Unit | SubstituteRecommender — empty DB + filter unavailable | ⚠️ Minimal (only 2 tests) |
| `utils.py` | — | Helper | Concurrency test session factory | — |

### Frontend Test Files (4 files)

| File | Tests | Type | What It Covers | Quality |
|------|-------|------|----------------|---------|
| `services/facultyService.test.js` | ~15 | Unit | All `facultyService` methods — CRUD, preferences, network errors, auth errors | ✅ Well-structured, mocks Axios |
| `academic_setup/courses.test.js` | ~10 | Unit | Course form fields, tutorial_hours, table rendering, form validation | ✅ DOM + API coverage |
| `academic_setup/departments.test.js` | ~15 | Unit | Department CRUD, form validation, DOM rendering, search, error handling | ✅ Good coverage |
| `pages/faculty/Dashboard.test.jsx` | ~10 | Unit | FacultyDashboard component — render, workload, overload, loading, error states | ⚠️ Uses React Testing Library (`render`, `screen`, `fireEvent`) but project is vanilla JS — **these tests won't run** |

---

## 3. Issues Found in Existing Tests

### 🔴 Critical

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 1 | **Hardcoded DB password in test fixtures** | `conftest.py:48` — `luckypandu911` | Security risk if repo is public. Should use env var. |
| 2 | **`Dashboard.test.jsx` imports React Testing Library** | `tests/pages/faculty/Dashboard.test.jsx` | These tests **cannot run** — the project uses vanilla JS, not React. File uses JSX syntax, `render()`, `screen`, `fireEvent`, `waitFor` which require `@testing-library/react` (not installed). |
| 3 | **7 empty test stubs in `test_faculty.py`** | `test_get_faculty_list`, `test_get_faculty_detail`, `test_delete_faculty`, `test_get_faculty_preferences`, `test_update_preference`, `test_delete_preference`, `test_faculty_authorization_checks` | These tests have docstrings but `pass` as the body. They inflate test count without validating anything. |

### 🟡 Significant

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 4 | **Duplicate import** | `conftest.py:11-12` — `from app.main import app` imported twice | Minor — no functional impact |
| 5 | **Hardcoded API URL in frontend tests** | `courses.test.js:7`, `departments.test.js:7` — `http://localhost:8000/api/v1` | Should reference config or constants, not hardcode |
| 6 | **No test coverage configured for backend** | `pytest.ini` has no `--cov` flag | Can't track what's tested vs not |
| 7 | **AuditLoggingMiddleware disabled in tests** | `conftest.py:108-113` | Middleware is explicitly removed during testing due to `BaseHTTPMiddleware`/`anyio` conflicts. Audit logging behavior is never tested. |
| 8 | **`cleanup_test_data` fixture is a no-op** | `conftest.py:290-298` | Autouse fixture that does nothing — relies on `test_db` rollback instead |

---

## 4. Test Coverage Gaps

### Backend — What's NOT Tested

| Area | Endpoints/Functions | Priority |
|------|--------------------|----------|
| **Auth endpoints** | `POST /auth/login`, `POST /auth/register`, `POST /auth/logout`, `POST /auth/forgot-password`, `POST /auth/reset-password` | 🔴 **Critical** — auth is the #1 attack surface |
| **User CRUD** | `GET/POST/PUT/DELETE /users/` (8 endpoints) | 🟡 High |
| **Semester/Department/Room/TimeSlot CRUD** | All basic entity endpoints | 🟡 High |
| **Course CRUD** | `GET/POST/PUT/DELETE /courses/` | 🟡 High |
| **Section CRUD** | `GET/POST/PUT/DELETE /sections/` | 🟡 High |
| **Curriculum management** | All `/curriculums/` endpoints | 🟡 Medium |
| **Constraint management** | All `/constraints/` endpoints | 🟡 Medium |
| **Genetic Algorithm core** | `GeneticAlgorithm` class — crossover, mutation, fitness calculation | 🔴 **Critical** — core business logic |
| **Audit middleware** | Logging behavior, IP extraction, user identification | 🟠 Medium |
| **RBAC / role-based access** | Faculty/student role restrictions across endpoints | 🟡 High |
| **Password hashing** | `verify_password`, `get_password_hash` | 🟠 Medium |
| **JWT token** | Token creation, expiry, invalid token handling | 🔴 **Critical** |

### Frontend — What's NOT Tested

| Area | Priority |
|------|----------|
| **Login page** (`login.html`) | 🔴 Critical |
| **Admin dashboard** (`dashboard/admin_dashboard/`) | 🟡 High |
| **Student dashboard** (`dashboard/student_dashbord/`) | 🟡 High |
| **Conflict dashboard** (`dashboard/conflict_dashboard/`) | 🟡 High |
| **Academic setup pages** (beyond courses/departments) | 🟡 Medium |
| **`server.js` Express routes** (login/register/create-user) | 🟡 Medium (will be removed at integration) |
| **`api.js` interceptor** (token attachment, error handling) | 🟡 High |
| **WorkloadChart component** (`components/WorkloadChart/`) | 🟠 Medium |

---

## 5. Test Architecture

### Backend Test Fixture Flow

```
pytest.ini
  └─ conftest.py
       ├─ event_loop (session scope)
       ├─ test_db → creates timeweaver_test DB tables
       │     ├─ drops all → creates all (fresh per test)
       │     └─ yields AsyncSession → rollback on teardown
       ├─ setup_admin → inserts admin user
       ├─ client → AsyncClient with ASGI transport
       │     ├─ overrides get_db dependency
       │     └─ strips AuditLoggingMiddleware
       ├─ admin_token → logs in via /auth/login
       ├─ auth_headers → {"Authorization": "Bearer <token>"}
       └─ sample data fixtures
             ├─ sample_semester (Fall 2024)
             ├─ sample_timetable
             ├─ sample_rooms (2 rooms)
             ├─ sample_time_slots (2 slots)
             └─ sample_sections (1 section with course)
```

### Frontend Test Setup

```
jest.config.js
  ├─ testEnvironment: jsdom
  ├─ testMatch: **/tests/**/*.test.js
  ├─ setupFiles: tests/setup.js
  │     ├─ mocks localStorage, sessionStorage
  │     ├─ mocks fetch API
  │     ├─ mocks alert, confirm, prompt
  │     └─ beforeEach: clearAllMocks + fake token
  └─ coverageThreshold: 50% (all metrics)
```

---

## 6. How to Run Tests

### Backend

```bash
# Prerequisite: PostgreSQL running, timeweaver_test DB exists
# Create test database (one-time):
# psql -U postgres -c "CREATE DATABASE timeweaver_test;"

# Activate venv
cd timeweaver_backend
.\venv\Scripts\activate        # Windows
source venv/bin/activate       # Linux/Mac

# Run all tests
pytest tests/ -v

# Run specific file
pytest tests/test_phase10_apis.py -v

# Run specific class
pytest tests/test_timetable_models.py::TestTimetableModel -v

# Run with coverage (need to add pytest-cov)
pip install pytest-cov
pytest tests/ --cov=app --cov-report=html
```

### Frontend

```bash
cd timeweaver_frontend
npm install
npm test                    # Run all tests
npm run test:coverage       # Run with coverage report
npm run test:watch          # Watch mode
npm run test:verbose        # Verbose output
```

---

## 7. Recommended Testing Strategy

### Priority Order for New Tests

```
Priority 1 (Security): Auth + JWT tests
    ↓
Priority 2 (Core Logic): GA algorithm + timetable generation
    ↓
Priority 3 (CRUD): Entity endpoint tests (users, courses, semesters, etc.)
    ↓
Priority 4 (Frontend): Login, dashboards, API client
    ↓
Priority 5 (Integration): Frontend ↔ Backend E2E tests (post-integration)
```

### Recommended Test Types

| Type | Backend Tool | Frontend Tool | When |
|------|-------------|---------------|------|
| **Unit tests** | pytest + mock | Jest + JSDOM | Now |
| **Integration tests** | pytest + httpx (AsyncClient) | Jest + mock fetch | Now |
| **E2E tests** | — | Playwright / Cypress | After integration |
| **Load tests** | locust / k6 | — | After deployment |
| **Security tests** | pytest (existing edge cases) | — | Now |

### Fix These First

| # | Action | Effort |
|---|--------|--------|
| 1 | Move DB password from `conftest.py` to env var | 5 min |
| 2 | Remove duplicate import in `conftest.py` | 1 min |
| 3 | Fill in the 7 empty `test_faculty.py` stubs or delete them | 1-2 hrs |
| 4 | Delete `Dashboard.test.jsx` or rewrite for vanilla JS | 30 min |
| 5 | Add `pytest-cov` to `requirements.txt` + configure in `pytest.ini` | 10 min |
| 6 | Extract hardcoded API URL in frontend tests to a constant | 10 min |
| 7 | Write auth endpoint tests (login, register, token expiry, invalid creds) | 2-3 hrs |
| 8 | Write GA algorithm unit tests (crossover, mutation, fitness) | 3-4 hrs |

---

## 8. Test File Naming Conventions

### Backend (Current Pattern)
```
tests/
├── conftest.py                    # Shared fixtures
├── utils.py                       # Concurrency helpers
├── test_<feature>.py              # Feature-level tests
├── test_<feature>_<aspect>.py     # Specific aspect
└── test_models/                   # Model-only tests (subdirectory)
```

### Frontend (Current Pattern)
```
tests/
├── setup.js                       # Global mocks
├── services/                      # API service tests
│   └── facultyService.test.js
├── academic_setup/                # Module tests
│   ├── courses.test.js
│   └── departments.test.js
└── pages/                         # Page/component tests
    └── faculty/
        └── Dashboard.test.jsx     # ⚠️ Should be .test.js
```

---

## 9. Environment Variables for Testing

### Backend Test Environment

| Variable | Current Value (hardcoded) | Should Be |
|----------|--------------------------|-----------|
| Test DB URL | `postgresql+asyncpg://postgres:luckypandu911@localhost:5432/timeweaver_test` | `TEST_DATABASE_URL` env var |
| Admin password | `admin123` | Fine for test fixtures |
| Concurrency pool | `pool_size=10, max_overflow=20` (in `utils.py`) | Fine — uses production `DATABASE_URL` with asyncpg transform |

### Frontend Test Environment

| Variable | Current Value | Notes |
|----------|--------------|-------|
| API URL | `http://localhost:8000/api/v1` (hardcoded) | Should be configurable |
| Auth token | `'fake-token'` (via `setup.js` mock) | Fine for unit tests |
