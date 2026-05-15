# RBAC Login System Guide

This guide covers the Role-Based Access Control (RBAC) login system with JWT authentication, MySQL storage, and admin/user dashboards.

## Architecture

- **Database**: MySQL (via SQLAlchemy ORM)
- **Authentication**: JWT tokens + Password hashing (bcrypt)
- **Roles**: `admin`, `user` (Enum-based)
- **Dashboards**: HTML UI for admin and user boards

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(150) UNIQUE NOT NULL,
    hashed_password VARCHAR(256) NOT NULL,
    role ENUM('admin', 'user') DEFAULT 'user' NOT NULL,
    INDEX idx_username (username)
);
```

## API Endpoints

### Authentication
| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/register` | POST | Register new user | None |
| `/token` | POST | Get JWT access token | None |
| `/me` | GET | Get current user profile | JWT |

### User Dashboards
| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/user-dashboard` | GET | User dashboard (HTML) | JWT |
| `/admin-dashboard` | GET | Admin dashboard (HTML) | JWT + Admin role |

### Admin APIs
| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/admin/users` | GET | List all users | JWT + Admin |
| `/admin/users` | POST | Create user | JWT + Admin |
| `/admin/users/{id}` | DELETE | Delete user | JWT + Admin |

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Server
```bash
uvicorn main:app --reload
```

### 3. Register a User (Regular User)
```bash
curl -X POST http://127.0.0.1:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}'
```

### 4. Login and Get Token
```bash
curl -X POST http://127.0.0.1:8000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'username=alice&password=password123'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 5. Access User Dashboard
```bash
curl -H "Authorization: Bearer <ACCESS_TOKEN>" \
  http://127.0.0.1:8000/user-dashboard
```

## Admin-Only Operations

### Create Admin User (Direct DB or API)

**Option A: Via API (if you have admin token)**
```bash
curl -X POST http://127.0.0.1:8000/admin/users \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"username":"bob","password":"secure123","role":"admin"}'
```

**Option B: Direct Database**
```sql
INSERT INTO users (username, hashed_password, role) 
VALUES ('admin', '<hashed_password>', 'admin');
```

### Get Admin Token
```bash
curl -X POST http://127.0.0.1:8000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'username=admin&password=secure123'
```

### Access Admin Dashboard
```bash
curl http://127.0.0.1:8000/admin-dashboard \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

## Admin Dashboard Features

The admin dashboard (`/admin-dashboard`) provides:
- **View all users**: Click "Load All Users" to fetch and display all registered users
- **Create new user**: Form to add new users with custom roles
- **Delete users**: Remove users from the system (cannot delete self)
- **User management**: Full control over user accounts

## User Dashboard Features

The user dashboard (`/user-dashboard`) provides:
- **View profile**: Display user ID, username, and role
- **Role-based UI**: Shows admin dashboard link if user has admin role

## Security Features

✅ **Password Security**
- Passwords hashed with bcrypt (`passlib[bcrypt]`)
- Never stored in plaintext

✅ **JWT Tokens**
- Short-lived tokens (default 30 minutes, configurable)
- Signed with secret key
- Decoded on each request

✅ **Role-Based Access Control**
- Admin endpoints require admin role
- Returns 403 Forbidden if insufficient permissions
- Role stored in database

✅ **Session Management**
- HTTP-only cookies (for session-based endpoints)
- CSRF protection via `SameSite=Lax`

## Environment Variables

```bash
# JWT Configuration
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# Session Configuration
SESSION_SECRET_KEY=your-session-secret-key

# Database (from .env or environment)
DATABASE_URL=mysql+pymysql://user:password@localhost/dbname
# or DB_DIALECT=mysql, DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
```

## Error Responses

### Unauthorized (401)
```json
{
  "detail": "Invalid authentication credentials"
}
```

### Forbidden (403)
```json
{
  "detail": "Admin access required"
}
```

### Conflict (400)
```json
{
  "detail": "Username already registered"
}
```

## Database Migration

To add roles to existing users, run:
```sql
ALTER TABLE users ADD COLUMN role ENUM('admin', 'user') DEFAULT 'user';

-- Or update specific users to admin
UPDATE users SET role='admin' WHERE username='admin';
```

## Testing with Postman

Import this collection structure:
```
├── Auth
│   ├── Register User
│   ├── Login (Get Token)
│   └── Get Current User (/me)
├── Admin APIs
│   ├── List All Users
│   ├── Create User
│   └── Delete User
└── Dashboards
    ├── User Dashboard
    └── Admin Dashboard
```

Each request needs:
- **Authorization Header**: `Authorization: Bearer <TOKEN>` (except register/login)
- **Content-Type**: `application/json` for POST requests

## Troubleshooting

**"Admin access required"**
- Make sure you're using an admin token
- Verify the user has `role='admin'` in database

**"Invalid authentication credentials"**
- Check token expiration (default 30 min)
- Verify JWT_SECRET_KEY matches between encoding/decoding

**"Username already registered"**
- Pick a different username
- Check for existing users: `/admin/users` (requires admin)

**Database connection error**
- Verify MySQL is running
- Check DATABASE_URL env variable
- Ensure credentials are correct

## Next Steps

- Add email verification
- Implement token refresh
- Add audit logging
- Rate limiting on login attempts
- Two-factor authentication (2FA)
