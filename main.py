

import logging
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, FastAPI, Form, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session

import crud
import mongo_crud
import models
import mongo_schemas
import schemas
from database import engine, get_db
from mongo_database import close_mongo_client, get_mongo_db


logger = logging.getLogger(__name__)


app = FastAPI(title="Student Management API", version="1.0.0")

SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "change-me-session-secret")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-jwt-secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))
DEMO_USERNAME = os.getenv("DEMO_USERNAME", "admin")
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "admin123")

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY,
    same_site="lax",
    https_only=False,
)


def render_page(title: str, body: str) -> HTMLResponse:
    return HTMLResponse(
        f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f7fb; color: #111827; }}
        .card {{ max-width: 420px; margin: 0 auto; background: white; padding: 24px; border-radius: 12px; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08); }}
        input {{ width: 100%; padding: 10px; margin: 8px 0 16px; box-sizing: border-box; }}
        button, a.button {{ display: inline-block; padding: 10px 14px; border: 0; border-radius: 8px; background: #2563eb; color: white; text-decoration: none; cursor: pointer; }}
        a.button.secondary {{ background: #6b7280; }}
        .error {{ color: #b91c1c; margin-bottom: 12px; }}
        .links a {{ margin-right: 12px; }}
    </style>
</head>
<body>
    <div class="card">
        {body}
    </div>
</body>
</html>"""
    )


def login_form(title: str, action: str, error: str | None = None) -> HTMLResponse:
    error_html = f'<div class="error">{error}</div>' if error else ""
    return render_page(
        title,
        f"""
        <h1>{title}</h1>
        {error_html}
        <form method="post" action="{action}">
            <label>Username</label>
            <input name="username" value="admin" autocomplete="username">
            <label>Password</label>
            <input name="password" type="password" value="admin123" autocomplete="current-password">
            <button type="submit">Login</button>
        </form>
        <p><a href="/auth">Back to auth demo</a></p>
        """,
    )


def auth_home() -> HTMLResponse:
    return render_page(
        "Auth Demo",
        """
        <h1>Auth Demo</h1>
        <p>Minimal login examples for study.</p>
        <div class="links">
            <a class="button" href="/session/login">Session Login</a>
            <a class="button secondary" href="/jwt/login">JWT Login</a>
        </div>
        """,
    )


def create_jwt_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def read_jwt_token(request: Request) -> str | None:
    return request.cookies.get("access_token")


def require_jwt_user(request: Request) -> str | None:
    token = read_jwt_token(request)
    if not token:
        return None

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None

    return payload.get("sub")


@app.on_event("startup")
def on_startup():
    try:
        models.Base.metadata.create_all(bind=engine)
    except Exception as exc:  # noqa: BLE001
        strict = os.getenv("SQL_STARTUP_STRICT", "false").strip().lower() in {
            "1",
            "true",
            "yes",
        }
        message = (
            "SQL database init failed. SQL endpoints (/students) may not work until configured. "
            "Set DB_DIALECT (mysql/postgresql) + DB_* env vars, or provide DATABASE_URL."
        )
        if strict:
            raise RuntimeError(message) from exc
        logger.warning("%s Error=%r", message, exc)


@app.on_event("shutdown")
def on_shutdown():
    close_mongo_client()


@app.get("/")
def root():

    return {"message": "API is running"}


@app.get("/auth", response_class=HTMLResponse)
def auth_demo():
    return auth_home()


@app.get("/session/login", response_class=HTMLResponse)
def session_login_page(request: Request):
    if request.session.get("user"):
        return RedirectResponse(url="/session/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return login_form("Session Login", "/session/login")


@app.post("/session/login", response_class=HTMLResponse)
def session_login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username != DEMO_USERNAME or password != DEMO_PASSWORD:
        return login_form("Session Login", "/session/login", "Invalid username or password")

    request.session["user"] = username
    return RedirectResponse(url="/session/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/session/dashboard", response_class=HTMLResponse)
def session_dashboard(request: Request):
    username = request.session.get("user")
    if not username:
        return RedirectResponse(url="/session/login", status_code=status.HTTP_303_SEE_OTHER)

    return render_page(
        "Session Dashboard",
        f"""
        <h1>Session Dashboard</h1>
        <p>Logged in as <strong>{username}</strong>.</p>
        <p>Session data is stored in a signed cookie by the session middleware.</p>
        <p><a class="button secondary" href="/session/logout">Logout</a></p>
        """,
    )


@app.get("/session/logout")
def session_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/session/login", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/jwt/login", response_class=HTMLResponse)
def jwt_login_page(request: Request):
    if require_jwt_user(request):
        return RedirectResponse(url="/jwt/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return login_form("JWT Login", "/jwt/login")


@app.post("/jwt/login", response_class=HTMLResponse)
def jwt_login(username: str = Form(...), password: str = Form(...)):
    if username != DEMO_USERNAME or password != DEMO_PASSWORD:
        return login_form("JWT Login", "/jwt/login", "Invalid username or password")

    token = create_jwt_token(username)
    response = RedirectResponse(url="/jwt/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
    )
    return response


@app.get("/jwt/dashboard", response_class=HTMLResponse)
def jwt_dashboard(request: Request):
    username = require_jwt_user(request)
    if not username:
        return RedirectResponse(url="/jwt/login", status_code=status.HTTP_303_SEE_OTHER)

    return render_page(
        "JWT Dashboard",
        f"""
        <h1>JWT Dashboard</h1>
        <p>Logged in as <strong>{username}</strong>.</p>
        <p>The access token is stored in an HTTP-only cookie.</p>
        <p><a class="button secondary" href="/jwt/logout">Logout</a></p>
        """,
    )


@app.get("/jwt/logout")
def jwt_logout():
    response = RedirectResponse(url="/jwt/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response


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