"""Repository abstraction for user preference tag scores."""

from __future__ import annotations


class UserPreferenceRepository:
    """Temporary mock repository for user preference tag scores."""

    def get_user_tag_scores(self, user_id: int) -> dict[str, int]:
        """Return tag score map for a user id."""
        if user_id == 1:
            return {
                '요트': 5,
                '야경': 3,
                '프라이빗': 2,
                '크루즈': 1,
            }

        return {}
