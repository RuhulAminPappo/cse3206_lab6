from __future__ import annotations

from typing import List, Optional

from lost_found.domain.models import DomainEvent, ItemStatus, ItemType, MatchCandidate
from lost_found.patterns.observer import EventBus
from lost_found.patterns.strategy import MatchingStrategy
from lost_found.persistence.repository import ItemRepository


class MatchingService:
    """Module 3: Smart matching engine using swappable Strategy and Observer events."""

    def __init__(
        self,
        item_repo: ItemRepository,
        strategy: MatchingStrategy,
        event_bus: Optional[EventBus] = None,
        min_threshold: float = 0.40,
    ) -> None:
        self._item_repo = item_repo
        self._strategy = strategy
        self._event_bus = event_bus
        self._min_threshold = min_threshold

    @property
    def strategy(self) -> MatchingStrategy:
        return self._strategy

    def set_strategy(self, strategy: MatchingStrategy) -> None:
        self._strategy = strategy

    def find_matches_for_item(self, item_id: str, notify: bool = True) -> List[MatchCandidate]:
        target = self._item_repo.get_by_id(item_id)
        if not target:
            raise LookupError(f"Item not found: {item_id}")

        opposite_type = ItemType.FOUND if target.item_type == ItemType.LOST else ItemType.LOST
        pool = self._item_repo.list_by_type(opposite_type, only_open=True)

        candidates: List[MatchCandidate] = []
        for other in pool:
            if other.reporter_id == target.reporter_id:
                continue
            lost_item = target if target.item_type == ItemType.LOST else other
            found_item = other if target.item_type == ItemType.LOST else target

            score, reason = self._strategy.compute_score(lost_item, found_item)
            if score >= self._min_threshold:
                candidates.append(
                    MatchCandidate(
                        lost_item_id=lost_item.item_id,
                        found_item_id=found_item.item_id,
                        score=score,
                        strategy_name=self._strategy.name,
                        reasons=(reason,),
                    )
                )

        candidates.sort(key=lambda c: c.score, reverse=True)

        if candidates:
            if target.status == ItemStatus.OPEN:
                self._item_repo.update_status(target.item_id, ItemStatus.MATCHED)
            if notify and self._event_bus is not None:
                top = candidates[0]
                lost_obj = self._item_repo.get_by_id(top.lost_item_id)
                found_obj = self._item_repo.get_by_id(top.found_item_id)
                self._event_bus.publish(
                    DomainEvent(
                        event_type="MATCH_FOUND",
                        payload={
                            "lost_item_id": top.lost_item_id,
                            "found_item_id": top.found_item_id,
                            "lost_owner_id": lost_obj.reporter_id if lost_obj else "",
                            "finder_id": found_obj.reporter_id if found_obj else "",
                            "item_title": lost_obj.title if lost_obj else target.title,
                            "score": top.score,
                            "strategy": top.strategy_name,
                        },
                    )
                )

        return candidates
