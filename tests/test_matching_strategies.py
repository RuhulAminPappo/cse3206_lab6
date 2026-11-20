from datetime import date

from lost_found.patterns.factory import ItemFactory
from lost_found.patterns.strategy import (
    CategoryMatchStrategy,
    CompositeWeightedStrategy,
    DateProximityMatchStrategy,
    KeywordMatchStrategy,
)


def test_keyword_match_strategy_scores_shared_tokens():
    lost = ItemFactory.create_lost_item(
        "USR-1", "Black Dell Laptop Charger", "electronics", "65W USB-C charger", "CSE Lab", date(2026, 11, 10)
    )
    found = ItemFactory.create_found_item(
        "USR-2", "Dell USB-C Laptop Charger", "electronics", "Black 65W adapter", "CSE Lab", date(2026, 11, 11)
    )

    score, reason = KeywordMatchStrategy().compute_score(lost, found)
    assert score > 0.5
    assert "dell" in reason


def test_category_match_strategy_binary_score():
    lost = ItemFactory.create_lost_item("USR-1", "Watch", "accessories", "Silver watch", "Hall", date(2026, 11, 10))
    same_cat = ItemFactory.create_found_item("USR-2", "Wristwatch", "ACCESSORIES", "Found watch", "Hall", date(2026, 11, 10))
    diff_cat = ItemFactory.create_found_item("USR-2", "Wallet", "documents", "Brown wallet", "Hall", date(2026, 11, 10))

    assert CategoryMatchStrategy().compute_score(lost, same_cat)[0] == 1.0
    assert CategoryMatchStrategy().compute_score(lost, diff_cat)[0] == 0.0


def test_date_proximity_strategy_decays_with_day_gap():
    lost = ItemFactory.create_lost_item("USR-1", "Umbrella", "accessories", "Blue", "Gate", date(2026, 11, 1))
    same_day = ItemFactory.create_found_item("USR-2", "Umbrella", "accessories", "Blue", "Gate", date(2026, 11, 1))
    far_day = ItemFactory.create_found_item("USR-2", "Umbrella", "accessories", "Blue", "Gate", date(2026, 11, 25))

    strategy = DateProximityMatchStrategy(max_days_window=10)
    assert strategy.compute_score(lost, same_day)[0] == 1.0
    assert strategy.compute_score(lost, far_day)[0] == 0.0


def test_composite_weighted_strategy_combines_scores():
    lost = ItemFactory.create_lost_item(
        "USR-1", "Casio Scientific Calculator", "electronics", "fx-991EX", "Auditorium", date(2026, 11, 12)
    )
    found = ItemFactory.create_found_item(
        "USR-2", "Casio fx-991EX Calculator", "electronics", "Scientific calculator", "Auditorium", date(2026, 11, 12)
    )

    composite = CompositeWeightedStrategy(
        [
            (KeywordMatchStrategy(), 0.5),
            (CategoryMatchStrategy(), 0.3),
            (DateProximityMatchStrategy(10), 0.2),
        ]
    )
    score, reason = composite.compute_score(lost, found)
    assert score >= 0.85
    assert "CategoryMatch=1.00" in reason
