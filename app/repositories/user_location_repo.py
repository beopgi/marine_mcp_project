"""Repository for reading the latest user location from the shared service DB."""

from __future__ import annotations

import re
from typing import Any

import asyncpg

from app.core.config import Settings
from app.schemas.location import LocationContext

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)?$")


class LocationDependencyError(RuntimeError):
    """Raised when location DB dependency is unavailable or misconfigured."""


class LocationNotFoundError(LookupError):
    """Raised when no latest location exists for the requested user."""


class UserLocationRepository:
    """Read latest user location rows saved by the Spring Boot backend.

    TODO(DB schema): this repository assumes a location log table containing both
    user identifiers and coordinates. Override the DB_LOCATION_* environment
    variables when the production schema differs (for example
    tracking.location_logs, user_locations, accuracyM vs accuracy_m, etc.).

    user_id is the numeric application user id. clerk_id is Clerk's external
    identity string. They are intentionally queried via separate columns so the
    two identifiers are not mixed accidentally.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def get_latest_location(
        self,
        *,
        user_id: int | None = None,
        clerk_id: str | None = None,
    ) -> LocationContext:
        """Return the newest location by recorded_at/created_at for user_id or clerk_id."""
        if not self.settings.db_enabled:
            raise LocationDependencyError("DB 기능이 비활성화되어 있습니다.")
        if not self.settings.database_url:
            raise LocationDependencyError("DATABASE_URL이 설정되어 있지 않습니다.")
        if user_id is None and not clerk_id:
            raise LocationNotFoundError("user_id 또는 clerk_id가 필요합니다.")

        query, value = self._build_latest_location_query(user_id=user_id, clerk_id=clerk_id)

        try:
            connection = await asyncpg.connect(dsn=self._asyncpg_dsn(self.settings.database_url))
        except Exception as exc:
            raise LocationDependencyError("DB 연결에 실패했습니다.") from exc

        try:
            row = await connection.fetchrow(query, value)
        except Exception as exc:
            raise LocationDependencyError("최신 위치 조회에 실패했습니다.") from exc
        finally:
            await connection.close()

        if row is None:
            raise LocationNotFoundError("사용자 최신 위치를 찾을 수 없습니다.")

        return self._row_to_context(dict(row))

    def _build_latest_location_query(
        self,
        *,
        user_id: int | None,
        clerk_id: str | None,
    ) -> tuple[str, int | str]:
        table = self._identifier(self.settings.db_location_table, "DB_LOCATION_TABLE")
        user_id_col = self._identifier(self.settings.db_location_user_id_column, "DB_LOCATION_USER_ID_COLUMN")
        clerk_id_col = self._identifier(self.settings.db_location_clerk_id_column, "DB_LOCATION_CLERK_ID_COLUMN")
        lat_col = self._identifier(self.settings.db_location_latitude_column, "DB_LOCATION_LATITUDE_COLUMN")
        lon_col = self._identifier(self.settings.db_location_longitude_column, "DB_LOCATION_LONGITUDE_COLUMN")
        region_col = self._identifier(self.settings.db_location_region_column, "DB_LOCATION_REGION_COLUMN")
        address_col = self._identifier(self.settings.db_location_address_column, "DB_LOCATION_ADDRESS_COLUMN")
        accuracy_col = self._identifier(self.settings.db_location_accuracy_column, "DB_LOCATION_ACCURACY_COLUMN")
        recorded_col = self._identifier(self.settings.db_location_recorded_at_column, "DB_LOCATION_RECORDED_AT_COLUMN")
        created_col = self._identifier(self.settings.db_location_created_at_column, "DB_LOCATION_CREATED_AT_COLUMN")

        where_col = user_id_col if user_id is not None else clerk_id_col
        value = user_id if user_id is not None else clerk_id

        query = f"""
            SELECT
                {user_id_col} AS user_id,
                {clerk_id_col} AS clerk_id,
                {lat_col} AS latitude,
                {lon_col} AS longitude,
                {region_col} AS region,
                {address_col} AS address,
                {accuracy_col} AS accuracy_m,
                COALESCE({recorded_col}, {created_col}) AS recorded_at
            FROM {table}
            WHERE {where_col} = $1
            ORDER BY COALESCE({recorded_col}, {created_col}) DESC NULLS LAST
            LIMIT 1
        """
        return query, value  # type: ignore[return-value]

    def _row_to_context(self, row: dict[str, Any]) -> LocationContext:
        return LocationContext(
            user_id=row.get("user_id"),
            clerk_id=row.get("clerk_id"),
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
            region=row.get("region"),
            address=row.get("address"),
            accuracy_m=float(row["accuracy_m"]) if row.get("accuracy_m") is not None else None,
            recorded_at=row.get("recorded_at"),
        )

    def _identifier(self, value: str, env_name: str) -> str:
        if not _IDENTIFIER_RE.match(value):
            raise LocationDependencyError(f"{env_name} 값이 안전한 SQL 식별자가 아닙니다.")
        return value

    def _asyncpg_dsn(self, database_url: str) -> str:
        if database_url.startswith("postgresql+asyncpg://"):
            return "postgresql://" + database_url.removeprefix("postgresql+asyncpg://")
        return database_url
