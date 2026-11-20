from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from lost_found.domain.models import Claim, Item, ItemStatus, ItemType, User


class UserRepository(ABC):
    @abstractmethod
    def save(self, user: User) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, user_id: str) -> Optional[User]:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> List[User]:
        raise NotImplementedError


class ItemRepository(ABC):
    @abstractmethod
    def save(self, item: Item) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, item_id: str) -> Optional[Item]:
        raise NotImplementedError

    @abstractmethod
    def list_by_type(self, item_type: ItemType, only_open: bool = True) -> List[Item]:
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> List[Item]:
        raise NotImplementedError

    @abstractmethod
    def update_status(self, item_id: str, status: ItemStatus) -> None:
        raise NotImplementedError


class ClaimRepository(ABC):
    @abstractmethod
    def save(self, claim: Claim) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, claim_id: str) -> Optional[Claim]:
        raise NotImplementedError

    @abstractmethod
    def list_by_item(self, item_id: str) -> List[Claim]:
        raise NotImplementedError
