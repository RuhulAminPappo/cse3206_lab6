from __future__ import annotations

from datetime import date, datetime
import sqlite3
from typing import List, Optional

from lost_found.domain.models import Claim, ClaimStatus, Item, ItemStatus, ItemType, User
from lost_found.persistence.repository import ClaimRepository, ItemRepository, UserRepository


class SQLiteDatabase:
    def __init__(self, db_path: str = "lost_found.db") -> None:
        self.db_path = db_path
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    @property
    def connection(self) -> sqlite3.Connection:
        return self._conn

    def _init_schema(self) -> None:
        cur = self._conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                department TEXT NOT NULL,
                role TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS items (
                item_id TEXT PRIMARY KEY,
                reporter_id TEXT NOT NULL,
                item_type TEXT NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                location TEXT NOT NULL,
                event_date TEXT NOT NULL,
                secret_detail TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (reporter_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS claims (
                claim_id TEXT PRIMARY KEY,
                item_id TEXT NOT NULL,
                claimant_id TEXT NOT NULL,
                proof_detail TEXT NOT NULL,
                status TEXT NOT NULL,
                review_note TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (item_id) REFERENCES items(item_id),
                FOREIGN KEY (claimant_id) REFERENCES users(user_id)
            );
            """
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()


class SQLiteUserRepository(UserRepository):
    def __init__(self, db: SQLiteDatabase) -> None:
        self._conn = db.connection

    def save(self, user: User) -> None:
        self._conn.execute(
            """
            INSERT OR REPLACE INTO users (user_id, name, email, department, role)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user.user_id, user.name, user.email, user.department, user.role),
        )
        self._conn.commit()

    def get_by_id(self, user_id: str) -> Optional[User]:
        row = self._conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if not row:
            return None
        return User(
            user_id=row["user_id"],
            name=row["name"],
            email=row["email"],
            department=row["department"],
            role=row["role"],
        )

    def list_all(self) -> List[User]:
        rows = self._conn.execute("SELECT * FROM users ORDER BY user_id").fetchall()
        return [
            User(
                user_id=r["user_id"],
                name=r["name"],
                email=r["email"],
                department=r["department"],
                role=r["role"],
            )
            for r in rows
        ]


class SQLiteItemRepository(ItemRepository):
    def __init__(self, db: SQLiteDatabase) -> None:
        self._conn = db.connection

    @staticmethod
    def _row_to_item(row: sqlite3.Row) -> Item:
        return Item(
            item_id=row["item_id"],
            reporter_id=row["reporter_id"],
            item_type=ItemType(row["item_type"]),
            title=row["title"],
            category=row["category"],
            description=row["description"],
            location=row["location"],
            event_date=date.fromisoformat(row["event_date"]),
            secret_detail=row["secret_detail"],
            status=ItemStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def save(self, item: Item) -> None:
        self._conn.execute(
            """
            INSERT OR REPLACE INTO items (
                item_id, reporter_id, item_type, title, category,
                description, location, event_date, secret_detail, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.item_id,
                item.reporter_id,
                item.item_type.value,
                item.title,
                item.category,
                item.description,
                item.location,
                item.event_date.isoformat(),
                item.secret_detail,
                item.status.value,
                item.created_at.isoformat(),
            ),
        )
        self._conn.commit()

    def get_by_id(self, item_id: str) -> Optional[Item]:
        row = self._conn.execute("SELECT * FROM items WHERE item_id = ?", (item_id,)).fetchone()
        return self._row_to_item(row) if row else None

    def list_by_type(self, item_type: ItemType, only_open: bool = True) -> List[Item]:
        if only_open:
            rows = self._conn.execute(
                "SELECT * FROM items WHERE item_type = ? AND status IN ('OPEN', 'MATCHED') ORDER BY created_at DESC",
                (item_type.value,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM items WHERE item_type = ? ORDER BY created_at DESC",
                (item_type.value,),
            ).fetchall()
        return [self._row_to_item(r) for r in rows]

    def list_all(self) -> List[Item]:
        rows = self._conn.execute("SELECT * FROM items ORDER BY created_at DESC").fetchall()
        return [self._row_to_item(r) for r in rows]

    def update_status(self, item_id: str, status: ItemStatus) -> None:
        self._conn.execute(
            "UPDATE items SET status = ? WHERE item_id = ?",
            (status.value, item_id),
        )
        self._conn.commit()


class SQLiteClaimRepository(ClaimRepository):
    def __init__(self, db: SQLiteDatabase) -> None:
        self._conn = db.connection

    @staticmethod
    def _row_to_claim(row: sqlite3.Row) -> Claim:
        return Claim(
            claim_id=row["claim_id"],
            item_id=row["item_id"],
            claimant_id=row["claimant_id"],
            proof_detail=row["proof_detail"],
            status=ClaimStatus(row["status"]),
            review_note=row["review_note"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def save(self, claim: Claim) -> None:
        self._conn.execute(
            """
            INSERT OR REPLACE INTO claims (
                claim_id, item_id, claimant_id, proof_detail, status, review_note, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                claim.claim_id,
                claim.item_id,
                claim.claimant_id,
                claim.proof_detail,
                claim.status.value,
                claim.review_note,
                claim.created_at.isoformat(),
            ),
        )
        self._conn.commit()

    def get_by_id(self, claim_id: str) -> Optional[Claim]:
        row = self._conn.execute("SELECT * FROM claims WHERE claim_id = ?", (claim_id,)).fetchone()
        return self._row_to_claim(row) if row else None

    def list_by_item(self, item_id: str) -> List[Claim]:
        rows = self._conn.execute(
            "SELECT * FROM claims WHERE item_id = ? ORDER BY created_at DESC", (item_id,)
        ).fetchall()
        return [self._row_to_claim(r) for r in rows]
