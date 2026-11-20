import re
from unittest.mock import MagicMock
import pytest

from lost_found import cli as cli_mod
from lost_found.cli import interactive_cli, main, run_demo
from lost_found.domain.models import ItemType
from lost_found.modules.claims import ClaimService
from lost_found.modules.items import ItemService
from lost_found.modules.notifications import (
    ClaimStatusNotificationObserver,
    ConsoleNotificationSender,
    NotificationSender,
)
from lost_found.modules.users import UserService
from lost_found.patterns.observer import EventBus


def test_user_service_crud_and_validation(repos):
    user_repo, _, _ = repos
    service = UserService(user_repo)

    user = service.register_user("  Rafiq Hasan ", "rafiq@ruet.ac.bd", "cse")
    assert user.department == "CSE"
    assert service.get_user(user.user_id).name == "Rafiq Hasan"
    assert len(service.list_users()) == 1

    with pytest.raises(ValueError, match="Invalid email"):
        service.register_user("Bad Email", "not-an-email", "CSE")

    with pytest.raises(LookupError, match="User not found"):
        service.get_user("USR-MISSING")


def test_console_sender_and_rejected_claim_notification(repos, seeded_users, sample_dates):
    user_repo, item_repo, claim_repo = repos
    alice, bob, _ = seeded_users
    d1, _ = sample_dates

    console_sender = ConsoleNotificationSender(verbose=False)
    assert console_sender.send("test@ruet.ac.bd", "Subj", "Body") is True
    assert len(console_sender.sent_messages) == 1

    mock_sender = MagicMock(spec=NotificationSender)
    bus = EventBus()
    bus.subscribe("CLAIM_PROCESSED", ClaimStatusNotificationObserver(mock_sender, user_repo))

    found_item = ItemService(item_repo, user_repo).report_item(
        ItemType.FOUND,
        bob.user_id,
        "Backpack",
        "accessories",
        "Grey bag",
        "Library",
        d1,
        secret_detail="blue zip",
    )
    claim = ClaimService(claim_repo, item_repo, user_repo, event_bus=bus).submit_and_verify_claim(
        found_item.item_id,
        alice.user_id,
        "wrong clue",
    )
    assert claim.status.value == "REJECTED"
    mock_sender.send.assert_called_once()
    assert "REJECTED" in mock_sender.send.call_args[0][1]


def test_run_demo_executes_without_error(capsys):
    run_demo()
    captured = capsys.readouterr()
    assert "Total notifications sent: 3" in captured.out


def test_user_empty_name_and_item_listing(repos, seeded_users, sample_dates):
    user_repo, item_repo, _ = repos
    alice, _, _ = seeded_users
    d1, _ = sample_dates

    user_service = UserService(user_repo)
    with pytest.raises(ValueError, match="User name cannot be empty"):
        user_service.register_user("   ", "valid@ruet.ac.bd", "CSE")

    item_service = ItemService(item_repo, user_repo)
    item_service.report_item(ItemType.LOST, alice.user_id, "Pen", "other", "Blue pen", "Hall", d1)
    assert len(item_service.list_items()) == 1
    assert len(item_service.list_items(ItemType.LOST, only_open=True)) == 1


def test_interactive_cli_and_main_entry(monkeypatch, capsys, tmp_path):
    db_file = str(tmp_path / "cli_test.db")
    created_ids = []
    captured_chunks = []
    menu_choices = iter(["1", "2", "3", "9", "0"])

    def flush_stdout():
        chunk = capsys.readouterr().out
        if chunk:
            captured_chunks.append(chunk)
        return "".join(captured_chunks)

    def fake_input(prompt=""):
        if "Name:" in prompt:
            return "Sadia"
        if "Email:" in prompt:
            return "sadia@ruet.ac.bd"
        if "Department:" in prompt:
            return "CSE"
        if "Type (LOST/FOUND):" in prompt:
            return "LOST"
        if "Reporter User ID:" in prompt:
            all_out = flush_stdout()
            match = re.search(r"ID:\s*(USR-[A-Z0-9]+)", all_out)
            if match:
                created_ids.append(match.group(1))
            return created_ids[-1]
        if "Title:" in prompt:
            return "Notebook"
        if "Category:" in prompt:
            return "documents"
        if "Description:" in prompt:
            return "Lab notes"
        if "Location:" in prompt:
            return "CSE"
        if "Secret identifying detail:" in prompt:
            return "star sticker"
        return next(menu_choices)

    monkeypatch.setattr("builtins.input", fake_input)
    original_build = cli_mod.build_application
    monkeypatch.setattr(
        cli_mod,
        "build_application",
        lambda db_path="lost_found.db", verbose_notifications=True: original_build(
            db_file, verbose_notifications=False
        ),
    )

    interactive_cli()
    out = flush_stdout()
    assert len(created_ids) == 1
    assert "Registered Sadia" in out
    assert "Notebook" in out

    monkeypatch.setattr("sys.argv", ["lost_found.cli", "--demo"])
    main()
    demo_out = capsys.readouterr().out
    assert "=== RUET Campus Lost & Found - End-to-End Demo ===" in demo_out