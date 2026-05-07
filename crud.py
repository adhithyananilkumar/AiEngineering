from sqlalchemy.orm import Session

import models
import schemas


def create_student(db: Session, student_in: schemas.StudentCreate) -> models.Student:

    student = models.Student(name=student_in.name, age=student_in.age)
    db.add(student)

    db.commit()

    db.refresh(student)

    return student


def get_student_by_id(db: Session, student_id: int) -> models.Student | None:

    return db.query(models.Student).filter(models.Student.id == student_id).first()


def get_students(db: Session, skip: int = 0, limit: int = 10) -> list[models.Student]:

    return db.query(models.Student).offset(skip).limit(limit).all()


def update_student(
    db: Session, student_id: int, student_in: schemas.StudentUpdate
) -> models.Student | None:

    student = get_student_by_id(db, student_id)
    if student is None:
        return None

    try:
        update_data = student_in.model_dump(exclude_unset=True)
    except AttributeError:  # pragma: no cover
        update_data = student_in.dict(exclude_unset=True)

    for field_name, value in update_data.items():
        setattr(student, field_name, value)

    db.commit()
    db.refresh(student)

    return student


def delete_student(db: Session, student_id: int) -> bool:

    student = get_student_by_id(db, student_id)
    if student is None:
        return False

    db.delete(student)
    db.commit()

    return True
