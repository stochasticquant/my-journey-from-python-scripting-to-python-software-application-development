# src/inventory_system/repositories/base.py
from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar

from sqlalchemy.orm import Session

T = TypeVar("T")


class BaseRepository(Generic[T], ABC):
    def __init__(self, session: Session) -> None:
        self.session = session

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[T]:
        """Get entity by primary key."""
        pass

    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination."""
        pass

    @abstractmethod
    def create(self, entity: T) -> T:
        """Create a new entity."""
        pass

    @abstractmethod
    def update(self, id: int, entity_data: dict) -> Optional[T]:
        """Update an entity by ID."""
        pass

    @abstractmethod
    def delete(self, id: int) -> bool:
        """Delete an entity by ID."""
        pass
