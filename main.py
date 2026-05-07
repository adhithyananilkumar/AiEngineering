"""main.py

Beginner-level Student Management API (FastAPI + MySQL + SQLAlchemy + Pydantic).

This file contains the FastAPI app and the HTTP routes.
The database logic lives in:
- database.py (connection + session dependency)
- models.py   (SQLAlchemy ORM table)
- schemas.py  (Pydantic request/response models)
- crud.py     (database operations)
"""

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy.orm import Session

import crud
import models
import schemas
from database import engine, get_db


app = FastAPI(title="Student Management API", version="1.0.0")


@app.on_event("startup")
def on_startup():
    """Create tables on app startup.

    Beginner note:
    - This requires your MySQL server to be running.
    - Your DB credentials must be correct (see environment variables in `database.py`).

    For production apps, you'd usually manage tables with migrations (Alembic),
    but `create_all()` is the simplest way to start learning.
    """

    try:
        models.Base.metadata.create_all(bind=engine)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "Failed to connect to MySQL / create tables. "
            "Check DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME and ensure MySQL is running."
        ) from exc


@app.get("/")
def root():
    """Health check / welcome route."""

    return {"message": "Student Management API is running"}


@app.post("/students", response_model=schemas.StudentOut, status_code=status.HTTP_201_CREATED)
def create_student(student: schemas.StudentCreate, db: Session = Depends(get_db)):
    """Create a new student.

    - FastAPI takes the request body and validates it using `StudentCreate`.
    - `db` is provided by the `get_db` dependency (database session).
    """

    return crud.create_student(db, student)


@app.get("/students", response_model=list[schemas.StudentOut])
def get_all_students(
    skip: int = Query(0, ge=0, description="How many records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Max records to return"),
    db: Session = Depends(get_db),
):
    """Get all students with pagination.

    Example:
        GET /students?skip=0&limit=10
    """

    return crud.get_students(db, skip=skip, limit=limit)


@app.get("/students/{student_id}", response_model=schemas.StudentOut)
def get_student(student_id: int, db: Session = Depends(get_db)):
    """Get a single student by ID."""

    student = crud.get_student_by_id(db, student_id)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student


@app.put("/students/{student_id}", response_model=schemas.StudentOut)
def update_student(student_id: int, student: schemas.StudentUpdate, db: Session = Depends(get_db)):
    """Update a student by ID.

    You can send only the fields you want to update.
    """

    updated = crud.update_student(db, student_id, student)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return updated


@app.delete("/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    """Delete a student by ID."""

    deleted = crud.delete_student(db, student_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return {"message": "Student deleted successfully"}