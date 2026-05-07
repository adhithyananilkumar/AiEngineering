"""models.py

SQLAlchemy ORM models live here.

Beginner note:
An ORM model is a Python class that represents a database table.
Each attribute on the class is a column in the table.
"""

from sqlalchemy import Column, Integer, String

from database import Base


class Student(Base):
    """Represents the `students` table."""

    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
