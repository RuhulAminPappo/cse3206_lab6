from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Tuple

from lost_found.domain.models import DomainEvent
from lost_found.patterns.observer import EventObserver
from lost_found.persistence.repository import UserRepository


class NotificationSender(ABC):
    """Module 5: External delivery boundary (primary mock target in unit tests)."""

    @abstractmethod
    def send(self, recipient_email: str, subject: str, body: str) -> bool:
        raise NotImplementedError


class ConsoleNotificationSender(NotificationSender):
    """Default local sender recording dispatched messages."""

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose
        self.sent_messages: List[Tuple[str, str, str]] = []

    def send(self, recipient_email: str, subject: str, body: str) -> bool:
        self.sent_messages.append((recipient_email, subject, body))
        if self.verbose:
            print(f"[NOTIFICATION -> {recipient_email}] {subject}: {body}")
        return True


class MatchNotificationObserver(EventObserver):
    """Observer translating MATCH_FOUND events into user alerts via NotificationSender."""

    def __init__(self, sender: NotificationSender, user_repo: UserRepository) -> None:
        self._sender = sender
        self._user_repo = user_repo

    def update(self, event: DomainEvent) -> None:
        if event.event_type != "MATCH_FOUND":
            return
        owner = self._user_repo.get_by_id(event.payload.get("lost_owner_id", ""))
        if not owner:
            return
        title = event.payload.get("item_title", "your item")
        score = event.payload.get("score", 0.0)
        found_id = event.payload.get("found_item_id", "")
        subject = f"Potential Match Found for '{title}'"
        body = (
            f"Hi {owner.name}, found report {found_id} matched your lost item '{title}' "
            f"with confidence score {score:.2f}."
        )
        self._sender.send(owner.email, subject, body)


class ClaimStatusNotificationObserver(EventObserver):
    """Observer notifying claimants when their claim is approved or rejected."""

    def __init__(self, sender: NotificationSender, user_repo: UserRepository) -> None:
        self._sender = sender
        self._user_repo = user_repo

    def update(self, event: DomainEvent) -> None:
        if event.event_type != "CLAIM_PROCESSED":
            return
        claimant = self._user_repo.get_by_id(event.payload.get("claimant_id", ""))
        if not claimant:
            return
        status = event.payload.get("status", "UPDATED")
        title = event.payload.get("item_title", "item")
        note = event.payload.get("review_note", "")
        subject = f"Claim {status}: {title}"
        body = f"Hi {claimant.name}, your claim status is {status}. Details: {note}"
        self._sender.send(claimant.email, subject, body)
