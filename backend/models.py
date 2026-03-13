"""
SQLAlchemy database models.

Defines ORM models for the application data layer.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Default values
DEFAULT_PRIORITY = 0


class Todo(Base):
    """Todo model."""
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    priority = Column(Integer, default=0, nullable=False)

    def __repr__(self):
        """String representation of Todo."""
        return f"<Todo(id={self.id}, title='{self.title}', completed={self.completed})>"
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "completed": self.completed,
            "priority": self.priority
        }


class SchemaMigration(Base):
    """Schema migrations tracking."""
    __tablename__ = "schema_migrations"

    version = Column(String, primary_key=True)
    applied_at = Column(DateTime(timezone=True), server_default=func.now())

