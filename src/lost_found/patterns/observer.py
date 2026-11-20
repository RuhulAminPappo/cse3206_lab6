from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Dict, List

from lost_found.domain.models import DomainEvent


class EventObserver(ABC):
    """Behavioral Pattern: Observer interface reacting to domain events."""

    @abstractmethod
    def update(self, event: DomainEvent) -> None:
        raise NotImplementedError


class EventBus:
    """Subject / Publisher broadcasting domain events to subscribed observers."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[EventObserver]] = defaultdict(list)

    def subscribe(self, event_type: str, observer: EventObserver) -> None:
        if observer not in self._subscribers[event_type]:
            self._subscribers[event_type].append(observer)

    def unsubscribe(self, event_type: str, observer: EventObserver) -> None:
        if observer in self._subscribers[event_type]:
            self._subscribers[event_type].remove(observer)

    def publish(self, event: DomainEvent) -> None:
        for observer in list(self._subscribers.get(event.event_type, [])):
            observer.update(event)
