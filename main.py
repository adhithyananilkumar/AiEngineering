

import logging
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, FastAPI, Form, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

import crud
import mongo_crud
import models
import mongo_schemas
import schemas
from database import engine, get_db
from mongo_database import close_mongo_client, get_mongo_db
import auth


logger = logging.getLogger(__name__)


app = FastAPI(title="Student Management API", version="1.0.0")

SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "change-me-session-secret")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-jwt-secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))
DEMO_USERNAME = os.getenv("DEMO_USERNAME", "admin")
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "admin123")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

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


@app.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = crud.get_user_by_username(db, user.username)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")

    created = crud.create_user(db, user)
    return created


@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    access_token = auth.create_access_token(user.username)
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/me", response_model=schemas.UserOut)
def read_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    username = auth.decode_access_token(token)
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")

    user = crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


# RBAC Dependencies
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    """Get current user from JWT token."""
    username = auth.decode_access_token(token)
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    
    user = crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    """Dependency to require admin role."""
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


# Dashboard HTML Routes
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_redirect(request: Request):
    """Redirect to appropriate dashboard based on token in Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return RedirectResponse(url="/jwt/login", status_code=status.HTTP_303_SEE_OTHER)
    
    token = auth_header[7:]  # Remove "Bearer " prefix
    username = auth.decode_access_token(token)
    if not username:
        return RedirectResponse(url="/jwt/login", status_code=status.HTTP_303_SEE_OTHER)
    
    # Note: In practice, you'd query DB or store role in JWT payload
    # For now, redirect to /user-dashboard (can be enhanced)
    return RedirectResponse(url="/user-dashboard", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/admin-dashboard", response_class=HTMLResponse)
def admin_dashboard(current_user: models.User = Depends(require_admin)):
    """Admin dashboard - view and manage all users."""
    return render_page(
        "Admin Dashboard",
        f"""
        <h1>Admin Dashboard</h1>
        <p>Welcome, <strong>{current_user.username}</strong> (Admin)</p>
        
        <h2>User Management</h2>
        <button onclick="loadUsers()">Load All Users</button>
        <div id="users-list"></div>
        
        <h2>Create New User</h2>
        <form id="create-user-form">
            <label>Username:</label>
            <input type="text" id="new-username" required>
            <label>Password:</label>
            <input type="password" id="new-password" required>
            <label>Role:</label>
            <select id="new-role">
                <option value="user">User</option>
                <option value="admin">Admin</option>
            </select>
            <button type="button" onclick="createUser()">Create User</button>
        </form>
        
        <p><a class="button secondary" href="/jwt/logout">Logout</a></p>
        
        <script>
        async function loadUsers() {{
            const token = localStorage.getItem('access_token');
            const resp = await fetch('/admin/users', {{
                headers: {{'Authorization': 'Bearer ' + token}}
            }});
            const users = await resp.json();
            const html = users.map(u => `<div><strong>${{u.username}}</strong> - Role: ${{u.role}} 
                <button onclick="deleteUser(${{u.id}})">Delete</button></div>`).join('');
            document.getElementById('users-list').innerHTML = html;
        }}
        
        async function createUser() {{
            const username = document.getElementById('new-username').value;
            const password = document.getElementById('new-password').value;
            const role = document.getElementById('new-role').value;
            const token = localStorage.getItem('access_token');
            
            const resp = await fetch('/admin/users', {{
                method: 'POST',
                headers: {{'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}},
                body: JSON.stringify({{username, password, role}})
            }});
            if (resp.ok) alert('User created'); 
            else alert('Error: ' + await resp.text());
            loadUsers();
        }}
        
        async function deleteUser(userId) {{
            if (!confirm('Delete this user?')) return;
            const token = localStorage.getItem('access_token');
            const resp = await fetch('/admin/users/' + userId, {{
                method: 'DELETE',
                headers: {{'Authorization': 'Bearer ' + token}}
            }});
            if (resp.ok) alert('User deleted');
            loadUsers();
        }}
        </script>
        """,
    )


@app.get("/user-dashboard", response_class=HTMLResponse)
def user_dashboard(current_user: models.User = Depends(get_current_user)):
    """User dashboard - view own profile."""
    return render_page(
        "User Dashboard",
        f"""
        <h1>User Dashboard</h1>
        <p>Welcome, <strong>{current_user.username}</strong></p>
        
        <h2>Your Profile</h2>
        <p><strong>ID:</strong> {current_user.id}</p>
        <p><strong>Username:</strong> {current_user.username}</p>
        <p><strong>Role:</strong> {current_user.role.value}</p>
        
        {"<p><a class='button' href='/admin-dashboard'>Go to Admin Dashboard</a></p>" if current_user.role == models.UserRole.ADMIN else ""}
        
        <p><a class="button secondary" href="/jwt/logout">Logout</a></p>
        """,
    )


# Admin API Endpoints for user management
@app.get("/admin/users", response_model=list[schemas.UserOut])
def get_all_users(current_user: models.User = Depends(require_admin), db: Session = Depends(get_db)):
    """Get all users (admin only)."""
    return db.query(models.User).all()


@app.post("/admin/users", response_model=schemas.UserOut)
def create_user_as_admin(
    user: schemas.UserCreate,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a new user (admin only)."""
    existing = crud.get_user_by_username(db, user.username)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    
    return crud.create_user(db, user)


@app.delete("/admin/users/{user_id}")
def delete_user_as_admin(
    user_id: int,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Delete a user (admin only)."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if user.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself")
    
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}


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