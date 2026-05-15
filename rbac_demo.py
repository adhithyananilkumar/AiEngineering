#!/usr/bin/env python3
"""
RBAC System Demo Script
Demonstrates how to use the RBAC login system with JWT authentication.
"""

import requests
import json
from typing import Optional

BASE_URL = "http://127.0.0.1:8000"


class RBACClient:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.current_user = None

    def register(self, username: str, password: str, role: str = "user") -> dict:
        """Register a new user."""
        resp = requests.post(
            f"{self.base_url}/register",
            json={"username": username, "password": password, "role": role}
        )
        return resp.json()

    def login(self, username: str, password: str) -> bool:
        """Login and store access token."""
        resp = requests.post(
            f"{self.base_url}/token",
            data={"username": username, "password": password}
        )
        if resp.status_code == 200:
            data = resp.json()
            self.access_token = data["access_token"]
            self._get_current_user()
            return True
        return False

    def _get_current_user(self):
        """Fetch current user info."""
        if self.access_token:
            resp = requests.get(
                f"{self.base_url}/me",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            if resp.status_code == 200:
                self.current_user = resp.json()

    def get_me(self) -> Optional[dict]:
        """Get current user info."""
        if self.access_token:
            resp = requests.get(
                f"{self.base_url}/me",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            return resp.json() if resp.status_code == 200 else None
        return None

    def is_admin(self) -> bool:
        """Check if current user is admin."""
        return self.current_user and self.current_user.get("role") == "admin"

    def get_all_users(self) -> Optional[list]:
        """Get all users (admin only)."""
        if not self.access_token:
            print("❌ Not authenticated")
            return None
        
        resp = requests.get(
            f"{self.base_url}/admin/users",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 403:
            print("❌ Admin access required")
        else:
            print(f"❌ Error: {resp.status_code} - {resp.json()}")
        return None

    def create_user(self, username: str, password: str, role: str = "user") -> Optional[dict]:
        """Create a new user (admin only)."""
        if not self.access_token:
            print("❌ Not authenticated")
            return None
        
        resp = requests.post(
            f"{self.base_url}/admin/users",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json={"username": username, "password": password, "role": role}
        )
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 403:
            print("❌ Admin access required")
        else:
            print(f"❌ Error: {resp.status_code} - {resp.json()}")
        return None

    def delete_user(self, user_id: int) -> bool:
        """Delete a user (admin only)."""
        if not self.access_token:
            print("❌ Not authenticated")
            return False
        
        resp = requests.delete(
            f"{self.base_url}/admin/users/{user_id}",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        if resp.status_code == 200:
            return True
        elif resp.status_code == 403:
            print("❌ Admin access required")
        else:
            print(f"❌ Error: {resp.status_code} - {resp.json()}")
        return False


def main():
    """Demo the RBAC system."""
    print("\n" + "="*60)
    print("RBAC Login System Demo")
    print("="*60 + "\n")

    # Create client
    client = RBACClient()

    # 1. Register a regular user
    print("1️⃣ Registering regular user 'alice'...")
    result = client.register("alice", "password123", "user")
    print(f"   ✅ Registered: {result}\n")

    # 2. Register an admin user (normally done by admin or direct DB)
    print("2️⃣ Registering admin user 'admin'...")
    result = client.register("admin", "admin123", "admin")
    print(f"   ✅ Registered: {result}\n")

    # 3. Login as regular user
    print("3️⃣ Logging in as 'alice'...")
    if client.login("alice", "password123"):
        print(f"   ✅ Login successful!")
        user = client.get_me()
        print(f"   📌 User: {user}\n")
    else:
        print("   ❌ Login failed\n")
        return

    # 4. Try to access admin features (should fail)
    print("4️⃣ Trying to get all users as regular user (should fail)...")
    users = client.get_all_users()
    if users is None:
        print("   ✅ Correctly denied access\n")
    else:
        print(f"   ⚠️ Unexpected: {users}\n")

    # 5. Login as admin
    print("5️⃣ Logging in as 'admin'...")
    if client.login("admin", "admin123"):
        print(f"   ✅ Admin login successful!")
        user = client.get_me()
        print(f"   📌 User: {user}")
        print(f"   🔑 Is Admin: {client.is_admin()}\n")
    else:
        print("   ❌ Login failed\n")
        return

    # 6. Access admin features
    print("6️⃣ Getting all users as admin...")
    users = client.get_all_users()
    if users:
        print(f"   ✅ Users: {json.dumps(users, indent=2)}\n")

    # 7. Create new user via admin
    print("7️⃣ Creating new user 'bob' as admin...")
    result = client.create_user("bob", "bob_pass123", "user")
    if result:
        print(f"   ✅ Created: {result}\n")

    # 8. List users again
    print("8️⃣ Listing all users again...")
    users = client.get_all_users()
    if users:
        print(f"   ✅ Total users: {len(users)}")
        for u in users:
            print(f"      - {u['username']} ({u['role']})")
        print()

    # 9. Login as bob to verify
    print("9️⃣ Logging in as 'bob' to verify...")
    if client.login("bob", "bob_pass123"):
        print(f"   ✅ Bob login successful!")
        user = client.get_me()
        print(f"   📌 User: {user}")
        print(f"   🔑 Is Admin: {client.is_admin()}\n")
    else:
        print("   ❌ Bob login failed\n")

    print("="*60)
    print("✨ Demo complete!")
    print("="*60)


if __name__ == "__main__":
    main()
