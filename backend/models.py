"""
SQLAlchemy database models.

This module defines all database models for the application.
Models support JSON serialization for CloudWatch log aggregation.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Index, func
from sqlalchemy.ext.declarative import declarative_base
from typing import Dict, Any, Optional

# =============================================================================
# BASE CONFIGURATION
# =============================================================================

Base = declarative_base()

# =============================================================================
# CONSTANTS
# =============================================================================

# Priority levels
PRIORITY_LOW = 0
PRIORITY_MEDIUM = 1
PRIORITY_HIGH = 2
PRIORITY_URGENT = 3

PRIORITY_LABELS = {
    PRIORITY_LOW: "Low",
    PRIORITY_MEDIUM: "Medium", 
    PRIORITY_HIGH: "High",
    PRIORITY_URGENT: "Urgent",
}

# =============================================================================
# TODO MODEL
# =============================================================================

class Todo(Base):
    """
    Todo model representing a task item.
    
    Supports JSON serialization for structured logging
    and CloudWatch log aggregation.
    """
    __tablename__ = "todos"
    
    __table_args__ = (
        Index("idx_todos_completed", "completed"),
        Index("idx_todos_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(String(2000), nullable=True)
    completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    priority = Column(Integer, default=PRIORITY_LOW, nullable=False)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<Todo(id={self.id}, title='{self.title}', completed={self.completed})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for JSON logging.
        
        Used for CloudWatch structured log aggregation.
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "completed": self.completed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "priority": self.priority,
            "priority_label": PRIORITY_LABELS.get(self.priority, "Unknown"),
        }
    
    def to_log_context(self) -> Dict[str, Any]:
        """
        Return minimal context for log entries.
        
        Used for request tracing and correlation.
        """
        return {
            "todo_id": self.id,
            "completed": self.completed,
            "priority": self.priority,
        }


# =============================================================================
# SCHEMA MIGRATION MODEL
# =============================================================================

class SchemaMigration(Base):
    """
    Schema migrations tracking.
    
    Records applied migrations for idempotent deployments.
    """
    __tablename__ = "schema_migrations"

    version = Column(String(100), primary_key=True)
    applied_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self) -> str:
        """Return string representation."""
        return f"<SchemaMigration(version='{self.version}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
        }

