"""PostgreSQL repository implementation."""
from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, create_engine, select
from sqlmodel.ext.asyncio.session import AsyncEngine, AsyncSession

from app.models.user import User


class PostgresRepository:
    """PostgreSQL implementation of DatabaseRepository protocol."""

    def __init__(self, database_url: str):
        """Initialize PostgreSQL repository."""
        self.database_url = database_url
        self.engine: Optional[AsyncEngine] = None

    async def initialize(self) -> None:
        """Initialize database and create tables."""
        from sqlmodel import SQLModel
        from sqlalchemy.ext.asyncio import create_async_engine

        self.engine = create_async_engine(self.database_url, echo=False, future=True)

        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    async def create_user(self, username: str) -> User:
        """Create a new user."""
        if not self.engine:
            raise RuntimeError("Database not initialized")

        user = User(username=username, block_count=0, is_blocked=False)

        async with AsyncSession(self.engine) as session:
            try:
                session.add(user)
                await session.commit()
                await session.refresh(user)
                return user
            except IntegrityError:
                await session.rollback()
                raise ValueError(f"User already exists: {username}")

    async def get_user(self, username: str) -> Optional[User]:
        """Get user by username."""
        if not self.engine:
            raise RuntimeError("Database not initialized")

        async with AsyncSession(self.engine) as session:
            statement = select(User).where(User.username == username)
            result = await session.execute(statement)
            return result.scalar_one_or_none()

    async def get_all_users(self) -> List[User]:
        """Get all users."""
        if not self.engine:
            raise RuntimeError("Database not initialized")

        async with AsyncSession(self.engine) as session:
            statement = select(User)
            result = await session.execute(statement)
            return list(result.scalars().all())

    async def get_all_usernames(self) -> List[str]:
        """Get all usernames (optimized query - only username column)."""
        if not self.engine:
            raise RuntimeError("Database not initialized")

        async with AsyncSession(self.engine) as session:
            statement = select(User.username)
            result = await session.execute(statement)
            return list(result.scalars().all())

    async def update_user(self, user: User) -> User:
        """Update user."""
        if not self.engine:
            raise RuntimeError("Database not initialized")

        async with AsyncSession(self.engine) as session:
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    async def health_check(self) -> bool:
        """Check database connectivity."""
        if not self.engine:
            return False

        try:
            async with AsyncSession(self.engine) as session:
                await session.execute(select(1))
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()
