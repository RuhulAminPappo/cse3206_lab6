from __future__ import annotations

from datetime import date
from typing import Optional

from lost_found.domain.models import Item, ItemStatus, ItemType, generate_id


class ItemFactory:
    """Creational Pattern: Factory Method for constructing validated Lost/Found items."""

    @staticmethod
    def create_item(
        item_type: ItemType | str,
        reporter_id: str,
        title: str,
        category: str,
        description: str,
        location: str,
        event_date: date,
        secret_detail: str = "",
        item_id: Optional[str] = None,
    ) -> Item:
        normalized_type = (
            item_type if isinstance(item_type, ItemType) else ItemType(item_type.strip().upper())
        )
        if not reporter_id or not reporter_id.strip():
            raise ValueError("reporter_id is required.")
        if not title or not title.strip():
            raise ValueError("title is required.")
        if not category or not category.strip():
            raise ValueError("category is required.")
        if not location or not location.strip():
            raise ValueError("location is required.")

        prefix = "LST" if normalized_type == ItemType.LOST else "FND"
        resolved_id = item_id or generate_id(prefix)

        return Item(
            item_id=resolved_id,
            reporter_id=reporter_id.strip(),
            item_type=normalized_type,
            title=title.strip(),
            category=category.strip().lower(),
            description=description.strip(),
            location=location.strip(),
            event_date=event_date,
            secret_detail=secret_detail.strip().lower(),
            status=ItemStatus.OPEN,
        )

    @classmethod
    def create_lost_item(
        cls,
        reporter_id: str,
        title: str,
        category: str,
        description: str,
        location: str,
        event_date: date,
        secret_detail: str = "",
    ) -> Item:
        return cls.create_item(
            item_type=ItemType.LOST,
            reporter_id=reporter_id,
            title=title,
            category=category,
            description=description,
            location=location,
            event_date=event_date,
            secret_detail=secret_detail,
        )

    @classmethod
    def create_found_item(
        cls,
        reporter_id: str,
        title: str,
        category: str,
        description: str,
        location: str,
        event_date: date,
        secret_detail: str = "",
    ) -> Item:
        return cls.create_item(
            item_type=ItemType.FOUND,
            reporter_id=reporter_id,
            title=title,
            category=category,
            description=description,
            location=location,
            event_date=event_date,
            secret_detail=secret_detail,
        )
