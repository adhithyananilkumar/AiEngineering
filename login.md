# Session Login vs JWT Login

This repo has two simple login demos in [main.py](main.py):

- Session login: `/session/login`
- JWT login: `/jwt/login`

Both use the same demo credentials:

- username: `admin`
- password: `admin123`

## 1) Session Login

### How it works

1. User submits the login form.
2. Server checks the username and password.
3. If valid, the app stores the user in `request.session["user"]`.
4. Starlette session middleware writes the session into a signed cookie.
5. On the next request, the cookie is sent back and the app reads the session data.

### What is stored

- A signed session cookie in the browser.
- In this demo, the session data is small and kept inside the cookie itself.

### Main issues

- If the session data gets too large, cookie size becomes a problem.
- If the secret key changes, old sessions become invalid.
- Because it uses cookies, it still needs CSRF protection for unsafe requests.

### Good for

- Simple server-rendered apps.
- Traditional web apps where you want easy login state.

## 2) JWT Login

### How it works

1. User submits the login form.
2. Server checks the username and password.
3. If valid, the app creates a JWT with a subject and expiry.
4. The JWT is stored in an HTTP-only cookie named `access_token`.
5. On later requests, the app reads the cookie and verifies the token signature.

### What is stored

- A JWT string in an HTTP-only cookie.
- The token itself contains claims like `sub` and `exp`.

### Main issues

- JWTs are hard to revoke immediately unless you add server-side tracking.
- If the token is stolen before expiry, it can be reused.
- Very long-lived tokens are risky.

### Good for

- APIs and stateless auth.
- Apps where multiple services need to verify the same token.

## 3) Key Difference

- Session login: browser stores a signed session cookie, server reads session state from that cookie.
- JWT login: browser stores a token, server validates the token signature and reads claims from it.

Practical short version:

- Session = login state managed with session middleware.
- JWT = login state managed with a signed token.

## 4) How To Inspect In Browser DevTools

Open the app and log in using each page.

### A. Check the cookie

1. Open DevTools with `F12` or `Ctrl+Shift+I`.
2. Go to `Application` or `Storage`.
3. Open `Cookies` for `http://127.0.0.1:8000`.
4. Compare the cookie values.

What to look for:

- Session login: a session cookie created by the middleware.
- JWT login: an `access_token` cookie with a long JWT string.

### B. Check the network request

1. Open the `Network` tab.
2. Submit the login form.
3. Click the `POST /session/login` or `POST /jwt/login` request.
4. Inspect `Headers`.

What to look for:

- `Set-Cookie` response header after login.
- Redirect response to the dashboard page.

### C. Check what is readable by JavaScript

- Session cookie in this demo is still cookie-based, but HTTP-only cookies cannot be read with `document.cookie`.
- JWT cookie is also set as HTTP-only, so it is also hidden from JavaScript.

That means:

- You inspect both in DevTools, not in normal page JavaScript.

## 5) Simple Testing Flow

### Session

1. Open `/session/login`.
2. Log in.
3. Open DevTools and check cookies.
4. Refresh the dashboard.
5. Click logout and confirm the cookie is removed.

### JWT

1. Open `/jwt/login`.
2. Log in.
3. Open DevTools and check the `access_token` cookie.
4. Refresh the dashboard.
5. Click logout and confirm the cookie is removed.

## 6) Important Note

In this project, both flows are cookie-based for simplicity.

- The session demo uses Starlette session middleware.
- The JWT demo stores the token in a cookie.

So both can be inspected in browser DevTools, but the data inside them is different.
