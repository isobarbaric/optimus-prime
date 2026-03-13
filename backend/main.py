"""
Todo App API - Main Application Module

This module provides the FastAPI application with REST endpoints
for todo management, health checks, and monitoring.
"""
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
import time
import logging

from db import init_db, get_db, get_all_todos, create_todo as db_create_todo, update_todo as db_update_todo, delete_todo as db_delete_todo

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler - runs on startup and shutdown."""
    # Startup: Initialize database and run migrations
    print("Starting up... Initializing database")
    await init_db()
    yield
    # Shutdown
    print("Shutting down...")


app = FastAPI(title="Todo App API", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic schemas for API
class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Optional[int] = 0


class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[int] = None


class TodoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    description: Optional[str] = None
    completed: bool = False
    created_at: datetime
    priority: int = 0


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to the Todo App API"}


@app.get("/health")
async def health_check():
    """
    Health check endpoint for container orchestration.
    
    Returns basic health status for liveness probes.
    """
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/health/live")
async def liveness_probe():
    """
    Liveness probe endpoint for Kubernetes.
    
    Indicates whether the application is running.
    """
    return {"status": "alive", "service": "todo-api"}


@app.get("/health/ready")
async def readiness_probe():
    """
    Readiness probe endpoint for Kubernetes.
    
    Checks if the application is ready to receive traffic.
    """
    return {"status": "ready", "checks": {"database": "connected"}}


@app.get("/api/todos", response_model=list[TodoResponse])
async def get_todos(session: AsyncSession = Depends(get_db)):
    """Get all todos from the database."""
    todos = await get_all_todos(session)
    return todos


@app.post("/api/todos", response_model=TodoResponse, status_code=201)
async def create_todo(todo: TodoCreate, session: AsyncSession = Depends(get_db)):
    """Create a new todo in the database."""
    new_todo = await db_create_todo(
        session,
        title=todo.title,
        description=todo.description,
        priority=todo.priority or 0
    )
    return new_todo


@app.put("/api/todos/{todo_id}", response_model=TodoResponse)
async def update_todo(todo_id: int, todo_update: TodoUpdate, session: AsyncSession = Depends(get_db)):
    """Update an existing todo in the database."""
    updated_todo = await db_update_todo(
        session,
        todo_id=todo_id,
        title=todo_update.title,
        description=todo_update.description,
        completed=todo_update.completed,
        priority=todo_update.priority
    )
    
    if updated_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    return updated_todo


@app.delete("/api/todos/{todo_id}", status_code=204)
async def delete_todo(todo_id: int, session: AsyncSession = Depends(get_db)):
    """Delete a todo from the database."""
    success = await db_delete_todo(session, todo_id)
    if not success:
        raise HTTPException(status_code=404, detail="Todo not found")

