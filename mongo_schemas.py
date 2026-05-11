"""MongoDB-specific Pydantic schemas.

MongoDB uses ObjectId for primary keys, so our API exposes them as strings.
"""

from typing import Optional

from pydantic import BaseModel, Field


class MongoStudentBase(BaseModel):
    name: str = Field(..., example="Akhil")
    age: int = Field(..., ge=1, le=150, example=20)


class MongoStudentCreate(MongoStudentBase):
    pass


class MongoStudentUpdate(BaseModel):
    name: Optional[str] = Field(None, example="Updated Name")
    age: Optional[int] = Field(None, ge=1, le=150, example=21)


class MongoStudentOut(MongoStudentBase):
    id: str = Field(..., description="MongoDB ObjectId as a string")
