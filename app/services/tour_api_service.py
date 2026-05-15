from __future__ import annotations

from typing import Any

import requests

from app.core.config import Settings


class TourAPIError(RuntimeError):
    pass


class TourAPIService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = settings.tour_api_base_url.rstrip("/")
        self.accessible_base_url = settings.tour_api_accessible_base_url.rstrip("/")

    def area_based_list(
        self,
        area_code: str,
        sigungu_code: str | None = None,
        num_of_rows: int = 10,
        page_no: int = 1,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "areaCode": area_code,
            "numOfRows": num_of_rows,
            "pageNo": page_no,
            "arrange": "A",
        }
        if sigungu_code:
            params["sigunguCode"] = sigungu_code
        return self._request_items(
            "areaBasedList2",
            params,
        )

    def accessible_area_based_list(
        self,
        area_code: str,
        sigungu_code: str | None = None,
        num_of_rows: int = 10,
        page_no: int = 1,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "areaCode": area_code,
            "numOfRows": num_of_rows,
            "pageNo": page_no,
            "arrange": "A",
        }
        if sigungu_code:
            params["sigunguCode"] = sigungu_code
        return self._request_items(
            "areaBasedList2",
            params,
            base_url=self.accessible_base_url,
            service_key=self.settings.tour_api_accessible_service_key,
        )

    def detail_common(self, content_id: str) -> dict[str, Any]:
        items = self._request_items(
            "detailCommon2",
            {"contentId": content_id},
        )
        return items[0] if items else {}

    def detail_with_tour(self, content_id: str) -> dict[str, Any]:
        items = self._request_items(
            "detailWithTour2",
            {"contentId": content_id},
            base_url=self.accessible_base_url,
            service_key=self.settings.tour_api_accessible_service_key,
        )
        return items[0] if items else {}

    def area_codes(self, area_code: str | None = None, accessible: bool = True) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"numOfRows": 100, "pageNo": 1}
        if area_code:
            params["areaCode"] = area_code
        return self._request_items(
            "areaCode2",
            params,
            base_url=self.accessible_base_url if accessible else None,
            service_key=self.settings.tour_api_accessible_service_key if accessible else None,
        )

    def _request_items(
        self,
        operation: str,
        params: dict[str, Any],
        base_url: str | None = None,
        service_key: str | None = None,
    ) -> list[dict[str, Any]]:
        effective_service_key = service_key or self.settings.tour_api_service_key
        if not effective_service_key:
            raise TourAPIError("TOUR_API_SERVICE_KEY가 설정되어 있지 않습니다.")

        request_params = {
            "serviceKey": effective_service_key,
            "MobileOS": self.settings.tour_api_mobile_os,
            "MobileApp": self.settings.tour_api_mobile_app,
            "_type": "json",
            **params,
        }
        try:
            response = requests.get(
                f"{base_url or self.base_url}/{operation}",
                params=request_params,
                timeout=self.settings.tour_api_timeout,
            )
            response.raise_for_status()
        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else "unknown"
            raise TourAPIError(f"TourAPI HTTP 오류: {status_code}") from exc
        except requests.RequestException as exc:
            raise TourAPIError(f"TourAPI 요청 실패: {exc.__class__.__name__}") from exc
        payload = response.json()
        return self._extract_items(payload)

    def _extract_items(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        if "resultCode" in payload and str(payload.get("resultCode")) not in {"0000", "0"}:
            message = payload.get("resultMsg") or "TourAPI 응답 오류"
            raise TourAPIError(f"{payload.get('resultCode')}: {message}")

        header = payload.get("response", {}).get("header", {})
        result_code = str(header.get("resultCode", "0000"))
        if result_code not in {"0000", "0"}:
            message = header.get("resultMsg") or "TourAPI 응답 오류"
            raise TourAPIError(f"{result_code}: {message}")

        items = payload.get("response", {}).get("body", {}).get("items", {})
        if not isinstance(items, dict):
            return []
        raw_items = items.get("item", [])
        if isinstance(raw_items, dict):
            return [raw_items]
        if isinstance(raw_items, list):
            return [item for item in raw_items if isinstance(item, dict)]
        return []
