from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.user_list import UserList


class UserListRepository:
    """Repository handling UserList database queries for watchlist and favorites."""

    def get_user_list(
        self, db: Session, profile_id: str, list_type: str = "watchlist"
    ) -> List[UserList]:
        """Query user list items for a profile and list_type, newest first."""
        return (
            db.query(UserList)
            .filter(UserList.profile_id == profile_id, UserList.list_type == list_type)
            .order_by(UserList.created_at.desc(), UserList.id.desc())
            .all()
        )

    def get_item(
        self, db: Session, profile_id: str, movie_id: int, list_type: str = "watchlist"
    ) -> Optional[UserList]:
        """Fetch a single user list item by profile_id, movie_id, and list_type."""
        return (
            db.query(UserList)
            .filter(
                UserList.profile_id == profile_id,
                UserList.movie_id == movie_id,
                UserList.list_type == list_type,
            )
            .first()
        )

    def add_item(
        self, db: Session, profile_id: str, movie_id: int, list_type: str = "watchlist"
    ) -> UserList:
        """Add an item to a profile's list if not present, otherwise return existing."""
        existing = self.get_item(db, profile_id, movie_id, list_type)
        if existing:
            return existing

        item = UserList(profile_id=profile_id, movie_id=movie_id, list_type=list_type)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def remove_item(
        self, db: Session, profile_id: str, movie_id: int, list_type: str = "watchlist"
    ) -> bool:
        """Remove an item from a profile's list. Returns True if removed, False otherwise."""
        item = self.get_item(db, profile_id, movie_id, list_type)
        if not item:
            return False

        db.delete(item)
        db.commit()
        return True

    def is_in_list(
        self, db: Session, profile_id: str, movie_id: int, list_type: str = "watchlist"
    ) -> bool:
        """Check whether a movie is in the specified list for a profile."""
        return (
            db.query(UserList.id)
            .filter(
                UserList.profile_id == profile_id,
                UserList.movie_id == movie_id,
                UserList.list_type == list_type,
            )
            .first()
            is not None
        )

    def count_items(
        self, db: Session, profile_id: str, list_type: str = "watchlist"
    ) -> int:
        """Count total items in a list for a profile."""
        return (
            db.query(UserList)
            .filter(UserList.profile_id == profile_id, UserList.list_type == list_type)
            .count()
        )


user_list_repository = UserListRepository()
