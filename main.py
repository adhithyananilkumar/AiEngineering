

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy.orm import Session

import crud
import models
import schemas
from database import engine, get_db


app = FastAPI(title="Student Management API", version="1.0.0")


@app.on_event("startup")
def on_startup():


    try:
        models.Base.metadata.create_all(bind=engine)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
        ) from exc


@app.get("/")
def root():

    return {"message": "API is running"}


@app.post("/students", response_model=schemas.StudentOut, status_code=status.HTTP_201_CREATED)
def create_student(student: schemas.StudentCreate, db: Session = Depends(get_db)):
   

    return crud.create_student(db, student)


@app.get("/students", response_model=list[schemas.StudentOut])
def get_all_students(
    skip: int = Query(0, ge=0, description="How many records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Max records to return"),
    db: Session = Depends(get_db),
):


    return crud.get_students(db, skip=skip, limit=limit)


@app.get("/students/{student_id}", response_model=schemas.StudentOut)
def get_student(student_id: int, db: Session = Depends(get_db)):

    student = crud.get_student_by_id(db, student_id)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student


@app.put("/students/{student_id}", response_model=schemas.StudentOut)
def update_student(student_id: int, student: schemas.StudentUpdate, db: Session = Depends(get_db)):
  

    updated = crud.update_student(db, student_id, student)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return updated


@app.delete("/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):

    deleted = crud.delete_student(db, student_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return {"message": "Student deleted successfully"}