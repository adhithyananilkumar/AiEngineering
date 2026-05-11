from __future__ import annotations

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

import mongo_schemas


def _to_object_id(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except Exception as exc:  # noqa: BLE001
        raise ValueError("Invalid MongoDB id") from exc


def _serialize_student(doc: dict) -> mongo_schemas.MongoStudentOut:
    return mongo_schemas.MongoStudentOut(
        id=str(doc["_id"]),
        name=doc.get("name", ""),
        age=doc.get("age", 0),
    )


async def create_student(
    db: AsyncIOMotorDatabase, student_in: mongo_schemas.MongoStudentCreate
) -> mongo_schemas.MongoStudentOut:
    payload = {"name": student_in.name, "age": student_in.age}
    result = await db.students.insert_one(payload)
    doc = {**payload, "_id": result.inserted_id}
    return _serialize_student(doc)


async def get_student_by_id(
    db: AsyncIOMotorDatabase, student_id: str
) -> mongo_schemas.MongoStudentOut | None:
    oid = _to_object_id(student_id)
    doc = await db.students.find_one({"_id": oid})
    if doc is None:
        return None
    return _serialize_student(doc)


async def get_students(
    db: AsyncIOMotorDatabase, skip: int = 0, limit: int = 10
) -> list[mongo_schemas.MongoStudentOut]:
    cursor = db.students.find({}).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [_serialize_student(doc) for doc in docs]


async def update_student(
    db: AsyncIOMotorDatabase,
    student_id: str,
    student_in: mongo_schemas.MongoStudentUpdate,
) -> mongo_schemas.MongoStudentOut | None:
    oid = _to_object_id(student_id)

    try:
        update_data = student_in.model_dump(exclude_unset=True)
    except AttributeError:  # pragma: no cover
        update_data = student_in.dict(exclude_unset=True)

    if not update_data:
        doc = await db.students.find_one({"_id": oid})
        if doc is None:
            return None
        return _serialize_student(doc)

    await db.students.update_one({"_id": oid}, {"$set": update_data})
    doc = await db.students.find_one({"_id": oid})
    if doc is None:
        return None
    return _serialize_student(doc)


async def delete_student(db: AsyncIOMotorDatabase, student_id: str) -> bool:
    oid = _to_object_id(student_id)
    result = await db.students.delete_one({"_id": oid})
    return result.deleted_count > 0
