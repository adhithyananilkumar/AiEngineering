# Student Management API (FastAPI + MySQL)

A beginner-level CRUD application using:
- FastAPI
- MySQL
- SQLAlchemy ORM
- Pydantic
- PyMySQL

It manages a simple `students` table with:
- `id` (Primary Key)
- `name`
- `age`

## Project Structure

This repo uses a simple, scalable structure (separating routes, DB, models, schemas, and CRUD logic):

- `main.py`      → FastAPI routes
- `database.py`  → MySQL connection + session dependency
- `models.py`    → SQLAlchemy ORM model (`Student`)
- `schemas.py`   → Pydantic request/response schemas
- `crud.py`      → CRUD functions

## 1) Install Dependencies

If you want a quick install:

```bash
pip install fastapi uvicorn[standard] sqlalchemy pymysql
```

Or install from `requirements.txt`:

```bash
pip install -r requirements.txt
```

## 2) Create MySQL Database

Run this in MySQL:

```sql
CREATE DATABASE student_db;

-- Optional: create a dedicated user (recommended)
CREATE USER 'student_user'@'localhost' IDENTIFIED BY 'student_pass';
GRANT ALL PRIVILEGES ON student_db.* TO 'student_user'@'localhost';
FLUSH PRIVILEGES;
```

Beginner note:
- You do NOT have to manually create the `students` table.
- This project creates it automatically using SQLAlchemy (`create_all`).

## 3) Configure Database Connection

This project reads DB settings from environment variables. Example:

```bash
export DB_USER="student_user"
export DB_PASSWORD="student_pass"
export DB_HOST="127.0.0.1"
export DB_PORT="3306"
export DB_NAME="student_db"
```

Tip (optional):
- Copy `.env.example` to `.env` so you have your DB values saved in one place.
- This project still reads from environment variables, so you’ll either export them (as above) or set them in your shell profile.

If you don’t set them, defaults are used (see `database.py`).

## 4) Run the API

Start the server:

```bash
uvicorn main:app --reload
```

Open Swagger UI:
- http://127.0.0.1:8000/docs

## 5) API Endpoints (CRUD)

### Create Student

`POST /students`

Body:
```json
{
	"name": "Akhil",
	"age": 20
}
```

### Get All Students (Pagination)

`GET /students?skip=0&limit=10`

Beginner note:
- `skip` = how many rows to skip
- `limit` = how many rows to return

### Get Student By ID

`GET /students/1`

### Update Student

`PUT /students/1`

Body (you can send only what you want to update):
```json
{
	"name": "Akhil Updated",
	"age": 21
}
```

### Delete Student

`DELETE /students/1`

## 6) Postman Examples

This repo includes a ready Postman collection:
- `postman_fastapi_collection.json`

Steps:
1. Open Postman
2. Import the collection JSON
3. Make sure `baseUrl` is `http://127.0.0.1:8000`
4. Run requests in this order:
	 - Create Student
	 - List Students
	 - Get Student
	 - Update Student
	 - Delete Student

---

# Internship Journal (kept for reference)

Ai Engineering - Intership JOURNAL
Techgentsia, Infopark Cherthala
Mentor : Prithwin

DAY 1 - 27/04/26 Monday 9.05 AM to 6.56 PM
- Python Basics
- OOPS in Python
- Generators
- Decoraters
- Solid Principles
- Design Patterns

DAY 2
- API
- Post Man
- GET, POST, PUT
- REST API
- Fast API

DAY 3
- Fast API CRUD
- POSTMAN TESTING Implimentation

DAY 4
- FAST API- CRUD Implimentation

DAY 5
- FAST API x DB
- Database OPeratios.
- Pagination