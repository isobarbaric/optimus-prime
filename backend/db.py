"""
Database utilities and migration management.

Provides async database connectivity and CRUD operations.

This module implements the data access layer with support for:
- Async database connections via SQLAlchemy
- Connection pooling and session management
- Schema migrations with version tracking
- CRUD operations for todo entities

Architecture Notes:
- Uses async/await pattern for non-blocking I/O
- Implements repository pattern for data access
- Supports multiple database backends (SQLite, PostgreSQL)

Performance Considerations:
- Connection pool pre-ping enabled for stale connection detection
- Session-per-request pattern to prevent connection leaks
- Lazy loading disabled to prevent N+1 query issues
"""
import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, text
from models import Base, Todo

# Configure module logger
logger = logging.getLogger(__name__)

# Path to migration files
MIGRATIONS_DIR = Path(__file__).parent / "migrations"

# Database configuration constants
DEFAULT_POOL_SIZE = 5
DEFAULT_MAX_OVERFLOW = 10
DEFAULT_POOL_TIMEOUT = 30
DEFAULT_POOL_RECYCLE = 1800
DEFAULT_ECHO = False

# Database URL - defaults to SQLite for local development
# Infrastructure layer should override this with environment variable
# Supported formats:
#   - SQLite: sqlite+aiosqlite:///./todos.db
#   - PostgreSQL: postgresql+asyncpg://user:pass@host:port/db
#   - MySQL: mysql+aiomysql://user:pass@host:port/db
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./todos.db")

# Enable SQL echo for debugging (set via environment)
SQL_ECHO = os.environ.get("SQL_ECHO", "false").lower() == "true"

# =============================================================================
# DATABASE ENGINE CONFIGURATION
# =============================================================================

# Create async engine with optimized settings
# The engine manages the connection pool and handles database connectivity
engine = create_async_engine(
    DATABASE_URL,
    echo=SQL_ECHO,
    future=True,
    pool_pre_ping=True,
)

# Log engine configuration
logger.info(f"Database engine created with URL pattern: {DATABASE_URL.split('@')[0] if '@' in DATABASE_URL else DATABASE_URL[:30]}...")

# =============================================================================
# SESSION FACTORY CONFIGURATION
# =============================================================================

# Create session factory for generating database sessions
# Each request should get its own session instance
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# =============================================================================
# SESSION MANAGEMENT
# =============================================================================

async def get_db():
    """
    Get database session dependency.
    
    This is a FastAPI dependency that provides a database session
    for each request. The session is automatically closed when
    the request completes.
    
    Yields:
        AsyncSession: An async SQLAlchemy session for database operations
        
    Example:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            return await db.execute(select(Item))
    """
    session = AsyncSessionLocal()
    try:
        logger.debug("Database session created")
        yield session
    except Exception as e:
        logger.error(f"Database session error: {e}")
        await session.rollback()
        raise
    finally:
        logger.debug("Database session closed")
        await session.close()


# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================

async def init_db():
    """
    Initialize database schema and run pending migrations.
    
    This function performs the following operations:
    1. Creates all tables defined in SQLAlchemy models
    2. Scans the migrations directory for SQL files
    3. Applies any migrations not yet recorded in schema_migrations
    4. Records applied migrations to prevent re-execution
    
    Should be called once during application startup via the
    lifespan context manager.
    
    Raises:
        SQLAlchemyError: If database operations fail
        FileNotFoundError: If migration files cannot be read
    """
    logger.info("Initializing database...")
    async with engine.begin() as conn:
        # Create all tables from SQLAlchemy models
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created/verified")
        
        # Run SQL migrations for additional setup (indexes, etc.)
        migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        
        for migration_file in migration_files:
            version = migration_file.stem
            
            # Check if migration already applied
            result = await conn.execute(
                text("SELECT version FROM schema_migrations WHERE version = :version"),
                {"version": version}
            )
            row = result.fetchone()
            
            if row is None:
                print(f"Applying migration: {version}")
                
                # Read and execute migration
                with open(migration_file, 'r') as f:
                    migration_sql = f.read()
                
                # Execute each statement separately
                for statement in migration_sql.split(';'):
                    statement = statement.strip()
                    if statement and not statement.startswith('--'):
                        # Skip CREATE TABLE statements - already handled by models
                        if not statement.upper().startswith('CREATE TABLE'):
                            await conn.execute(text(statement))
                
                # Record migration as applied
                await conn.execute(
                    text("INSERT INTO schema_migrations (version) VALUES (:version)"),
                    {"version": version}
                )
                
                print(f"✓ Migration {version} applied successfully")
            else:
                print(f"Migration {version} already applied, skipping")
        
        print("Database initialized successfully!")


# =============================================================================
# TODO CRUD OPERATIONS
# =============================================================================

async def get_all_todos(session: AsyncSession) -> List[Todo]:
    """
    Retrieve all todos from the database.
    
    Returns todos ordered by creation date (newest first).
    
    Args:
        session: The async database session
        
    Returns:
        List[Todo]: A list of all todo items, ordered by created_at desc
        
    Example:
        async with AsyncSessionLocal() as session:
            todos = await get_all_todos(session)
            for todo in todos:
                print(todo.title)
    """
    logger.debug("Fetching all todos from database")
    query = select(Todo).order_by(Todo.created_at.desc())
    result = await session.execute(query)
    todos = result.scalars().all()
    logger.debug(f"Retrieved {len(todos)} todos")
    return todos


