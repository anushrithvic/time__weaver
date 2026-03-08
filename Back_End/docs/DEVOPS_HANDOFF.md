# TimeWeaver - DevOps Handoff Document

> **Purpose:** Everything your DevOps teammate needs to write the DevOps strategy document for the TimeWeaver project (backend + frontend).

---

## 1. Project Overview

**TimeWeaver** is an AI-powered academic timetable generation system for universities. It uses a Genetic Algorithm to auto-generate conflict-free class schedules while respecting constraints (faculty availability, room capacity, workload limits, etc).

| Repo | URL |
|------|-----|
| **Backend** | `https://github.com/Pranathi-N-47/timeweaver_backend` |
| **Frontend** | `https://github.com/Pranathi-N-47/timeweaver_frontend` |

> [!IMPORTANT]
> **The frontend and backend are NOT yet integrated.** They currently operate as independent applications. The frontend runs its own Express server with direct PostgreSQL access for auth. Integration to connect the frontend to the backend API is a pending task — see [Section 13](#13-frontend-backend-integration-plan).

---

## 2. Tech Stack

### Backend (`timeweaver_backend`)

| Layer | Technology | Version |
|-------|-----------|---------|
| **Language** | Python | 3.12 |
| **Framework** | FastAPI | 0.109.0 |
| **ASGI Server** | Uvicorn | 0.27.0 |
| **Database** | PostgreSQL | (latest stable) |
| **ORM** | SQLAlchemy (async) | 2.0.25 |
| **DB Driver (async)** | asyncpg | 0.29.0 |
| **DB Driver (sync)** | psycopg2-binary | 2.9.9 |
| **Migrations** | Alembic | 1.13.1 |
| **Validation** | Pydantic | 2.5.3 |
| **Auth** | python-jose (JWT/HS256) + passlib (bcrypt) | 3.3.0 / 1.7.4 |
| **Testing** | pytest + pytest-asyncio + pytest-cov | 7.4.4 |
| **Linting** | Ruff | 0.1.14 |
| **HTTP Client** | httpx | 0.26.0 |
| **AI/Algorithm** | numpy + networkx | 1.26.3 / 3.2.1 |

### Frontend (`timeweaver_frontend`)

| Layer | Technology | Version |
|-------|-----------|---------|
| **Language** | Vanilla HTML / CSS / JavaScript | ES6+ |
| **Server** | Express.js (Node.js) | 4.18.2 |
| **DB Driver** | pg (node-postgres) | 8.10.0 |
| **Password Hashing** | bcrypt | 5.1.0 |
| **HTTP Client** | Axios (for backend API calls) | — |
| **CORS** | cors middleware | 2.8.5 |
| **Env Config** | dotenv | 16.0.3 |
| **Testing** | Jest + JSDOM + @testing-library/dom | 30.2.0 |
| **Dev Reloading** | nodemon | 2.0.22 |
| **Module Type** | CommonJS | — |

---

## 3. Database Details

| Property | Value |
|----------|-------|
| **Engine** | PostgreSQL |
| **Default DB Name** | `timeweaver_db` |
| **Default User** | `postgres` |
| **Default Port** | `5432` |
| **Connection String** | `postgresql://postgres:<password>@localhost:5432/timeweaver_db` |
| **Async Driver** | `postgresql+asyncpg://` (auto-converted in code) |
| **Migration Tool** | Alembic (`alembic/` directory) |
| **Session Mode** | Async (`AsyncSession`, no autocommit, no autoflush) |

### Database Models (15 tables)

| Model | Table Name | Description |
|-------|------------|-------------|
| `User` | `users` | User accounts with roles (admin/faculty/student) |
| `AuditLog` | `audit_logs` | Tracks all state-changing operations |
| `Semester` | `semesters` | Academic terms |
| `Department` | `departments` | Academic departments |
| `Section` | `sections` | Class sections (e.g., CSE-A) |
| `Course` | `courses` | Course definitions with hours/credits |
| `Room` | `rooms` | Classrooms, labs, auditoriums |
| `TimeSlot` | `time_slots` | Scheduling time blocks |
| `Constraint` | `constraints` | Scheduling rules/constraints |
| `Curriculum` | `curricula` | Course-section mappings |
| `Timetable` | `timetables` | Generated timetable metadata |
| `TimetableSlot` | `timetable_slots` | Individual class assignments |
| `ConflictRecord` | `conflict_records` | Detected scheduling conflicts |
| `InstitutionalRule` | `institutional_rules` | University-wide scheduling rules |
| `Faculty` | `faculty` | Faculty profiles linked to users |
| `FacultyPreference` | `faculty_preferences` | Faculty time slot preferences |
| `FacultyLeave` | `faculty_leaves` | Faculty leave tracking |

---

## 4. Environment Variables

### Backend `.env`
```env
DATABASE_URL=postgresql://postgres:<password>@localhost:5432/timeweaver_db
API_V1_PREFIX=/api/v1
PROJECT_NAME=TimeWeaver API
DEBUG=True                          # Set False in production
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8080","http://localhost:5173"]
SECRET_KEY=<strong-random-key>     # MUST change in production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Frontend `.env` (in `src/`)
```env
DB_USER=postgres
DB_HOST=localhost
DB_NAME=timeweaver_db
DB_PASSWORD=<password>
DB_PORT=5432
PORT=3000                           # Express server port
```

> ⚠️ **Production Concerns:**
> - Backend `SECRET_KEY` must be a strong, unique random value
> - Backend `DEBUG` must be `False`
> - `BACKEND_CORS_ORIGINS` should list only the production frontend URL
> - Both repos should use a dedicated DB user, not `postgres`
> - Frontend server has its own direct DB connection (auth routes) — consider migrating these to use the backend API instead

---

## 5. API Specification

| Property | Value |
|----------|-------|
| **Base URL** | `http://localhost:8000` |
| **API Prefix** | `/api/v1` |
| **Swagger UI** | `http://localhost:8000/docs` |
| **ReDoc** | `http://localhost:8000/redoc` |
| **OpenAPI JSON** | `http://localhost:8000/api/v1/openapi.json` |
| **Health Check** | `GET /health` → `{"status": "healthy"}` |
| **Total Endpoints** | **92** |
| **Auth Mechanism** | JWT Bearer Token (HS256) |
| **Token Lifetime** | 30 minutes |

### Endpoint Summary

| Module | Endpoints | Auth Required |
|--------|-----------|---------------|
| Authentication | 6 | Mixed |
| User Management | 8 | Admin |
| Audit Logs | 2 | Admin |
| Semesters | 5 | Admin (write) / Public (read) |
| Departments | 5 | Admin |
| Sections | 5 | Admin |
| Courses | 5 | Admin |
| Elective Groups | 5 | Admin |
| Rooms | 5 | Admin |
| Time Slots | 5 | Admin |
| Constraints | 6 | Admin |
| Timetables | 7 | Admin (generate) / Any (view) |
| Institutional Rules | 6 | Admin |
| Faculty Management | 6 | Admin (write) / Any (read) |
| Faculty Preferences | 5 | Faculty/Admin |
| Substitutes | 2 | Admin (assign) / Any (view) |
| Faculty Leaves | 6 | Faculty/Admin |
| Slot Locks | 3 | Admin |

> Full API documentation: `docs/API_DOCUMENTATION.md`

### Role-Based Access Control

| Role | Permissions |
|------|-------------|
| **Admin** | Full access to all endpoints |
| **Faculty** | View timetables, set own preferences, apply for leave |
| **Student** | View timetables, view own profile |

---

## 6. Project Structure

### Backend
```
timeweaver_backend/
├── app/
│   ├── main.py                     # FastAPI app entry point
│   ├── core/                       # config.py, security.py, dependencies.py
│   ├── api/v1/
│   │   ├── router.py               # Main API router
│   │   └── endpoints/              # 14 endpoint modules
│   ├── models/                     # 15 SQLAlchemy models
│   ├── schemas/                    # Pydantic request/response schemas
│   ├── services/                   # GA, conflict detection, workload, substitutes
│   ├── middleware/                 # Audit logging middleware
│   └── db/                         # Async engine + session factory
├── alembic/                        # Database migrations
├── tests/                          # pytest test suite
├── docs/                           # Documentation
├── requirements.txt
├── alembic.ini
├── pytest.ini
└── .env                            # Environment variables
```

### Frontend
```
timeweaver_frontend/
├── src/
│   ├── server.js                   # Express.js server (serves static files + auth API)
│   ├── login.html                  # Login page
│   ├── package.json                # Server dependencies (express, pg, bcrypt)
│   ├── components/                 # Reusable UI components
│   ├── pages/
│   │   ├── admin/                  # Admin dashboard pages
│   │   ├── faculty/                # Faculty view pages
│   │   ├── student/                # Student view pages
│   │   └── auth/                   # Auth-related pages
│   ├── services/
│   │   ├── api.js                  # Axios client → backend API (localhost:8000)
│   │   └── facultyService.js       # Faculty-specific API calls
│   ├── dashboard/                  # Dashboard views
│   ├── academic_setup/             # Academic entity management UI
│   ├── db/                         # DB-related frontend utils
│   └── utils/                      # Shared utilities
├── public/
│   ├── index.html                  # Landing page
│   └── style.css                   # Global styles
├── tests/                          # Jest test suite
├── jest.config.js
└── package.json                    # Root deps (jest, testing-library)
```

---

## 7. How to Run

### Backend Setup

```bash
git clone https://github.com/Pranathi-N-47/timeweaver_backend.git
cd timeweaver_backend
python -m venv venv
venv\Scripts\activate          # Windows (source venv/bin/activate on Linux/Mac)
pip install -r requirements.txt && pip install -e .
# Setup PostgreSQL → create timeweaver_db → update .env
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
git clone https://github.com/Pranathi-N-47/timeweaver_frontend.git
cd timeweaver_frontend/src
npm install
# Configure .env with DB_USER, DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT
npm run dev                    # Starts Express server on port 3000 (nodemon)
# OR: npm start               # Without hot-reload
```

### Running Tests

```bash
# Backend
pytest                           # All tests
pytest --cov=app                 # With coverage

# Frontend
npm test                         # Jest tests
npm run test:coverage            # With coverage
```

---

## 8. What Doesn't Exist Yet (DevOps Gaps)

| Item | Status |
|------|--------|
| **Dockerfile** | ❌ Not created |
| **docker-compose.yml** | ❌ Not created |
| **CI/CD Pipeline** | ❌ No GitHub Actions / Jenkins config |
| **Nginx/Reverse Proxy Config** | ❌ Not configured |
| **Production .env template** | ❌ Only dev .env.example exists |
| **Logging to file/service** | ❌ Console-only logging |
| **Rate Limiting** | ❌ Not implemented |
| **HTTPS/SSL** | ❌ Not configured |
| **Database Backups** | ❌ No backup strategy |
| **Monitoring/Alerting** | ❌ Only `/health` endpoint exists |
| **Load Balancing** | ❌ Not configured |

---

## 9. Key Commands Reference

### Backend
| Action | Command |
|--------|---------|
| Start dev server | `uvicorn app.main:app --reload` |
| Run tests | `pytest` |
| Run tests with coverage | `pytest --cov=app` |
| Create migration | `alembic revision --autogenerate -m "description"` |
| Apply migrations | `alembic upgrade head` |
| Rollback migration | `alembic downgrade -1` |
| Lint code | `ruff check app/` |
| Install deps | `pip install -r requirements.txt` |

### Frontend
| Action | Command | CWD |
|--------|---------|-----|
| Start dev server | `npm run dev` | `src/` |
| Start production | `npm start` | `src/` |
| Run tests | `npm test` | root |
| Run tests (coverage) | `npm run test:coverage` | root |
| Install deps (root) | `npm install` | root |
| Install deps (server) | `npm install` | `src/` |

---

## 10. Middleware & Security

- **CORS Middleware**: Configured for frontend origins (3000, 8080, 5173)
- **Audit Logging Middleware**: Automatically logs all POST/PUT/DELETE operations to `audit_logs` table
- **JWT Authentication**: Bearer tokens via `Authorization: Bearer <token>` header
- **Password Hashing**: bcrypt via passlib
- **Token Algorithm**: HS256
- **Token Expiry**: 30 minutes (configurable)

---

## 11. Performance Characteristics

- **Async throughout**: All database operations use `asyncpg` + `AsyncSession`
- **Timetable Generation**: CPU-intensive Genetic Algorithm (population_size=50, max_generations=100)
- **DB Connection Pool**: Managed by SQLAlchemy async engine (defaults)
- **No caching layer**: No Redis/Memcached currently
- **No task queue**: Timetable generation runs synchronously in request (could be long-running)

> ⚠️ **DevOps Consideration:** Timetable generation can take significant time. Consider:
> - Background task queue (Celery + Redis) for generation
> - Longer request timeouts for the `/timetables/generate` endpoint
> - Worker processes sized for CPU-intensive GA computation

---

## 12. Architecture & Network Topology

### Current State (Not Integrated)

The two repos run independently. The frontend has its own Express server with direct DB access for auth.

```
┌─────────────────────┐                            ┌──────────────────────┐
│  Frontend (Express) │         NOT CONNECTED       │  Backend (FastAPI)   │
│  Port: 3000         │      ❌ ─ ─ ─ ─ ─ ─ ❌      │  Port: 8000          │
│  Static HTML/CSS/JS │                            │  92 REST endpoints   │
└────────┬────────────┘                            └──────────┬───────────┘
         │                                                    │
         │ pg (direct, own auth)                asyncpg (async)
         │                                                    │
         ▼                                                    ▼
┌──────────────────┐                            ┌──────────────────┐
│   PostgreSQL     │                            │   PostgreSQL     │
│   (own users     │                            │   timeweaver_db  │
│    table)        │                            │   (full schema)  │
└──────────────────┘                            └──────────────────┘
```

### Target State (After Integration)

All data access goes through the backend API. Frontend becomes a pure static file server.

```
┌─────────────────────┐     API calls (Axios)     ┌──────────────────────┐
│  Frontend (static)  │  ──────────────────────►   │  Backend (FastAPI)   │
│  Port: 3000         │  ◄──────────────────────   │  Port: 8000          │
│  HTML/CSS/JS only   │       JSON responses       │  92 REST endpoints   │
└─────────────────────┘                            └──────────┬───────────┘
                                                              │
                                                    asyncpg (async)
                                                              │
                                                              ▼
                                                   ┌──────────────────┐
                                                   │   PostgreSQL     │
                                                   │   Port: 5432     │
                                                   │   timeweaver_db  │
                                                   └──────────────────┘
```

---

## 13. Frontend-Backend Integration Plan

The following steps are needed to connect the frontend to the backend API:

### Phase 1: Auth Migration
| Step | What to Do | Files Affected |
|------|-----------|----------------|
| 1 | Remove Express auth routes (`/api/auth/login`, `/api/auth/register`, `/api/admin/create-user`) from `server.js` | `src/server.js` |
| 2 | Update login page to call backend `POST /api/v1/auth/login` via the Axios `api.js` client | `src/login.html` |
| 3 | Store JWT token from backend response in `localStorage` (already set up in `api.js` interceptor) | `src/services/api.js` |
| 4 | Remove frontend's direct `pg` database connection from `server.js` | `src/server.js`, `src/package.json` |
| 5 | Delete `src/db/schema.sql` (backend owns the schema via Alembic) | `src/db/schema.sql` |

### Phase 2: API Integration
| Step | What to Do | Files Affected |
|------|-----------|----------------|
| 6 | Connect admin dashboard pages to backend CRUD endpoints (semesters, departments, sections, courses, rooms, time-slots) | `src/pages/admin/`, `src/academic_setup/` |
| 7 | Connect faculty dashboard to backend faculty endpoints (already prepared in `facultyService.js`) | `src/dashboard/faculty_dashboard/` |
| 8 | Connect student dashboard to backend timetable view endpoints | `src/dashboard/student_dashbord/` |
| 9 | Connect timetable generation UI to `POST /api/v1/timetables/generate` | `src/dashboard/admin_dashboard/` |
| 10 | Connect conflict dashboard to `GET /api/v1/timetables/{id}/conflicts` | `src/dashboard/conflict_dashboard/` |

### Phase 3: Cleanup
| Step | What to Do |
|------|----------|
| 11 | Remove `pg`, `bcrypt` dependencies from frontend `src/package.json` (no longer needed) |
| 12 | Delete `src/legacy/app.js` (mock data, localStorage-based) |
| 13 | Fix typo: rename `student_dashbord/` → `student_dashboard/` |
| 14 | Clean up empty directories (`src/utils/`, `src/pages/admin/`) or populate them |
| 15 | Resolve module system: either convert `server.js` to ES modules or add a bundler for `api.js`/`facultyService.js` |
| 16 | Add `.env.example` to frontend repo documenting required variables |

### Environment Variable Changes After Integration

**Frontend `.env` (simplified — no more DB vars):**
```env
PORT=3000
VITE_API_BASE_URL=http://localhost:8000/api/v1   # Backend API URL
```

**Backend `.env` (unchanged)**
```env
BACKEND_CORS_ORIGINS=["http://localhost:3000"]    # Frontend origin
```

