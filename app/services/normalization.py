"""Normalization service for mapping raw adapter payloads into canonical schema."""

import hashlib
import html
import re
from typing import Any
from urllib.parse import quote

from app.schemas.content import MarineContentItem
from app.schemas.query import StructuredQuery


class NormalizationService:
    """Convert Naver API payload to MarineContentItem schema."""

    def normalize_items(
        self,
        raw_items: list[dict[str, Any]],
        query: StructuredQuery,
    ) -> list[MarineContentItem]:
        normalized: list[MarineContentItem] = []

        for raw in raw_items:
            try:
                item = self._normalize_naver_item(raw, query)
                normalized.append(item)
            except Exception as e:
                print(f"[Normalization] skip item: {e}")
                continue

        return normalized

    def _normalize_naver_item(
        self,
        raw: dict[str, Any],
        query: StructuredQuery,
    ) -> MarineContentItem:
        title = self._clean_html(raw.get("title", ""))
        category = self._clean_html(raw.get("category", ""))
        telephone = self._clean_html(raw.get("telephone", ""))
        address = self._clean_html(raw.get("address", ""))
        road_address = self._clean_html(raw.get("roadAddress", ""))
        mapx = str(raw.get("mapx") or "").strip()
        mapy = str(raw.get("mapy") or "").strip()
        raw_link = str(raw.get("link") or "").strip()

        location = (
            query.location
            or self._extract_location(road_address)
            or self._extract_location(address)
            or self._extract_location(title)
            or "미지정"
        )

        activity = query.activity or self._extract_activity(title, category) or "미지정"

        description = self._build_description(
            title=title,
            category=category,
            road_address=road_address,
            address=address,
            telephone=telephone,
            mapx=mapx,
            mapy=mapy,
        )

        return MarineContentItem(
            id=self._resolve_id(raw, title, road_address, address),
            service_name=title or "제목 없음",
            location=location,
            activity=activity,
            category=category or None,
            telephone=telephone or None,
            address=address or None,
            road_address=road_address or None,
            mapx=mapx or None,
            mapy=mapy or None,
            transport_info=road_address or address or query.transport,
            source="naver_local",
            source_url=raw_link or None,
            map_search_url=self._build_map_search_url(title, road_address, address),
            description=description or None,
        )

    def _clean_html(self, text: str) -> str:
        cleaned = html.unescape(text or "")
        cleaned = re.sub(r"<.*?>", "", cleaned)
        return cleaned.strip()

    def _resolve_id(
        self,
        raw: dict[str, Any],
        title: str,
        road_address: str,
        address: str,
    ) -> str:
        raw_link = str(raw.get("link") or "").strip()
        mapx = str(raw.get("mapx") or "").strip()
        mapy = str(raw.get("mapy") or "").strip()

        seed = raw_link or f"{title}|{road_address}|{address}|{mapx}|{mapy}"
        return hashlib.md5(seed.encode("utf-8")).hexdigest()

    def _build_map_search_url(
        self,
        title: str,
        road_address: str,
        address: str,
    ) -> str:
        keyword = title or road_address or address
        if keyword:
            return f"https://map.naver.com/v5/search/{quote(keyword)}"
        return "https://map.naver.com"

    def _extract_location(self, text: str) -> str | None:
        keywords = ["부산", "제주", "울산", "강릉", "여수", "속초", "포항", "통영"]
        for kw in keywords:
            if kw in text:
                return kw
        return None

    def _extract_activity(self, title: str, category: str) -> str | None:
        base_text = f"{title} {category}"

        mapping = {
            "낚시": ["낚시", "선상낚시", "배낚시", "낚시터"],
            "요트": ["요트", "요트투어", "마리나"],
            "보트": ["보트", "보트투어", "유람선"],
            "서핑": ["서핑", "서프", "서핑샵"],
            "카약": ["카약"],
        }

        for activity, keywords in mapping.items():
            for kw in keywords:
                if kw in base_text:
                    return activity
        return None

    def _build_description(
        self,
        title: str,
        category: str,
        road_address: str,
        address: str,
        telephone: str,
        mapx: str,
        mapy: str,
    ) -> str:
        parts = []

        if category:
            parts.append(f"카테고리: {category}")

        if road_address:
            parts.append(f"도로명주소: {road_address}")
        elif address:
            parts.append(f"주소: {address}")

        if telephone:
            parts.append(f"전화번호: {telephone}")

        if mapx and mapy:
            parts.append(f"좌표: mapx={mapx}, mapy={mapy}")

        if not parts and title:
            parts.append(title)

        return " | ".join(parts)