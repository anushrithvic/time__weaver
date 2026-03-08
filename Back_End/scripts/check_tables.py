"""Check which database tables exist vs what models expect."""
import asyncio
from sqlalchemy import text
from app.db.session import engine


EXPECTED_TABLES = [
    "users", "audit_logs",
    "semesters", "departments", "sections",
    "courses", "elective_groups",
    "rooms", "time_slots", "constraints",
    "curriculum", "course_elective_assignments", "course_batching_config",
    "timetables", "timetable_slots", "conflicts",
    "institutional_rules",
    "faculty", "faculty_preferences", "faculty_courses",
    "faculty_leaves",
    "students",
]


async def check():
    async with engine.connect() as conn:
        result = await conn.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' ORDER BY table_name;"
        ))
        db_tables = {row[0] for row in result}

    print(f"Found {len(db_tables)} tables in database:\n")
    for t in sorted(db_tables):
        print(f"  + {t}")

    missing = [t for t in EXPECTED_TABLES if t not in db_tables]
    extra = [t for t in sorted(db_tables) if t not in EXPECTED_TABLES]

    if missing:
        print(f"\n--- MISSING ({len(missing)}) ---")
        for t in missing:
            print(f"  x {t}")
    else:
        print("\n--- All expected tables exist! ---")

    if extra:
        print(f"\n--- EXTRA (in DB but not in expected list) ---")
        for t in extra:
            print(f"  ? {t}")


asyncio.run(check())
