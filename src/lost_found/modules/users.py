from __future__ import annotations

from typing import List, Optional

from lost_found.domain.models import User, generate_id
from lost_found.persistence.repository import UserRepository


class UserService:
    """Module 1: Campus user registration and lookup."""

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    def register_user(
        self,
        name: str,
        email: str,
        department: str,
        role: str = "STUDENT",
        user_id: Optional[str] = None,
    ) -> User:
        if not name.strip():
            raise ValueError("User name cannot be empty.")
        if "@" not in email:
            raise ValueError("Invalid email address.")
        user = User(
            user_id=user_id or generate_id("USR"),
            name=name.strip(),
            email=email.strip().lower(),
            department=department.strip().upper(),
            role=role.strip().upper(),
        )
        self._user_repo.save(user)
        return user

    def get_user(self, user_id: str) -> User:
        user = self._user_repo.get_by_id(user_id)
        if not user:
            raise LookupError(f"User not found: {user_id}")
        return user

    def list_users(self) -> List[User]:
        return self._user_repo.list_all()
