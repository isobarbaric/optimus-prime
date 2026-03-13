"""
Database utilities and migration management.

This module handles all database operations including:
- Connection pooling and session management
- Schema migrations
- CRUD operations for todos
"""
import os
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, text
from models import Base, Todo

# ===========================================
# DATABASE CONFIGURATION
# ===========================================

# Path to SQL migration files
MIGRATIONS_DIR = Path(__file__).parent / "migrations"

# Default connection pool settings
DEFAULT_POOL_SIZE = 5
DEFAULT_MAX_OVERFLOW = 10
DEFAULT_POOL_TIMEOUT = 30
DEFAULT_POOL_RECYCLE = 1800

# Database URL - defaults to SQLite for local development
# Infrastructure layer should override this with environment variable
# Supported databases: SQLite, PostgreSQL, MySQL
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./todos.db")

# Debug mode for SQL logging
SQL_ECHO_MODE = os.environ.get("SQL_ECHO", "false").lower() == "true"

# ===========================================
# ENGINE AND SESSION CONFIGURATION
# ===========================================

# Create async engine with connection pooling
engine = create_async_engine(
    DATABASE_URL,
    echo=SQL_ECHO_MODE,
    future=True,
    pool_pre_ping=True,
)

# Create session factory with optimized settings
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ===========================================
# SESSION MANAGEMENT
# ===========================================

async def get_db():
    """
    Get database session.
    
    Yields an async database session for use in request handlers.
    The session is automatically closed when the request completes.
    
    Yields:
        AsyncSession: An async SQLAlchemy session
    """
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()


# ===========================================
# DATABASE INITIALIZATION
# ===========================================

async def init_db():
    """
    Initialize database and run migrations.
    
    This function performs the following steps:
    1. Creates all tables defined in SQLAlchemy models
    2. Runs any pending SQL migrations from the migrations directory
    3. Records applied migrations in the schema_migrations table
    
    Should be called once during application startup.
    """
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


# ===========================================
# TODO CRUD OPERATIONS
# ===========================================

async def get_all_todos(session: AsyncSession):
    """
    Get all todos from database.
    
    Retrieves all todo items, ordered by creation date (newest first).
    
    Args:
        session: The async database session
        
    Returns:
        List[Todo]: A list of all todo items
    """
    query = select(Todo).order_by(Todo.created_at.desc())
    result = await session.execute(query)
    todos = result.scalars().all()
    return todos


async def get_todo_by_id(session: AsyncSession, todo_id: int):
    """
    Get a single todo by ID.
    
    Args:
        session: The async database session
        todo_id: The unique identifier of the todo
        
    Returns:
        Todo | None: The todo item if found, None otherwise
    """
    query = select(Todo).where(Todo.id == todo_id)
    result = await session.execute(query)
    todo = result.scalar_one_or_none()
    return todo


async def create_todo(
    session: AsyncSession,
    title: str,
    description: str = None,
    priority: int = 0
):
    """
    Create a new todo.
    
    Creates a new todo item with the provided details and saves it
    to the database.
    
    Args:
        session: The async database session
        title: The title of the todo (required)
        description: Optional description text
        priority: Priority level (default: 0)
        
    Returns:
        Todo: The newly created todo item
    """
    new_todo = Todo(
        title=title,
        description=description,
        completed=False,
        priority=priority
    )
    session.add(new_todo)
    await session.commit()
    await session.refresh(new_todo)
    return new_todo


async def update_todo(
    session: AsyncSession,
    todo_id: int,
    title: str = None,
    description: str = None,
    completed: bool = None,
    priority: int = None
):
    """
    Update an existing todo.
    
    Updates the specified fields of an existing todo item.
    Only provided fields will be updated; None values are ignored.
    
    Args:
        session: The async database session
        todo_id: The unique identifier of the todo to update
        title: New title (optional)
        description: New description (optional)
        completed: New completion status (optional)
        priority: New priority level (optional)
        
    Returns:
        Todo | None: The updated todo item, or None if not found
    """
    existing_todo = await get_todo_by_id(session, todo_id)
    
    if existing_todo is None:
        return None
    
    # Update fields if provided
    if title is not None:
        existing_todo.title = title
    if description is not None:
        existing_todo.description = description
    if completed is not None:
        existing_todo.completed = completed
    if priority is not None:
        existing_todo.priority = priority
    
    await session.commit()
    await session.refresh(existing_todo)
    return existing_todo


async def delete_todo(session: AsyncSession, todo_id: int):
    """
    Delete a todo.
    
    Permanently removes a todo item from the database.
    
    Args:
        session: The async database session
        todo_id: The unique identifier of the todo to delete
        
    Returns:
        bool: True if the todo was deleted, False if not found
    """
    existing_todo = await get_todo_by_id(session, todo_id)
    
    if existing_todo is None:
        return False
    
    await session.delete(existing_todo)
    await session.commit()
    return True


# ===========================================
# UTILITY FUNCTIONS
# ===========================================

async def health_check():
    """
    Perform a database health check.
    
    Returns:
        bool: True if database is accessible, False otherwise
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def get_todo_count(session: AsyncSession):
    """
    Get the total count of todos.
    
    Args:
        session: The async database session
        
    Returns:
        int: Total number of todos in the database
    """
    from sqlalchemy import func as sql_func
    query = select(sql_func.count(Todo.id))
    result = await session.execute(query)
    count = result.scalar()
    return count or 0
