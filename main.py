

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy.orm import Session

import crud
import mongo_crud
import models
import mongo_schemas
import schemas
from database import engine, get_db
from mongo_database import close_mongo_client, get_mongo_db


app = FastAPI(title="Student Management API", version="1.0.0")


@app.on_event("startup")
def on_startup():
    try:
        models.Base.metadata.create_all(bind=engine)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "Failed to connect to SQL database / create tables. "
            "Set DB_DIALECT (mysql/postgresql) + DB_* env vars, or provide DATABASE_URL."
        ) from exc


@app.on_event("shutdown")
def on_shutdown():
    close_mongo_client()


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


# -----------------
# MongoDB CRUD APIs
# -----------------


@app.post(
    "/mongo/students",
    response_model=mongo_schemas.MongoStudentOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_mongo_student(
    student: mongo_schemas.MongoStudentCreate,
    db=Depends(get_mongo_db),
):
    return await mongo_crud.create_student(db, student)


@app.get("/mongo/students", response_model=list[mongo_schemas.MongoStudentOut])
async def get_all_mongo_students(
    skip: int = Query(0, ge=0, description="How many records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Max records to return"),
    db=Depends(get_mongo_db),
):
    return await mongo_crud.get_students(db, skip=skip, limit=limit)


@app.get("/mongo/students/{student_id}", response_model=mongo_schemas.MongoStudentOut)
async def get_mongo_student(student_id: str, db=Depends(get_mongo_db)):
    try:
        student = await mongo_crud.get_student_by_id(db, student_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid student id")

    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student


@app.put("/mongo/students/{student_id}", response_model=mongo_schemas.MongoStudentOut)
async def update_mongo_student(
    student_id: str,
    student: mongo_schemas.MongoStudentUpdate,
    db=Depends(get_mongo_db),
):
    try:
        updated = await mongo_crud.update_student(db, student_id, student)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid student id")

    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return updated


@app.delete("/mongo/students/{student_id}")
async def delete_mongo_student(student_id: str, db=Depends(get_mongo_db)):
    try:
        deleted = await mongo_crud.delete_student(db, student_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid student id")

    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return {"message": "Student deleted successfully"}