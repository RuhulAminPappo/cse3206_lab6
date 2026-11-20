from __future__ import annotations

from datetime import date
from typing import List

from lost_found.domain.models import Item, ItemStatus, ItemType
from lost_found.patterns.factory import ItemFactory
from lost_found.persistence.repository import ItemRepository, UserRepository


class ItemService:
    """Module 2: Lost & Found item posting and lifecycle management."""

    def __init__(self, item_repo: ItemRepository, user_repo: UserRepository) -> None:
        self._item_repo = item_repo
        self._user_repo = user_repo

    def report_item(
        self,
        item_type: ItemType | str,
        reporter_id: str,
        title: str,
        category: str,
        description: str,
        location: str,
        event_date: date,
        secret_detail: str = "",
    ) -> Item:
        if not self._user_repo.get_by_id(reporter_id):
            raise LookupError(f"Reporter does not exist: {reporter_id}")

        item = ItemFactory.create_item(
            item_type=item_type,
            reporter_id=reporter_id,
            title=title,
            category=category,
            description=description,
            location=location,
            event_date=event_date,
            secret_detail=secret_detail,
        )
        self._item_repo.save(item)
        return item

    def get_item(self, item_id: str) -> Item:
        item = self._item_repo.get_by_id(item_id)
        if not item:
            raise LookupError(f"Item not found: {item_id}")
        return item

    def list_items(self, item_type: ItemType | None = None, only_open: bool = True) -> List[Item]:
        if item_type is None:
            return self._item_repo.list_all()
        return self._item_repo.list_by_type(item_type, only_open=only_open)

    def mark_status(self, item_id: str, status: ItemStatus) -> Item:
        item = self.get_item(item_id)
        item.status = status
        self._item_repo.update_status(item_id, status)
        return item
