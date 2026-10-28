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
        """GET/POST/PATCH with retry on transient network errors only.

        Incluye la credencial de servicio (ADR-008 addendum): Stock exige JWT
        también en llamadas internas; el rol del usuario final no se propaga.
        """
        from app.core import security as security_module

        headers = dict(kwargs.pop("headers", {}) or {})
        headers.setdefault(
            "Authorization", f"Bearer {security_module.create_service_token()}"
        )
        last_exc: Exception | None = None
        for _ in range(self.max_retries):
            try:
                return httpx.request(method, f"{self.base_url}{path}", timeout=self.timeout, headers=headers, **kwargs)
            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                last_exc = exc
        raise StockUnavailableError(f"stock no disponible: {last_exc}")

    def _unavailable(self, resp: httpx.Response, accion: str) -> StockUnavailableError:
        """Status que no sabemos interpretar = fallo de Stock (502), nunca 500 crudo."""
        return StockUnavailableError(
            f"stock no disponible en {accion}: HTTP {resp.status_code}"
        )

    def batch_get_products(self, ids: list[int]) -> list[StockProduct]:
        """SPEC-STOCK-006: una lectura por lote (precios + stock)."""
        try:
            resp = self._request("POST", "/api/v1/products/batch", json={"ids": ids})
        except httpx.HTTPError as exc:
            raise StockUnavailableError(f"stock no disponible: {exc}")
        if not resp.is_success:
            raise self._unavailable(resp, "lectura por lote")
        return [
            StockProduct(
                id=item["id"],
                codigo=item["codigo"],
                nombre=item["nombre"],
                precio=Decimal(str(item["precio"])),
                activo=item["activo"],
                stock=item["stock"],
            )
            for item in resp.json()
        ]

    def adjust_stock(self, product_id: int, delta: int, motivo: str, idem_key: str | None = None) -> int:
        try:
            headers = {"Idempotency-Key": idem_key} if idem_key else None
            resp = self._request(
                "PATCH",
                f"/api/v1/products/{product_id}/stock",
                json={"delta": delta, "motivo": motivo},
                headers=headers,
            )
        except httpx.HTTPError as exc:
            raise StockUnavailableError(f"stock no disponible: {exc}")
        if resp.status_code == 404:
            raise StockProductNotFoundError(f"producto inexistente: {product_id}")
        if resp.status_code == 409:
            raise StockInsufficientError(resp.json().get("detail", "stock insuficiente"))
        if not resp.is_success:
            raise self._unavailable(resp, f"ajuste de producto={product_id}")
        return int(resp.json()["cantidad"])


stock_client = StockClient()
