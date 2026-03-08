
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

# Dedicated engine for concurrency tests (no statement cache to avoid sharing state issues)
# We use the same URL but ensure it's async
database_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

async_engine = create_async_engine(
    database_url,
    echo=False,
    pool_size=10,  # Ensure pool can handle concurrent connections
    max_overflow=20
)

# A session maker that yields NEW sessions each time, unrelated to the test fixture's transaction
concurrent_session_factory = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

async def get_test_session():
    """Yields a fresh session for use in concurrency tests."""
    async with concurrent_session_factory() as session:
        yield session
