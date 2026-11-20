from __future__ import annotations

from abc import ABC, abstractmethod
import re
from typing import List, Tuple

from lost_found.domain.models import Item


def _tokenize(text: str) -> set[str]:
    stop_words = {"a", "an", "the", "in", "on", "at", "with", "of", "and", "or", "to", "my"}
    tokens = set(re.findall(r"[a-z0-9]+", text.lower()))
    return {t for t in tokens if t not in stop_words and len(t) > 1}


class MatchingStrategy(ABC):
    """Behavioral Pattern: Strategy interface for interchangeable item matching rules."""

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def compute_score(self, lost_item: Item, found_item: Item) -> Tuple[float, str]:
        """Returns (score in [0.0, 1.0], human-readable explanation)."""
        raise NotImplementedError


class KeywordMatchStrategy(MatchingStrategy):
    @property
    def name(self) -> str:
        return "KeywordMatch"

    def compute_score(self, lost_item: Item, found_item: Item) -> Tuple[float, str]:
        lost_tokens = _tokenize(f"{lost_item.title} {lost_item.description} {lost_item.location}")
        found_tokens = _tokenize(f"{found_item.title} {found_item.description} {found_item.location}")
        if not lost_tokens or not found_tokens:
            return 0.0, "No comparable keywords"
        overlap = lost_tokens & found_tokens
        union = lost_tokens | found_tokens
        score = round(len(overlap) / len(union), 4)
        reason = f"Shared keywords: {', '.join(sorted(overlap))}" if overlap else "No shared keywords"
        return score, reason


class CategoryMatchStrategy(MatchingStrategy):
    @property
    def name(self) -> str:
        return "CategoryMatch"

    def compute_score(self, lost_item: Item, found_item: Item) -> Tuple[float, str]:
        matched = lost_item.category.strip().lower() == found_item.category.strip().lower()
        return (1.0, f"Exact category match ({lost_item.category})") if matched else (0.0, "Different categories")


class DateProximityMatchStrategy(MatchingStrategy):
    def __init__(self, max_days_window: int = 14) -> None:
        if max_days_window <= 0:
            raise ValueError("max_days_window must be positive.")
        self.max_days_window = max_days_window

    @property
    def name(self) -> str:
        return "DateProximityMatch"

    def compute_score(self, lost_item: Item, found_item: Item) -> Tuple[float, str]:
        day_diff = abs((found_item.event_date - lost_item.event_date).days)
        if day_diff > self.max_days_window:
            return 0.0, f"Date gap ({day_diff}d) exceeds {self.max_days_window}d window"
        score = round(max(0.0, 1.0 - (day_diff / self.max_days_window)), 4)
        return score, f"Occurred {day_diff} day(s) apart"


class CompositeWeightedStrategy(MatchingStrategy):
    """Combines multiple strategies using normalized weights."""

    def __init__(self, weighted_strategies: List[Tuple[MatchingStrategy, float]]) -> None:
        if not weighted_strategies:
            raise ValueError("At least one strategy is required.")
        total_weight = sum(weight for _, weight in weighted_strategies)
        if total_weight <= 0:
            raise ValueError("Total weight must be positive.")
        self._strategies = [(s, w / total_weight) for s, w in weighted_strategies]

    @property
    def name(self) -> str:
        return "CompositeWeightedMatch"

    def compute_score(self, lost_item: Item, found_item: Item) -> Tuple[float, str]:
        total_score = 0.0
        reasons: List[str] = []
        for strategy, norm_weight in self._strategies:
            sub_score, reason = strategy.compute_score(lost_item, found_item)
            total_score += sub_score * norm_weight
            reasons.append(f"{strategy.name}={sub_score:.2f} ({reason})")
        return round(total_score, 4), "; ".join(reasons)
