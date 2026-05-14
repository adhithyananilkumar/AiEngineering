from sqlalchemy.orm import Session

import models
import schemas
import auth


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


def get_user_by_username(db: Session, username: str) -> models.User | None:
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, user_in: schemas.UserCreate) -> models.User:
    hashed = auth.get_password_hash(user_in.password)
    user = models.User(username=user_in.username, hashed_password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> models.User | None:
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not auth.verify_password(password, user.hashed_password):
        return None
    return user
