from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from lost_found.domain.models import Claim, Item, ItemStatus, User


@dataclass(frozen=True)
class ClaimContext:
    item: Item
    claim: Claim
    claimant: User


@dataclass(frozen=True)
class VerificationResult:
    approved: bool
    reason: str
    failed_step: Optional[str] = None


class VerificationHandler(ABC):
    """Behavioral Pattern: Chain of Responsibility handler for multi-step claim verification."""

    def __init__(self) -> None:
        self._next: Optional[VerificationHandler] = None

    def set_next(self, handler: VerificationHandler) -> VerificationHandler:
        self._next = handler
        return handler

    def handle(self, context: ClaimContext) -> VerificationResult:
        result = self._check(context)
        if not result.approved:
            return result
        if self._next is not None:
            return self._next.handle(context)
        return VerificationResult(approved=True, reason="All verification checks passed.")

    @abstractmethod
    def _check(self, context: ClaimContext) -> VerificationResult:
        raise NotImplementedError


class ItemOpenHandler(VerificationHandler):
    """Step 1: Ensures the item has not already been claimed or closed."""

    def _check(self, context: ClaimContext) -> VerificationResult:
        if context.item.status in {ItemStatus.CLAIMED, ItemStatus.CLOSED}:
            return VerificationResult(
                approved=False,
                reason=f"Item {context.item.item_id} is already {context.item.status.value}.",
                failed_step="ItemOpenHandler",
            )
        return VerificationResult(approved=True, reason="Item is eligible for claim.")


class ClaimantNotReporterHandler(VerificationHandler):
    """Step 2: Prevents a finder/reporter from submitting a fraudulent self-claim."""

    def _check(self, context: ClaimContext) -> VerificationResult:
        if context.claimant.user_id == context.item.reporter_id:
            return VerificationResult(
                approved=False,
                reason="Reporter cannot submit an ownership claim on their own post.",
                failed_step="ClaimantNotReporterHandler",
            )
        return VerificationResult(approved=True, reason="Claimant identity validated.")


class SecretDetailHandler(VerificationHandler):
    """Step 3: Verifies ownership proof against hidden identifying details."""

    def _check(self, context: ClaimContext) -> VerificationResult:
        expected = context.item.secret_detail.strip().lower()
        provided = context.claim.proof_detail.strip().lower()
        if not expected:
            if len(provided) < 4:
                return VerificationResult(
                    approved=False,
                    reason="Insufficient proof description provided.",
                    failed_step="SecretDetailHandler",
                )
            return VerificationResult(approved=True, reason="Manual proof accepted.")

        if expected not in provided and provided not in expected:
            return VerificationResult(
                approved=False,
                reason="Provided proof detail does not match item secret identifier.",
                failed_step="SecretDetailHandler",
            )
        return VerificationResult(approved=True, reason="Secret identifying detail matched.")


def build_default_verification_chain() -> VerificationHandler:
    step1 = ItemOpenHandler()
    step2 = ClaimantNotReporterHandler()
    step3 = SecretDetailHandler()
    step1.set_next(step2).set_next(step3)
    return step1
