"""
SQLAlchemy database models.

This module defines all database models used by the Task Manager Pro application.
Models are defined using SQLAlchemy's declarative base pattern.

Models:
    - Todo: Represents a task/todo item
    - SchemaMigration: Tracks applied database migrations

Version: 2.1.0
Author: Backend Team
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import validates

# ===========================================
# BASE CONFIGURATION
# ===========================================

Base = declarative_base()

# ===========================================
# CONSTANTS
# ===========================================

# Maximum lengths for string fields
MAX_TITLE_LENGTH = 255
MAX_DESCRIPTION_LENGTH = 2000

# Priority levels
PRIORITY_LOW = 0
PRIORITY_MEDIUM = 1
PRIORITY_HIGH = 2
PRIORITY_URGENT = 3

# ===========================================
# TODO MODEL
# ===========================================

class Todo(Base):
    """
    Todo model representing a task item.
    
    Attributes:
        id: Unique identifier (auto-generated)
        title: The title/name of the todo (required)
        description: Optional detailed description
        completed: Whether the todo is completed (default: False)
        created_at: Timestamp when the todo was created
        priority: Priority level (0=low, 1=medium, 2=high, 3=urgent)
    """
    
    __tablename__ = "todos"
    
    # Table configuration
    __table_args__ = (
        Index('idx_todos_completed', 'completed'),
        Index('idx_todos_priority', 'priority'),
        Index('idx_todos_created_at', 'created_at'),
        {'extend_existing': True}
    )

    # Primary key
    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        nullable=False
    )
    
    # Title field (required)
    title = Column(
        String(MAX_TITLE_LENGTH),
        nullable=False,
        index=False
    )
    
    # Description field (optional)
    description = Column(
        String(MAX_DESCRIPTION_LENGTH),
        nullable=True,
        default=None
    )
    
    # Completion status
    completed = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )
    
    # Creation timestamp
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    # Priority level
    priority = Column(
        Integer,
        default=PRIORITY_LOW,
        nullable=False,
        index=True
    )

    @validates('title')
    def validate_title(self, key, title):
        """Validate that title is not empty."""
        if not title or not title.strip():
            raise ValueError("Title cannot be empty")
        return title.strip()

    @validates('priority')
    def validate_priority(self, key, priority):
        """Validate that priority is within valid range."""
        if priority < PRIORITY_LOW or priority > PRIORITY_URGENT:
            raise ValueError(f"Priority must be between {PRIORITY_LOW} and {PRIORITY_URGENT}")
        return priority

    def __repr__(self):
        """Return string representation of Todo."""
        return (
            f"<Todo("
            f"id={self.id}, "
            f"title='{self.title[:20]}...', "
            f"completed={self.completed}, "
            f"priority={self.priority}"
            f")>"
        )
    
    def __str__(self):
        """Return human-readable string of Todo."""
        status = "Done" if self.completed else "Pending"
        return f"[{status}] {self.title}"
    
    def to_dict(self):
        """Convert Todo to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'completed': self.completed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'priority': self.priority
        }


# ===========================================
# SCHEMA MIGRATION MODEL
# ===========================================

class SchemaMigration(Base):
    """
    Schema migrations tracking model.
    
    Keeps track of which database migrations have been applied
    to prevent re-running migrations.
    
    Attributes:
        version: The migration version identifier (primary key)
        applied_at: Timestamp when the migration was applied
    """
    
    __tablename__ = "schema_migrations"
    
    __table_args__ = (
        {'extend_existing': True}
    )

    # Migration version (primary key)
    version = Column(
        String(255),
        primary_key=True,
        nullable=False
    )
    
    # Application timestamp
    applied_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self):
        """Return string representation of SchemaMigration."""
        return f"<SchemaMigration(version='{self.version}')>"
    
    def __str__(self):
        """Return human-readable string of SchemaMigration."""
        return f"Migration: {self.version}"


# ===========================================
# HELPER FUNCTIONS
# ===========================================

def get_priority_label(priority: int) -> str:
    """
    Get human-readable label for priority level.
    
    Args:
        priority: The priority level integer
        
    Returns:
        str: Human-readable priority label
    """
    labels = {
        PRIORITY_LOW: "Low",
        PRIORITY_MEDIUM: "Medium",
        PRIORITY_HIGH: "High",
        PRIORITY_URGENT: "Urgent"
    }
    return labels.get(priority, "Unknown")

