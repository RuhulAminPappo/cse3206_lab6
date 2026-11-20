from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Dict
import uuid


class ItemType(str, Enum):
    LOST = "LOST"
    FOUND = "FOUND"


class ItemStatus(str, Enum):
    OPEN = "OPEN"
    MATCHED = "MATCHED"
    CLAIMED = "CLAIMED"
    CLOSED = "CLOSED"


class ClaimStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass
class User:
    user_id: str
    name: str
    email: str
    department: str
    role: str = "STUDENT"


@dataclass
class Item:
    item_id: str
    reporter_id: str
    item_type: ItemType
    title: str
    category: str
    description: str
    location: str
    event_date: date
    secret_detail: str = ""
    status: ItemStatus = ItemStatus.OPEN
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class MatchCandidate:
    lost_item_id: str
    found_item_id: str
    score: float
    strategy_name: str
    reasons: tuple[str, ...] = ()


@dataclass
class Claim:
    claim_id: str
    item_id: str
    claimant_id: str
    proof_detail: str
    status: ClaimStatus = ClaimStatus.PENDING
    review_note: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class DomainEvent:
    event_type: str
    payload: Dict[str, Any]
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def generate_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"
