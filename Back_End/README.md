# TimeWeaver Backend

AI-powered academic timetable generation system. Uses a Genetic Algorithm to auto-generate conflict-free class schedules while respecting faculty preferences, room capacities, and institutional constraints.

> ⚠️ **Frontend and backend are not yet integrated.** See [docs/PROJECT_STRATEGY.md](docs/PROJECT_STRATEGY.md) for the integration plan.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI (Python 3.12) |
| Database | PostgreSQL 16 + asyncpg |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Auth | JWT (HS256) + bcrypt |
| Testing | pytest + pytest-asyncio + httpx |

---

## Quick Start

```powershell
# 1. Create & activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up PostgreSQL database
psql -U postgres -c "CREATE DATABASE timeweaver_db;"

# 4. Configure environment
#    Copy .env.example to .env and set your DATABASE_URL password

# 5. Run migrations
alembic upgrade head

# 6. Start server
uvicorn app.main:app --reload
```

- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Project Structure

```
timeweaver_backend/
├── app/
│   ├── api/v1/endpoints/        # 17 endpoint modules (92 endpoints total)
│   │   ├── auth.py              # Login, register, logout, password reset
│   │   ├── users.py             # User CRUD + self-service
│   │   ├── semesters.py         # Semester management
│   │   ├── departments.py       # Department management
│   │   ├── courses.py           # Course management
│   │   ├── sections.py          # Section management
│   │   ├── rooms.py             # Room management
│   │   ├── time_slots.py        # Time slot configuration
│   │   ├── constraints.py       # Scheduling constraints
│   │   ├── curriculums.py       # Curriculum management
│   │   ├── faculty.py           # Faculty CRUD + workload
│   │   ├── faculty_preferences.py
│   │   ├── faculty_leaves.py    # Leave management + substitute recommendations
│   │   ├── timetables.py        # Generation, viewing, publishing
│   │   ├── institutional_rules.py
│   │   ├── slot_locks.py        # Lock/unlock timetable slots
│   │   └── audit_logs.py        # Admin audit trail
│   ├── models/                  # 15 SQLAlchemy models
│   ├── schemas/                 # Pydantic request/response schemas
│   ├── services/                # Business logic
│   │   ├── timetable_generator.py   # Genetic Algorithm engine
│   │   ├── workload_calculator.py
│   │   ├── preference_weighting.py
│   │   └── substitute_recommender.py
│   ├── middleware/              # Audit logging middleware
│   ├── core/                    # Config, security, auth
│   └── db/                      # Database session & base
├── tests/                       # 9 test files (~160 tests)
├── alembic/                     # Database migrations
├── docs/                        # Documentation
│   ├── DEVOPS_HANDOFF.md
│   ├── TESTING_STRATEGY_HANDOFF.md
│   ├── PROJECT_STRATEGY.md
│   ├── MODULE_SPECIFICATIONS.md
│   └── SETUP_GUIDE.md
└── requirements.txt
```

---

## API Overview (92 Endpoints)

| Module | Endpoints | Auth Required |
|--------|-----------|---------------|
| Auth | 5 (login, register, logout, forgot/reset password) | Partial |
| Users | 8 (CRUD + self-service) | Admin / Self |
| Semesters | 5 | Admin |
| Departments | 5 | Admin |
| Courses | 7 | Admin |
| Sections | 5 | Admin |
| Rooms | 5 | Admin |
| Time Slots | 5 | Admin |
| Constraints | 6 | Admin |
| Curriculums | 7 | Admin |
| Faculty | 8 (CRUD + workload) | Admin / Self |
| Faculty Preferences | 5 | Admin / Faculty |
| Faculty Leaves | 6 (+ substitute recommender) | Admin / Faculty |
| Timetables | 8 (generate, view, publish, compare) | Admin |
| Institutional Rules | 6 | Admin |
| Slot Locks | 3 | Admin |
| Audit Logs | 2 | Admin |

Full API docs available at http://localhost:8000/docs when the server is running.

---

## RBAC (Role-Based Access Control)

| Role | Access Level |
|------|-------------|
| **Admin** | Full access — all CRUD, generation, publishing, audit logs |
| **Faculty** | Own profile, preferences, workload, schedule, leave requests |
| **Student** | View timetable, own profile |

---

## Testing

```powershell
# Run all tests
pytest tests/ -v

# Run specific file
pytest tests/test_phase10_apis.py -v

# Run with coverage (install pytest-cov first)
pip install pytest-cov
pytest tests/ --cov=app --cov-report=html
```

**Prerequisite**: Create a `timeweaver_test` database:
```powershell
psql -U postgres -c "CREATE DATABASE timeweaver_test;"
```

---

## Database Migrations

```powershell
alembic revision --autogenerate -m "description"   # Create migration
alembic upgrade head                                # Apply all
alembic downgrade -1                                # Rollback one
alembic history                                     # View history
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [SETUP_GUIDE.md](docs/SETUP_GUIDE.md) | Full setup instructions for both repos |
| [MODULE_SPECIFICATIONS.md](docs/MODULE_SPECIFICATIONS.md) | Detailed module breakdown & ownership |
| [DEVOPS_HANDOFF.md](docs/DEVOPS_HANDOFF.md) | Infrastructure, deployment, integration plan |
| [TESTING_STRATEGY_HANDOFF.md](docs/TESTING_STRATEGY_HANDOFF.md) | Test inventory, gaps, recommended strategy |
| [PROJECT_STRATEGY.md](docs/PROJECT_STRATEGY.md) | Prioritized roadmap of all remaining work |

---

## Related Repository

| Repo | URL |
|------|-----|
| **Frontend** | [timeweaver_frontend](https://github.com/Pranathi-N-47/timeweaver_frontend) |
