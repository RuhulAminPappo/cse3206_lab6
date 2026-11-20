from unittest.mock import MagicMock

from lost_found.domain.models import ClaimStatus, ItemStatus, ItemType
from lost_found.modules.claims import ClaimService
from lost_found.modules.items import ItemService
from lost_found.modules.notifications import ClaimStatusNotificationObserver, NotificationSender
from lost_found.patterns.observer import EventBus


def test_claim_verification_chain_approves_valid_claim_and_notifies(repos, seeded_users, sample_dates):
    user_repo, item_repo, claim_repo = repos
    alice, bob, _ = seeded_users
    d1, _ = sample_dates

    mock_sender = MagicMock(spec=NotificationSender)
    bus = EventBus()
    bus.subscribe("CLAIM_PROCESSED", ClaimStatusNotificationObserver(mock_sender, user_repo))

    item_service = ItemService(item_repo, user_repo)
    found_item = item_service.report_item(
        ItemType.FOUND,
        bob.user_id,
        "Leather Wallet",
        "accessories",
        "Brown leather wallet",
        "Central Field",
        d1,
        secret_detail="student library card inside",
    )

    claim_service = ClaimService(claim_repo, item_repo, user_repo, event_bus=bus)
    claim = claim_service.submit_and_verify_claim(
        item_id=found_item.item_id,
        claimant_id=alice.user_id,
        proof_detail="Contains my student library card inside",
    )

    assert claim.status == ClaimStatus.APPROVED
    assert item_service.get_item(found_item.item_id).status == ItemStatus.CLAIMED
    mock_sender.send.assert_called_once()
    recipient, subject, _ = mock_sender.send.call_args[0]
    assert recipient == alice.email
    assert "APPROVED" in subject


def test_claim_chain_rejects_self_claim_at_step_2(repos, seeded_users, sample_dates):
    user_repo, item_repo, claim_repo = repos
    _, bob, _ = seeded_users
    d1, _ = sample_dates

    item_service = ItemService(item_repo, user_repo)
    found_item = item_service.report_item(
        ItemType.FOUND, bob.user_id, "Keychain", "other", "Bike keys", "Parking", d1, secret_detail="red tag"
    )

    claim_service = ClaimService(claim_repo, item_repo, user_repo)
    claim = claim_service.submit_and_verify_claim(found_item.item_id, bob.user_id, "red tag")

    assert claim.status == ClaimStatus.REJECTED
    assert "ClaimantNotReporterHandler" in claim.review_note


def test_claim_chain_rejects_wrong_secret_detail_at_step_3(repos, seeded_users, sample_dates):
    user_repo, item_repo, claim_repo = repos
    alice, bob, _ = seeded_users
    d1, _ = sample_dates

    item_service = ItemService(item_repo, user_repo)
    found_item = item_service.report_item(
        ItemType.FOUND, bob.user_id, "Earbuds", "electronics", "White earbuds", "Bus Stop", d1, secret_detail="serial 9981"
    )

    claim_service = ClaimService(claim_repo, item_repo, user_repo)
    claim = claim_service.submit_and_verify_claim(found_item.item_id, alice.user_id, "serial 1111")

    assert claim.status == ClaimStatus.REJECTED
    assert "SecretDetailHandler" in claim.review_note
    assert item_service.get_item(found_item.item_id).status == ItemStatus.OPEN
