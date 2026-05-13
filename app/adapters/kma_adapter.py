"""Korea Meteorological Administration API adapter."""

from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.core.config import Settings
from app.schemas.weather import WeatherContext

logger = logging.getLogger(__name__)
KST = timezone(timedelta(hours=9))


class KMAAdapter:
    """Fetch and normalize KMA ultra short-term weather data."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def fetch_current_weather(self, latitude: float, longitude: float) -> WeatherContext | None:
        """Return normalized current weather, or None when KMA is disabled/unavailable."""
        if not self.settings.kma_enabled or not self.settings.kma_api_key:
            return None

        nx, ny = self.lat_lon_to_grid(latitude=latitude, longitude=longitude)
        now = datetime.now(KST)
        base_date, base_time = self._ultra_srt_ncst_base(now)
        url = f"{self.settings.kma_base_url.rstrip('/')}/getUltraSrtNcst"
        params = {
            "serviceKey": self.settings.kma_api_key,
            "pageNo": 1,
            "numOfRows": 100,
            "dataType": "JSON",
            "base_date": base_date,
            "base_time": base_time,
            "nx": nx,
            "ny": ny,
        }

        try:
            async with httpx.AsyncClient(timeout=self.settings.kma_timeout_seconds) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                payload = response.json()
        except Exception as exc:
            logger.warning("KMA current weather fetch failed: %s", exc.__class__.__name__)
            return None

        try:
            weather = self._parse_ultra_srt_ncst(payload, observed_at=now)
        except Exception as exc:
            logger.warning("KMA current weather parse failed: %s", exc.__class__.__name__)
            return None

        if weather is not None:
            weather.sky = await self._fetch_sky(nx=nx, ny=ny, now=now)
        return weather

    async def _fetch_sky(self, *, nx: int, ny: int, now: datetime) -> str | None:
        base_date, base_time = self._ultra_srt_fcst_base(now)
        url = f"{self.settings.kma_base_url.rstrip('/')}/getUltraSrtFcst"
        params = {
            "serviceKey": self.settings.kma_api_key,
            "pageNo": 1,
            "numOfRows": 100,
            "dataType": "JSON",
            "base_date": base_date,
            "base_time": base_time,
            "nx": nx,
            "ny": ny,
        }
        try:
            async with httpx.AsyncClient(timeout=self.settings.kma_timeout_seconds) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                payload = response.json()
            items = payload.get("response", {}).get("body", {}).get("items", {}).get("item", [])
            for item in items if isinstance(items, list) else []:
                if item.get("category") == "SKY":
                    return self._sky(item.get("fcstValue"))
        except Exception as exc:
            logger.warning("KMA sky forecast fetch failed: %s", exc.__class__.__name__)
        return None

    def _parse_ultra_srt_ncst(self, payload: dict[str, Any], observed_at: datetime) -> WeatherContext | None:
        header = payload.get("response", {}).get("header", {})
        if header.get("resultCode") not in (None, "00"):
            logger.warning("KMA returned non-success resultCode=%s", header.get("resultCode"))
            return None

        items = payload.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        if not isinstance(items, list):
            return None

        values = {item.get("category"): item.get("obsrValue") for item in items if isinstance(item, dict)}
        if not values:
            return None

        return WeatherContext(
            temperature=self._float_or_none(values.get("T1H")),
            precipitation_type=self._precipitation_type(values.get("PTY")),
            precipitation_amount=self._precipitation_amount(values.get("RN1")),
            humidity=self._int_or_none(values.get("REH")),
            wind_speed=self._float_or_none(values.get("WSD")),
            wind_direction=self._wind_direction(values.get("VEC")),
            sky=None,
            observed_at=observed_at,
        )

    def _ultra_srt_ncst_base(self, now: datetime) -> tuple[str, str]:
        # Ultra short-term observations are published around HH:40, so ask the
        # previous hour when the current hour's observations may not be ready.
        base = now - timedelta(hours=1) if now.minute < 40 else now
        return base.strftime("%Y%m%d"), base.strftime("%H00")

    def _ultra_srt_fcst_base(self, now: datetime) -> tuple[str, str]:
        # Ultra short-term forecasts are published every 30 minutes.
        base = now - timedelta(hours=1) if now.minute < 45 else now
        return base.strftime("%Y%m%d"), base.strftime("%H30")

    def lat_lon_to_grid(self, latitude: float, longitude: float) -> tuple[int, int]:
        """Convert WGS84 lat/lon to KMA DFS grid coordinates."""
        re = 6371.00877
        grid = 5.0
        slat1 = 30.0
        slat2 = 60.0
        olon = 126.0
        olat = 38.0
        xo = 43
        yo = 136

        degrad = math.pi / 180.0
        re_grid = re / grid
        slat1_rad = slat1 * degrad
        slat2_rad = slat2 * degrad
        olon_rad = olon * degrad
        olat_rad = olat * degrad

        sn = math.tan(math.pi * 0.25 + slat2_rad * 0.5) / math.tan(math.pi * 0.25 + slat1_rad * 0.5)
        sn = math.log(math.cos(slat1_rad) / math.cos(slat2_rad)) / math.log(sn)
        sf = math.tan(math.pi * 0.25 + slat1_rad * 0.5)
        sf = (sf ** sn) * math.cos(slat1_rad) / sn
        ro = math.tan(math.pi * 0.25 + olat_rad * 0.5)
        ro = re_grid * sf / (ro ** sn)
        ra = math.tan(math.pi * 0.25 + latitude * degrad * 0.5)
        ra = re_grid * sf / (ra ** sn)
        theta = longitude * degrad - olon_rad
        if theta > math.pi:
            theta -= 2.0 * math.pi
        if theta < -math.pi:
            theta += 2.0 * math.pi
        theta *= sn

        x = int(ra * math.sin(theta) + xo + 0.5)
        y = int(ro - ra * math.cos(theta) + yo + 0.5)
        return x, y

    def _sky(self, code: Any) -> str | None:
        mapping = {"1": "clear", "3": "cloudy", "4": "overcast"}
        return mapping.get(str(code)) if code is not None else None

    def _precipitation_type(self, code: Any) -> str | None:
        mapping = {
            "0": "none",
            "1": "rain",
            "2": "rain_snow",
            "3": "snow",
            "5": "drizzle",
            "6": "drizzle_snow",
            "7": "snow_flurry",
        }
        return mapping.get(str(code)) if code is not None else None

    def _precipitation_amount(self, value: Any) -> float | None:
        if value is None:
            return None
        text = str(value).strip()
        if text in {"강수없음", "", "0", "0.0"}:
            return 0.0
        text = text.replace("mm", "").replace("미만", "").strip()
        if text.startswith("1.0"):
            return 1.0
        try:
            return float(text)
        except ValueError:
            return None

    def _wind_direction(self, value: Any) -> str | None:
        degrees = self._float_or_none(value)
        if degrees is None:
            return None
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        idx = int((degrees + 22.5) // 45) % 8
        return directions[idx]

    def _float_or_none(self, value: Any) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _int_or_none(self, value: Any) -> int | None:
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None
