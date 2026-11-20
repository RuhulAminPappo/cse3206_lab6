import pytest

from lost_found.domain.models import ItemStatus, ItemType
from lost_found.modules.items import ItemService
from lost_found.patterns.factory import ItemFactory


def test_factory_creates_lost_and_found_items_with_normalized_fields(sample_dates):
    d1, d2 = sample_dates
    lost = ItemFactory.create_lost_item(
        reporter_id="USR-ALICE",
        title="  Blue Water Bottle  ",
        category="Accessories",
        description="Insulated flask",
        location="Library",
        event_date=d1,
        secret_detail="Dent at Bottom",
    )
    found = ItemFactory.create_found_item(
        reporter_id="USR-BOB",
        title="Blue Flask",
        category="accessories",
        description="Found near reading hall",
        location="Library",
        event_date=d2,
    )

    assert lost.item_id.startswith("LST-")
    assert lost.item_type == ItemType.LOST
    assert lost.category == "accessories"
    assert lost.secret_detail == "dent at bottom"
    assert lost.status == ItemStatus.OPEN

    assert found.item_id.startswith("FND-")
    assert found.item_type == ItemType.FOUND


def test_factory_rejects_missing_required_fields(sample_dates):
    d1, _ = sample_dates
    with pytest.raises(ValueError, match="title is required"):
        ItemFactory.create_lost_item("USR-ALICE", "   ", "electronics", "desc", "CSE", d1)


def test_item_service_persists_and_updates_status(repos, seeded_users, sample_dates):
    user_repo, item_repo, _ = repos
    alice, _, _ = seeded_users
    d1, _ = sample_dates

    service = ItemService(item_repo, user_repo)
    created = service.report_item(
        ItemType.LOST,
        alice.user_id,
        "ID Card",
        "documents",
        "Student ID card",
        "Cafeteria",
        d1,
    )

    fetched = service.get_item(created.item_id)
    assert fetched.title == "ID Card"

    updated = service.mark_status(created.item_id, ItemStatus.CLAIMED)
    assert updated.status == ItemStatus.CLAIMED
    assert service.get_item(created.item_id).status == ItemStatus.CLAIMED


def test_item_service_rejects_unknown_reporter(repos, sample_dates):
    user_repo, item_repo, _ = repos
    d1, _ = sample_dates
    service = ItemService(item_repo, user_repo)

    with pytest.raises(LookupError, match="Reporter does not exist"):
        service.report_item(ItemType.LOST, "USR-UNKNOWN", "Keys", "other", "Room keys", "Gate", d1)
