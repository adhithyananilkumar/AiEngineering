"""schemas.py

Pydantic schemas (data validation & serialization) live here.

Beginner note:
- SQLAlchemy models are for DB/table structure.
- Pydantic schemas are for request/response data.

We keep them separate because it's cleaner and scales better.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class StudentBase(BaseModel):
    """Shared properties for a student."""

    name: str = Field(..., example="Akhil")
    age: int = Field(..., ge=1, le=150, example=20)


class StudentCreate(StudentBase):
    """Schema used when creating a student."""

    pass


class StudentUpdate(BaseModel):
    """Schema used when updating a student.

    All fields are optional so you can update only what you want.
    """

    name: Optional[str] = Field(None, example="Updated Name")
    age: Optional[int] = Field(None, ge=1, le=150, example=21)


class StudentOut(StudentBase):
    """Schema used when returning a student in responses."""

    id: int

    # This tells Pydantic v2 how to read data from ORM objects (SQLAlchemy models)
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    username: str = Field(..., example="alice")
    password: str = Field(..., min_length=6)


class UserOut(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str
