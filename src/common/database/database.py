from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from src.common.config import settings  # Import the settings object

# SQLAlchemy async engine and session setup
engine = create_async_engine(
    settings.DATABASE_URL, 
    echo=settings.DEBUG, 
    future=True, 
    pool_pre_ping=True, 
    pool_recycle=1800,
)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def connect_to_db():
    """Connect to the database."""
    try:
        # Test connection by executing a simple query
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            print("Database connected successfully!")
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        raise

async def close_db_connection():
    """Close the database connection."""
    try:
        await engine.dispose()
        print("Database connection closed successfully!")
    except Exception as e:
        print(f"Error closing the database connection: {e}")
        raise

# Dependency for using a session in routes
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session for use in FastAPI routes."""
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise
        # finally:
        #     await session.close()