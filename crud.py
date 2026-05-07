"""crud.py

This file contains the CRUD logic (Create, Read, Update, Delete).

Beginner note:
Keeping CRUD logic separate from routes keeps `main.py` clean and scalable.
"""

from sqlalchemy.orm import Session

import models
import schemas


def create_student(db: Session, student_in: schemas.StudentCreate) -> models.Student:
    """Create a new student row in the database."""

    student = models.Student(name=student_in.name, age=student_in.age)
    db.add(student)

    # commit() writes the change to the database.
    db.commit()

    # refresh() loads generated fields (like `id`) from the DB into the object.
    db.refresh(student)

    return student


def get_student_by_id(db: Session, student_id: int) -> models.Student | None:
    """Fetch a single student by id."""

    return db.query(models.Student).filter(models.Student.id == student_id).first()


def get_students(db: Session, skip: int = 0, limit: int = 10) -> list[models.Student]:
    """Fetch students with pagination support."""

    return db.query(models.Student).offset(skip).limit(limit).all()


def update_student(
    db: Session, student_id: int, student_in: schemas.StudentUpdate
) -> models.Student | None:
    """Update an existing student."""

    student = get_student_by_id(db, student_id)
    if student is None:
        return None

    # Pydantic v2 uses `model_dump()`. (We keep a small fallback for older versions.)
    try:
        update_data = student_in.model_dump(exclude_unset=True)
    except AttributeError:  # pragma: no cover
        update_data = student_in.dict(exclude_unset=True)

    # Update only the provided fields.
    for field_name, value in update_data.items():
        setattr(student, field_name, value)

    db.commit()
    db.refresh(student)

    return student


def delete_student(db: Session, student_id: int) -> bool:
    """Delete a student. Returns True if deleted, False if not found."""

    student = get_student_by_id(db, student_id)
    if student is None:
        return False

    db.delete(student)
    db.commit()

    return True
