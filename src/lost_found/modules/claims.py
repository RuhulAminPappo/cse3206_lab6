from __future__ import annotations

from typing import List, Optional

from lost_found.domain.models import Claim, ClaimStatus, DomainEvent, ItemStatus, generate_id
from lost_found.patterns.chain import (
    ClaimContext,
    VerificationHandler,
    build_default_verification_chain,
)
from lost_found.patterns.observer import EventBus
from lost_found.persistence.repository import ClaimRepository, ItemRepository, UserRepository


class ClaimService:
    """Module 4: Claim submission and Chain-of-Responsibility verification."""

    def __init__(
        self,
        claim_repo: ClaimRepository,
        item_repo: ItemRepository,
        user_repo: UserRepository,
        verification_chain: Optional[VerificationHandler] = None,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        self._claim_repo = claim_repo
        self._item_repo = item_repo
        self._user_repo = user_repo
        self._chain = verification_chain or build_default_verification_chain()
        self._event_bus = event_bus

    def submit_and_verify_claim(
        self,
        item_id: str,
        claimant_id: str,
        proof_detail: str,
    ) -> Claim:
        item = self._item_repo.get_by_id(item_id)
        if not item:
            raise LookupError(f"Item not found: {item_id}")

        claimant = self._user_repo.get_by_id(claimant_id)
        if not claimant:
            raise LookupError(f"Claimant not found: {claimant_id}")

        claim = Claim(
            claim_id=generate_id("CLM"),
            item_id=item_id,
            claimant_id=claimant_id,
            proof_detail=proof_detail.strip(),
        )

        result = self._chain.handle(ClaimContext(item=item, claim=claim, claimant=claimant))
        if result.approved:
            claim.status = ClaimStatus.APPROVED
            claim.review_note = result.reason
            self._item_repo.update_status(item.item_id, ItemStatus.CLAIMED)
        else:
            claim.status = ClaimStatus.REJECTED
            claim.review_note = f"[{result.failed_step}] {result.reason}"

        self._claim_repo.save(claim)

        if self._event_bus is not None:
            self._event_bus.publish(
                DomainEvent(
                    event_type="CLAIM_PROCESSED",
                    payload={
                        "claim_id": claim.claim_id,
                        "item_id": item.item_id,
                        "item_title": item.title,
                        "claimant_id": claimant.user_id,
                        "reporter_id": item.reporter_id,
                        "status": claim.status.value,
                        "review_note": claim.review_note,
                    },
                )
            )

        return claim

    def list_claims_for_item(self, item_id: str) -> List[Claim]:
        return self._claim_repo.list_by_item(item_id)
