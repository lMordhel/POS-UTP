"""HTTP client Sales → Stock (ADR-003).

Single coupling point between services. Retries ONLY transient network
failures (ConnectError/Timeout); never 404/409/422 (skill
python-testing-patterns retry behavior).
"""

from dataclasses import dataclass
from decimal import Decimal

import httpx

from app.core.config import get_settings


class StockProductNotFoundError(LookupError):
    pass


class StockInsufficientError(ValueError):
    pass


class StockUnavailableError(ConnectionError):
    pass


@dataclass
class StockProduct:
    id: int
    codigo: str
    nombre: str
    precio: Decimal
    activo: bool
    stock: int


class StockClient:
    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
        max_retries: int = 2,
    ):
        settings = get_settings()
        self.base_url = (base_url or settings.STOCK_SERVICE_URL).rstrip("/")
        self.timeout = timeout or settings.STOCK_TIMEOUT_SECONDS
        self.max_retries = max_retries

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """GET/POST/PATCH with retry on transient network errors only."""
        last_exc: Exception | None = None
        for _ in range(self.max_retries):
            try:
                return httpx.request(method, f"{self.base_url}{path}", timeout=self.timeout, **kwargs)
            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                last_exc = exc
        raise StockUnavailableError(f"stock no disponible: {last_exc}")

    def get_product(self, product_id: int) -> StockProduct:
        try:
            resp = self._request("GET", f"/api/v1/products/{product_id}")
        except StockUnavailableError:
            raise
        except httpx.HTTPError as exc:
            raise StockUnavailableError(f"stock no disponible: {exc}")
        if resp.status_code == 404:
            raise StockProductNotFoundError(f"producto inexistente: {product_id}")
        if resp.status_code >= 500:
            raise StockUnavailableError(f"stock falló: HTTP {resp.status_code}")
        resp.raise_for_status()
        body = resp.json()
        return StockProduct(
            id=body["id"],
            codigo=body["codigo"],
            nombre=body["nombre"],
            precio=Decimal(str(body["precio"])),
            activo=body["activo"],
            stock=body["stock"],
        )

    def get_stock(self, product_id: int) -> int:
        try:
            resp = self._request("GET", f"/api/v1/products/{product_id}/stock")
        except httpx.HTTPError as exc:
            raise StockUnavailableError(f"stock no disponible: {exc}")
        if resp.status_code == 404:
            raise StockProductNotFoundError(f"producto inexistente: {product_id}")
        if resp.status_code >= 500:
            raise StockUnavailableError(f"stock falló: HTTP {resp.status_code}")
        resp.raise_for_status()
        return int(resp.json()["cantidad"])

    def adjust_stock(self, product_id: int, delta: int, motivo: str) -> int:
        try:
            resp = self._request(
                "PATCH",
                f"/api/v1/products/{product_id}/stock",
                json={"delta": delta, "motivo": motivo},
            )
        except httpx.HTTPError as exc:
            raise StockUnavailableError(f"stock no disponible: {exc}")
        if resp.status_code == 404:
            raise StockProductNotFoundError(f"producto inexistente: {product_id}")
        if resp.status_code == 409:
            raise StockInsufficientError(resp.json().get("detail", "stock insuficiente"))
        if resp.status_code >= 500:
            raise StockUnavailableError(f"stock falló: HTTP {resp.status_code}")
        resp.raise_for_status()
        return int(resp.json()["cantidad"])


stock_client = StockClient()
