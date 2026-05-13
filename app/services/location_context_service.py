"""Service layer for resolving a user's latest persisted location."""

from app.repositories.user_location_repo import UserLocationRepository
from app.schemas.location import LocationContext


class LocationContextService:
    """Resolve recommendation location context from the shared DB."""

    def __init__(self, repository: UserLocationRepository) -> None:
        self.repository = repository

    async def get_latest_location(
        self,
        *,
        user_id: int | None = None,
        clerk_id: str | None = None,
    ) -> LocationContext:
        return await self.repository.get_latest_location(user_id=user_id, clerk_id=clerk_id)