async def get_todo_by_id(session: AsyncSession, todo_id: int) -> Optional[Todo]:
    """
    Retrieve a single todo by its unique identifier.
    
    Args:
        session: The async database session
        todo_id: The unique identifier of the todo to retrieve
        
    Returns:
        Optional[Todo]: The todo if found, None otherwise
        
    Example:
        todo = await get_todo_by_id(session, 123)
        if todo:
            print(f"Found: {todo.title}")
        else:
            print("Todo not found")
    """
    logger.debug(f"Fetching todo with id={todo_id}")
    query = select(Todo).where(Todo.id == todo_id)
    result = await session.execute(query)
    todo = result.scalar_one_or_none()
    if todo:
        logger.debug(f"Found todo: {todo.title}")
    else:
        logger.debug(f"Todo with id={todo_id} not found")
    return todo


async def create_todo(
    session: AsyncSession,
    title: str,
    description: Optional[str] = None,
    priority: int = 0
) -> Todo:
    """
    Create a new todo item in the database.
    
    Args:
        session: The async database session
        title: The title of the todo (required, non-empty)
        description: Optional detailed description
        priority: Priority level (0=low, 1=medium, 2=high, 3=urgent)
        
    Returns:
        Todo: The newly created todo with generated id and timestamp
        
    Raises:
        IntegrityError: If title is empty or violates constraints
        
    Example:
        new_todo = await create_todo(
            session,
            title="Buy groceries",
            description="Milk, eggs, bread",
            priority=1
        )
        print(f"Created todo #{new_todo.id}")
    """
    logger.info(f"Creating new todo: {title}")
    
    # Create the todo instance
    todo = Todo(
        title=title,
        description=description,
        completed=False,
        priority=priority
    )
    
    # Add to session and commit
    session.add(todo)
    await session.commit()
    await session.refresh(todo)
    
    logger.info(f"Created todo with id={todo.id}")
    return todo


async def update_todo(
    session: AsyncSession,
    todo_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    completed: Optional[bool] = None,
    priority: Optional[int] = None
) -> Optional[Todo]:
    """
    Update an existing todo with new values.
    
    Only provided (non-None) fields will be updated. This allows
    partial updates without affecting other fields.
    
    Args:
        session: The async database session
        todo_id: The unique identifier of the todo to update
        title: New title (optional)
        description: New description (optional)
        completed: New completion status (optional)
        priority: New priority level (optional)
        
    Returns:
        Optional[Todo]: The updated todo if found, None otherwise
        
    Example:
        # Mark todo as completed
        updated = await update_todo(session, 123, completed=True)
        
        # Update title and priority
        updated = await update_todo(
            session, 123,
            title="New title",
            priority=2
        )
    """
    logger.info(f"Updating todo with id={todo_id}")
    
    # Fetch the existing todo
    todo = await get_todo_by_id(session, todo_id)
    
    if todo is None:
        logger.warning(f"Todo with id={todo_id} not found for update")
        return None
    
    # Track what fields are being updated
    updates = []
    
    # Update fields if provided
    if title is not None:
        todo.title = title
        updates.append("title")
    if description is not None:
        todo.description = description
        updates.append("description")
    if completed is not None:
        todo.completed = completed
        updates.append("completed")
    if priority is not None:
        todo.priority = priority
        updates.append("priority")
    
    # Commit changes
    await session.commit()
    await session.refresh(todo)
    
    logger.info(f"Updated todo {todo_id}, fields: {', '.join(updates)}")
    return todo


async def delete_todo(session: AsyncSession, todo_id: int) -> bool:
    """
    Delete a todo from the database.
    
    Permanently removes the todo. This operation cannot be undone.
    
    Args:
        session: The async database session
        todo_id: The unique identifier of the todo to delete
        
    Returns:
        bool: True if the todo was deleted, False if not found
        
    Example:
        if await delete_todo(session, 123):
            print("Todo deleted successfully")
        else:
            print("Todo not found")
    """
    logger.info(f"Deleting todo with id={todo_id}")
    
    # Fetch the todo first
    todo = await get_todo_by_id(session, todo_id)
    
    if todo is None:
        logger.warning(f"Todo with id={todo_id} not found for deletion")
        return False
    
    # Delete and commit
    await session.delete(todo)
    await session.commit()
    
    logger.info(f"Deleted todo with id={todo_id}")
    return True


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

async def get_todo_count(session: AsyncSession) -> int:
    """
    Get the total count of todos in the database.
    
    Args:
        session: The async database session
        
    Returns:
        int: Total number of todos
    """
    from sqlalchemy import func
    query = select(func.count(Todo.id))
    result = await session.execute(query)
    return result.scalar() or 0


async def get_completed_todos(session: AsyncSession) -> List[Todo]:
    """
    Get all completed todos.
    
    Args:
        session: The async database session
        
    Returns:
        List[Todo]: List of completed todos
    """
    query = select(Todo).where(Todo.completed == True).order_by(Todo.created_at.desc())
    result = await session.execute(query)
    return result.scalars().all()


async def get_pending_todos(session: AsyncSession) -> List[Todo]:
    """
    Get all pending (incomplete) todos.
    
    Args:
        session: The async database session
        
    Returns:
        List[Todo]: List of pending todos
    """
    query = select(Todo).where(Todo.completed == False).order_by(Todo.created_at.desc())
    result = await session.execute(query)
    return result.scalars().all()


async def health_check() -> Dict[str, Any]:
    """
    Perform a database health check.
    
    Returns:
        Dict with health status and metadata
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "engine": str(engine.url).split("@")[0] if "@" in str(engine.url) else "sqlite"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }
