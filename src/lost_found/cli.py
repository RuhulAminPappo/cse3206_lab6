from __future__ import annotations

import argparse
from datetime import date, timedelta

from lost_found.domain.models import ItemType
from lost_found.modules.claims import ClaimService
from lost_found.modules.items import ItemService
from lost_found.modules.matching import MatchingService
from lost_found.modules.notifications import (
    ClaimStatusNotificationObserver,
    ConsoleNotificationSender,
    MatchNotificationObserver,
)
from lost_found.modules.users import UserService
from lost_found.patterns.observer import EventBus
from lost_found.patterns.strategy import (
    CategoryMatchStrategy,
    CompositeWeightedStrategy,
    DateProximityMatchStrategy,
    KeywordMatchStrategy,
)
from lost_found.persistence.sqlite_repo import (
    SQLiteClaimRepository,
    SQLiteDatabase,
    SQLiteItemRepository,
    SQLiteUserRepository,
)


def build_application(db_path: str = "lost_found.db", verbose_notifications: bool = True):
    db = SQLiteDatabase(db_path)
    user_repo = SQLiteUserRepository(db)
    item_repo = SQLiteItemRepository(db)
    claim_repo = SQLiteClaimRepository(db)

    event_bus = EventBus()
    sender = ConsoleNotificationSender(verbose=verbose_notifications)
    event_bus.subscribe("MATCH_FOUND", MatchNotificationObserver(sender, user_repo))
    event_bus.subscribe("CLAIM_PROCESSED", ClaimStatusNotificationObserver(sender, user_repo))

    strategy = CompositeWeightedStrategy(
        [
            (KeywordMatchStrategy(), 0.50),
            (CategoryMatchStrategy(), 0.30),
            (DateProximityMatchStrategy(max_days_window=14), 0.20),
        ]
    )

    user_service = UserService(user_repo)
    item_service = ItemService(item_repo, user_repo)
    matching_service = MatchingService(item_repo, strategy=strategy, event_bus=event_bus, min_threshold=0.35)
    claim_service = ClaimService(claim_repo, item_repo, user_repo, event_bus=event_bus)

    return db, user_service, item_service, matching_service, claim_service, sender


def run_demo() -> None:
    print("=== RUET Campus Lost & Found - End-to-End Demo ===")
    db, users, items, matching, claims, sender = build_application(":memory:", verbose_notifications=True)
    try:
        alice = users.register_user("Ayesha Rahman", "ayesha.22@student.ruet.ac.bd", "CSE")
        bob = users.register_user("Tanvir Ahmed", "tanvir.22@student.ruet.ac.bd", "EEE")

        lost_calc = items.report_item(
            item_type=ItemType.LOST,
            reporter_id=alice.user_id,
            title="Casio fx-991EX Scientific Calculator",
            category="electronics",
            description="Black scientific calculator lost near CSE Building Room 302",
            location="CSE Building",
            event_date=date.today() - timedelta(days=1),
            secret_detail="sticker on back cover: AR-2203",
        )
        print(f"[1] Posted LOST item: {lost_calc.item_id} - {lost_calc.title}")

        found_calc = items.report_item(
            item_type=ItemType.FOUND,
            reporter_id=bob.user_id,
            title="Black Casio Calculator fx-991EX",
            category="electronics",
            description="Found scientific calculator on desk in CSE Building",
            location="CSE Building",
            event_date=date.today(),
            secret_detail="sticker on back cover: AR-2203",
        )
        print(f"[2] Posted FOUND item: {found_calc.item_id} - {found_calc.title}")

        matches = matching.find_matches_for_item(lost_calc.item_id)
        print(f"[3] Matches found: {len(matches)}")
        for m in matches:
            print(f"    -> Lost={m.lost_item_id}, Found={m.found_item_id}, Score={m.score:.2f} ({m.strategy_name})")

        rejected = claims.submit_and_verify_claim(
            item_id=found_calc.item_id,
            claimant_id=alice.user_id,
            proof_detail="It is black",
        )
        print(f"[4] First claim attempt: {rejected.status.value} | {rejected.review_note}")

        approved = claims.submit_and_verify_claim(
            item_id=found_calc.item_id,
            claimant_id=alice.user_id,
            proof_detail="Has sticker on back cover: AR-2203",
        )
        print(f"[5] Second claim attempt: {approved.status.value} | {approved.review_note}")
        print(f"[6] Total notifications sent: {len(sender.sent_messages)}")
    finally:
        db.close()


def interactive_cli() -> None:
    db, users, items, matching, claims, _ = build_application("lost_found.db", verbose_notifications=True)
    try:
        while True:
            print("\n--- Campus Lost & Found Menu ---")
            print("1. Register User")
            print("2. Report Lost/Found Item")
            print("3. List All Items")
            print("4. Run Smart Matching for an Item")
            print("5. Submit & Verify Claim")
            print("0. Exit")
            choice = input("Select option: ").strip()

            if choice == "1":
                name = input("Name: ")
                email = input("Email: ")
                dept = input("Department: ")
                u = users.register_user(name, email, dept)
                print(f"Registered {u.name} with ID: {u.user_id}")
            elif choice == "2":
                kind = input("Type (LOST/FOUND): ")
                rep_id = input("Reporter User ID: ")
                title = input("Title: ")
                cat = input("Category: ")
                desc = input("Description: ")
                loc = input("Location: ")
                secret = input("Secret identifying detail: ")
                it = items.report_item(kind, rep_id, title, cat, desc, loc, date.today(), secret)
                print(f"Created item {it.item_id} [{it.status.value}]")
            elif choice == "3":
                for it in items.list_items():
                    print(f"{it.item_id} | {it.item_type.value} | {it.title} | {it.status.value}")
            elif choice == "4":
                iid = input("Item ID to match: ").strip()
                results = matching.find_matches_for_item(iid)
                if not results:
                    print("No matches above threshold.")
                for m in results:
                    print(f"Match: Lost={m.lost_item_id} <-> Found={m.found_item_id} | Score={m.score:.2f}")
            elif choice == "5":
                iid = input("Found Item ID to claim: ").strip()
                cid = input("Claimant User ID: ").strip()
                proof = input("Proof detail: ")
                clm = claims.submit_and_verify_claim(iid, cid, proof)
                print(f"Claim {clm.claim_id}: {clm.status.value} ({clm.review_note})")
            elif choice == "0":
                break
            else:
                print("Invalid option.")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Campus Lost & Found CLI")
    parser.add_argument("--demo", action="store_true", help="Run non-interactive end-to-end demo")
    args = parser.parse_args()
    if args.demo:
        run_demo()
    else:
        interactive_cli()


if __name__ == "__main__":
    main()
