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

async def create_superuser():
    username = input("Enter superuser username: ")
    email = input("Enter superuser email: ")
    password = input("Enter superuser password: ")
    full_name = input("Enter full name: ")

    async with AsyncSessionLocal() as session:
        # Check if user already exists
        result = await session.execute(select(User).where(User.username == username))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"User {username} already exists!")
            return

        # Create new superuser
        new_user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            role=UserRole.ADMIN.value,  # Ensure using value for String column
            is_active=True,
            is_superuser=True
        )
        
        session.add(new_user)
        await session.commit()
        print(f"Superuser {username} created successfully!")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(create_superuser())
