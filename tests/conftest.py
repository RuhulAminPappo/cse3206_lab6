from datetime import date
import pytest

from lost_found.modules.users import UserService
from lost_found.persistence.sqlite_repo import (
    SQLiteClaimRepository,
    SQLiteDatabase,
    SQLiteItemRepository,
    SQLiteUserRepository,
)


@pytest.fixture
def db():
    database = SQLiteDatabase(":memory:")
    yield database
    database.close()


@pytest.fixture
def repos(db):
    return (
        SQLiteUserRepository(db),
        SQLiteItemRepository(db),
        SQLiteClaimRepository(db),
    )


@pytest.fixture
def seeded_users(repos):
    user_repo, _, _ = repos
    user_service = UserService(user_repo)
    alice = user_service.register_user("Ayesha", "ayesha@ruet.ac.bd", "CSE", user_id="USR-ALICE")
    bob = user_service.register_user("Tanvir", "tanvir@ruet.ac.bd", "EEE", user_id="USR-BOB")
    charlie = user_service.register_user("Nusrat", "nusrat@ruet.ac.bd", "ME", user_id="USR-CHARLIE")
    return alice, bob, charlie


@pytest.fixture
def sample_dates():
    return date(2026, 11, 15), date(2026, 11, 16)
