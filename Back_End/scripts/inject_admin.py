import asyncio
import sys
import os
from sqlalchemy import select

# Add parent directory to path to allow importing app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import AsyncSessionLocal
from app import models  # Trigger model registration
from app.models.user import User, UserRole
from app.core.security import get_password_hash

async def insert_admin():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.username == "admin@example.com"))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            # force reset the password just in case
            existing_user.hashed_password = get_password_hash("adminpassword")
            session.add(existing_user)
            await session.commit()
            print("Reset existing admin password.")
            return

        new_user = User(
            username="admin@example.com",
            email="admin@example.com",
            hashed_password=get_password_hash("adminpassword"),
            full_name="Admin User",
            role=UserRole.ADMIN.value,
            is_active=True,
            is_superuser=True
        )
        
        session.add(new_user)
        await session.commit()
        print("Created admin@example.com.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(insert_admin())
