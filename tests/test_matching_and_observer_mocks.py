from unittest.mock import MagicMock

from lost_found.domain.models import ItemStatus, ItemType
from lost_found.modules.items import ItemService
from lost_found.modules.matching import MatchingService
from lost_found.modules.notifications import MatchNotificationObserver, NotificationSender
from lost_found.patterns.observer import EventBus
from lost_found.patterns.strategy import CategoryMatchStrategy, KeywordMatchStrategy


def test_matching_triggers_mocked_notification_sender_via_observer(repos, seeded_users, sample_dates):
    user_repo, item_repo, _ = repos
    alice, bob, _ = seeded_users
    d1, d2 = sample_dates

    mock_sender = MagicMock(spec=NotificationSender)
    mock_sender.send.return_value = True

    event_bus = EventBus()
    event_bus.subscribe("MATCH_FOUND", MatchNotificationObserver(mock_sender, user_repo))

    item_service = ItemService(item_repo, user_repo)
    lost = item_service.report_item(
        ItemType.LOST,
        alice.user_id,
        "Arduino Uno Kit",
        "electronics",
        "Blue Arduino board with jumper wires",
        "Robotics Lab",
        d1,
    )
    found = item_service.report_item(
        ItemType.FOUND,
        bob.user_id,
        "Arduino Uno Board",
        "electronics",
        "Found blue Arduino Uno with jumper wires",
        "Robotics Lab",
        d2,
    )

    matching_service = MatchingService(
        item_repo=item_repo,
        strategy=KeywordMatchStrategy(),
        event_bus=event_bus,
        min_threshold=0.35,
    )
    matches = matching_service.find_matches_for_item(lost.item_id)

    assert len(matches) == 1
    assert matches[0].found_item_id == found.item_id
    assert item_service.get_item(lost.item_id).status == ItemStatus.MATCHED

    mock_sender.send.assert_called_once()
    recipient, subject, body = mock_sender.send.call_args[0]
    assert recipient == alice.email
    assert "Arduino Uno Kit" in subject
    assert found.item_id in body


def test_swapping_matching_strategy_changes_candidate_selection(repos, seeded_users, sample_dates):
    user_repo, item_repo, _ = repos
    alice, bob, _ = seeded_users
    d1, d2 = sample_dates

    item_service = ItemService(item_repo, user_repo)
    lost = item_service.report_item(
        ItemType.LOST, alice.user_id, "ThinkPad Laptop", "electronics", "Black laptop", "Library", d1
    )
    item_service.report_item(
        ItemType.FOUND, bob.user_id, "Phone Charger", "electronics", "White cable", "Gym", d2
    )

    service = MatchingService(item_repo, strategy=KeywordMatchStrategy(), min_threshold=0.50)
    assert service.find_matches_for_item(lost.item_id, notify=False) == []

    service.set_strategy(CategoryMatchStrategy())
    category_matches = service.find_matches_for_item(lost.item_id, notify=False)
    assert len(category_matches) == 1
    assert category_matches[0].strategy_name == "CategoryMatch"
