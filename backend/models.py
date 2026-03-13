"""
SQLAlchemy database models.

Defines ORM models for the application data layer.

This module contains all database model definitions using SQLAlchemy's
declarative base pattern. Models define the structure of database tables
and provide methods for data manipulation.

Models:
    - Todo: Represents a task/todo item with title, description, status
    - SchemaMigration: Tracks applied database migrations

Usage:
    from models import Base, Todo
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create a todo
    todo = Todo(title="My task", priority=1)
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Index, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import validates
from typing import Dict, Any, Optional
from datetime import datetime

# =============================================================================
# BASE CONFIGURATION
# =============================================================================

Base = declarative_base()

# =============================================================================
# CONSTANTS
# =============================================================================

# Priority level constants
PRIORITY_LOW = 0
PRIORITY_MEDIUM = 1
PRIORITY_HIGH = 2
PRIORITY_URGENT = 3

# Priority labels for display
PRIORITY_LABELS = {
    PRIORITY_LOW: "Low",
    PRIORITY_MEDIUM: "Medium",
    PRIORITY_HIGH: "High",
    PRIORITY_URGENT: "Urgent",
}

# Field length constraints
MAX_TITLE_LENGTH = 255
MAX_DESCRIPTION_LENGTH = 2000
MAX_VERSION_LENGTH = 100

# Default values
DEFAULT_PRIORITY = PRIORITY_LOW
DEFAULT_COMPLETED = False


# =============================================================================
# TODO MODEL
# =============================================================================

class Todo(Base):
    """
    Todo model representing a task item.
    
    This model stores individual todo/task items with support for
    titles, descriptions, completion status, and priority levels.
    
    Attributes:
        id (int): Unique identifier, auto-generated primary key
        title (str): The title/name of the todo (required)
        description (str): Optional detailed description
        completed (bool): Whether the todo is completed (default: False)
        created_at (datetime): Timestamp when the todo was created
        priority (int): Priority level (0=low, 1=medium, 2=high, 3=urgent)
        
    Table Indexes:
        - Primary key index on id
        - Index on completed for filtering
        - Index on priority for sorting
        - Index on created_at for ordering
        
    Example:
        todo = Todo(
            title="Complete project",
            description="Finish the sensor fusion implementation",
            priority=PRIORITY_HIGH
        )
    """
    
    __tablename__ = "todos"
    
    # Define table-level indexes
    __table_args__ = (
        Index("idx_todos_completed", "completed"),
        Index("idx_todos_priority", "priority"),
        Index("idx_todos_created_at", "created_at"),
        {"extend_existing": True},
    )

    # Primary key
    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        nullable=False,
        comment="Unique identifier for the todo"
    )
    
    # Title field - required
    title = Column(
        String(MAX_TITLE_LENGTH),
        nullable=False,
        comment="Title of the todo item"
    )
    
    # Description field - optional
    description = Column(
        String(MAX_DESCRIPTION_LENGTH),
        nullable=True,
        default=None,
        comment="Detailed description of the todo"
    )
    
    # Completion status
    completed = Column(
        Boolean,
        default=DEFAULT_COMPLETED,
        nullable=False,
        comment="Whether the todo has been completed"
    )
    
    # Creation timestamp
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the todo was created"
    )
    
    # Priority level
    priority = Column(
        Integer,
        default=DEFAULT_PRIORITY,
        nullable=False,
        comment="Priority level (0=low, 1=medium, 2=high, 3=urgent)"
    )

    # -------------------------------------------------------------------------
    # Validators
    # -------------------------------------------------------------------------
    
    @validates("title")
    def validate_title(self, key: str, title: str) -> str:
        """
        Validate the title field.
        
        Ensures title is not empty and within length limits.
        
        Args:
            key: The field name being validated
            title: The title value to validate
            
        Returns:
            str: The validated and stripped title
            
        Raises:
            ValueError: If title is empty or too long
        """
        if not title or not title.strip():
            raise ValueError("Title cannot be empty")
        title = title.strip()
        if len(title) > MAX_TITLE_LENGTH:
            raise ValueError(f"Title cannot exceed {MAX_TITLE_LENGTH} characters")
        return title
    
    @validates("priority")
    def validate_priority(self, key: str, priority: int) -> int:
        """
        Validate the priority field.
        
        Ensures priority is within valid range.
        
        Args:
            key: The field name being validated
            priority: The priority value to validate
            
        Returns:
            int: The validated priority
            
        Raises:
            ValueError: If priority is out of range
        """
        if priority < PRIORITY_LOW or priority > PRIORITY_URGENT:
            raise ValueError(
                f"Priority must be between {PRIORITY_LOW} and {PRIORITY_URGENT}"
            )
        return priority

    # -------------------------------------------------------------------------
    # Instance Methods
    # -------------------------------------------------------------------------

    def __repr__(self) -> str:
        """
        Return string representation of Todo.
        
        Returns:
            str: Debug-friendly string representation
        """
        return (
            f"<Todo("
            f"id={self.id}, "
            f"title='{self.title[:30]}{'...' if len(self.title) > 30 else ''}', "
            f"completed={self.completed}, "
            f"priority={self.priority}"
            f")>"
        )
    
    def __str__(self) -> str:
        """
        Return human-readable string of Todo.
        
        Returns:
            str: User-friendly string representation
        """
        status = "✓" if self.completed else "○"
        priority_label = PRIORITY_LABELS.get(self.priority, "Unknown")
        return f"[{status}] {self.title} ({priority_label})"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Todo to dictionary representation.
        
        Returns:
            Dict[str, Any]: Dictionary with all todo fields
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "completed": self.completed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "priority": self.priority,
            "priority_label": self.priority_label,
        }
    
    @property
    def priority_label(self) -> str:
        """
        Get human-readable priority label.
        
        Returns:
            str: Priority label (Low, Medium, High, Urgent)
        """
        return PRIORITY_LABELS.get(self.priority, "Unknown")
    
    @property
    def is_high_priority(self) -> bool:
        """
        Check if todo is high priority or urgent.
        
        Returns:
            bool: True if priority >= HIGH
        """
        return self.priority >= PRIORITY_HIGH
    
    def mark_completed(self) -> None:
        """Mark the todo as completed."""
        self.completed = True
    
    def mark_pending(self) -> None:
        """Mark the todo as pending (not completed)."""
        self.completed = False
    
    def toggle_completed(self) -> bool:
        """
        Toggle the completion status.
        
        Returns:
            bool: The new completion status
        """
        self.completed = not self.completed
        return self.completed


# =============================================================================
# SCHEMA MIGRATION MODEL
# =============================================================================

class SchemaMigration(Base):
    """
    Schema migrations tracking model.
    
    Keeps track of which database migrations have been applied
    to prevent re-running migrations on subsequent startups.
    
    Attributes:
        version (str): The migration version identifier (primary key)
        applied_at (datetime): Timestamp when the migration was applied
        
    Example:
        migration = SchemaMigration(version="001_initial_schema")
    """
    
    __tablename__ = "schema_migrations"
    
    __table_args__ = (
        {"extend_existing": True},
    )

    # Migration version - primary key
    version = Column(
        String(MAX_VERSION_LENGTH),
        primary_key=True,
        nullable=False,
        comment="Migration version identifier"
    )
    
    # Application timestamp
    applied_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when migration was applied"
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<SchemaMigration(version='{self.version}')>"
    
    def __str__(self) -> str:
        """Return human-readable string."""
        return f"Migration: {self.version}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
        }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_priority_label(priority: int) -> str:
    """
    Get human-readable label for priority level.
    
    Args:
        priority: The priority level integer
        
    Returns:
        str: Human-readable priority label
    """
    return PRIORITY_LABELS.get(priority, "Unknown")


def get_priority_from_label(label: str) -> Optional[int]:
    """
    Get priority integer from label string.
    
    Args:
        label: The priority label (case-insensitive)
        
    Returns:
        Optional[int]: Priority integer or None if not found
    """
    label_lower = label.lower()
    for priority, priority_label in PRIORITY_LABELS.items():
        if priority_label.lower() == label_lower:
            return priority
    return None

