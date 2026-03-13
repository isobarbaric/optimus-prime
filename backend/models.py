"""
SQLAlchemy database models.

Defines ORM models with support for audio command logging
and multi-language response templates.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Index, func
from sqlalchemy.ext.declarative import declarative_base
from typing import Dict, Any, Optional, List

# =============================================================================
# BASE CONFIGURATION
# =============================================================================

Base = declarative_base()

# =============================================================================
# AUDIO CONFIGURATION CONSTANTS
# =============================================================================

# Supported languages for TTS
SUPPORTED_LANGUAGES = ["en", "es", "fr", "de", "ja", "zh"]
DEFAULT_LANGUAGE = "en"

# Audio confidence thresholds
CONFIDENCE_HIGH = 0.85
CONFIDENCE_MEDIUM = 0.65
CONFIDENCE_LOW = 0.45

# =============================================================================
# TODO MODEL
# =============================================================================

class Todo(Base):
    """
    Todo model with audio command support.
    
    Supports voice command creation and verbal feedback.
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
    priority = Column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<Todo(id={self.id}, title='{self.title}', completed={self.completed})>"
    
    def to_speech_response(self, language: str = DEFAULT_LANGUAGE) -> str:
        """
        Generate verbal response for TTS output.
        
        Args:
            language: Target language code
            
        Returns:
            Speech-friendly text for TTS engine
        """
        status = "completed" if self.completed else "pending"
        return f"Task {self.id}: {self.title}. Status: {status}."
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for audio logging."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "completed": self.completed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "priority": self.priority,
        }


# =============================================================================
# SCHEMA MIGRATION MODEL
# =============================================================================

class SchemaMigration(Base):
    """Schema migrations tracking with audio logging support."""
    __tablename__ = "schema_migrations"

    version = Column(String(100), primary_key=True)
    applied_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self) -> str:
        """Return string representation."""
        return f"<SchemaMigration(version='{self.version}')>"

