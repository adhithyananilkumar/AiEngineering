# Student Management API (FastAPI + MySQL/PostgreSQL + MongoDB)

A beginner-level CRUD application using:
- FastAPI
- MySQL or PostgreSQL (SQLAlchemy ORM)
- MongoDB (Motor)
- SQLAlchemy ORM
- Pydantic
- PyMySQL (MySQL driver)
- psycopg2 (PostgreSQL driver)
- Motor (MongoDB async driver)

It manages a simple `students` table with:
- `id` (Primary Key)
- `name`
- `age`

## Project Structure

This repo uses a simple, scalable structure (separating routes, DB, models, schemas, and CRUD logic):

- `main.py`      → FastAPI routes
- `database.py`  → SQL (MySQL/PostgreSQL) connection + session dependency
- `mongo_database.py` → MongoDB client + DB dependency
- `models.py`    → SQLAlchemy ORM model (`Student`)
- `schemas.py`   → Pydantic request/response schemas
- `crud.py`      → CRUD functions
- `mongo_schemas.py` → MongoDB Pydantic schemas
- `mongo_crud.py` → MongoDB CRUD functions

## 1) Install Dependencies

If you want a quick install:

```bash
pip install fastapi uvicorn[standard] sqlalchemy pymysql psycopg2-binary motor
```

Or install from `requirements.txt`:

```bash
pip install -r requirements.txt
```

## 2) Create a Database

This project supports **three** backends:
- MySQL (SQL)
- PostgreSQL (SQL)
- MongoDB (NoSQL)

The SQL endpoints are under `/students`.
MongoDB endpoints are under `/mongo/students`.

### Option A — MySQL

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

### Option B — PostgreSQL

Create a database (and optionally a user):

```sql
CREATE DATABASE student_db;

-- Optional: create a dedicated user
CREATE USER student_user WITH PASSWORD 'student_pass';
GRANT ALL PRIVILEGES ON DATABASE student_db TO student_user;
```

### Option C — MongoDB

MongoDB creates databases and collections automatically on first write.
You mainly need a running MongoDB server and a connection URI.

#### Debian (recommended): Run MongoDB using Docker + Compose

On Debian 13, the simplest way to get MongoDB running reliably is Docker.

1) Install Docker + Compose (requires sudo password):

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo systemctl enable --now docker
```

2) Optional (so you can run docker without sudo):

```bash
sudo usermod -aG docker $USER
newgrp docker
```

3) Start MongoDB using the repo's Compose file:

```bash
docker compose up -d
```

4) Verify MongoDB is running:

```bash
docker ps
```

## 3) Configure Database Connection

### SQL (MySQL or PostgreSQL)

This project reads SQL DB settings from environment variables.

Pick a dialect:
- `DB_DIALECT=mysql` (default)
- `DB_DIALECT=postgresql`

Example (MySQL):

```bash
export DB_DIALECT="mysql"
export DB_USER="student_user"
export DB_PASSWORD="student_pass"
export DB_HOST="localhost"
export DB_PORT="3306"
export DB_NAME="student_db"
```

Example (PostgreSQL):

```bash
export DB_DIALECT="postgresql"
export DB_USER="student_user"
export DB_PASSWORD="student_pass"
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_NAME="student_db"
```

Alternative (works for both): set a full SQLAlchemy URL:

```bash
export DATABASE_URL="postgresql+psycopg2://student_user:student_pass@localhost:5432/student_db"
```

Important note (common beginner issue):
- In MySQL/MariaDB, `'user'@'localhost'` is different from `'user'@'127.0.0.1'`.
- Since you created `student_user@localhost`, keep `DB_HOST="localhost"`.

Tip (optional):
- Copy `.env.example` to `.env` so you have your DB values saved in one place.
- This project still reads from environment variables, so you’ll either export them (as above) or set them in your shell profile.

If you don’t set them, defaults are used (see `database.py`).

### MongoDB

MongoDB config uses:

```bash
export MONGO_URI="mongodb://127.0.0.1:27017"
export MONGO_DB_NAME="student_db"
```

If you already verified MongoDB with `mongosh` (e.g. it connects to `127.0.0.1:27017`), you can use the same URI above.

## 4) Run the API

Start the server:

```bash
uvicorn main:app --reload
```

Open Swagger UI:
- http://127.0.0.1:8000/docs

## 5) API Endpoints (CRUD)

### SQL (MySQL/PostgreSQL) endpoints

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

### MongoDB endpoints

MongoDB uses string ids (ObjectId) and has its own route prefix:

- `POST /mongo/students`
- `GET /mongo/students?skip=0&limit=10`
- `GET /mongo/students/{id}`
- `PUT /mongo/students/{id}`
- `DELETE /mongo/students/{id}`

Example create body is the same:

```json
{
	"name": "Akhil",
	"age": 20
}
```

Response includes an `id` like:

```json
{
	"id": "663f6f9b2aa4d2a4f63a2e12",
	"name": "Akhil",
	"age": 20
}
```

## Differences Between MySQL vs PostgreSQL vs MongoDB

- **Data model**: MySQL/PostgreSQL are relational (tables/rows); MongoDB is document-based (JSON-like documents).
- **Schema**: SQL has a defined schema (migrations/DDL); MongoDB is flexible-schema (you enforce structure at the app level).
- **Transactions**: SQL databases are strong at multi-row/multi-table transactions; MongoDB supports transactions too, but many apps prefer document-level atomic updates.
- **Queries**: SQL is great for joins and analytics; MongoDB is great for hierarchical/nested data without joins.
- **Best fit**: SQL for structured data + relationships; MongoDB for rapidly evolving or nested data structures.

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