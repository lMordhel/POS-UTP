"""E2E real Ventas → Stock por HTTP (Fase 3).

Arranca ambos servicios con uvicorn (SQLite temporal) y ejecuta la saga
completa sin dobles: crear producto → registrar venta → verificar total y
descuento → 409 sin stock → 404 inexistente.

Uso: py infra/e2e_check.py
"""

import os
import subprocess
import sys
import tempfile
import time
import urllib.request
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STOCK_DIR = os.path.join(ROOT, "services", "stock-service")
SALES_DIR = os.path.join(ROOT, "services", "sales-service")


def _wait(url: str, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                if r.status == 200:
                    return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError(f"servicio no levantó: {url}")


def _call(method: str, url: str, body: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read().decode() or "null")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="pos-e2e-")
    stock_db = os.path.join(tmp, "stock.db")
    sales_db = os.path.join(tmp, "sales.db")
    env_stock = dict(os.environ, STOCK_DATABASE_URL=f"sqlite:///{stock_db}")
    env_sales = dict(
        os.environ,
        SALES_DATABASE_URL=f"sqlite:///{sales_db}",
        SALES_STOCK_SERVICE_URL="http://127.0.0.1:8002",
    )
    stock = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8002"],
        cwd=STOCK_DIR, env=env_stock,
        stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
    )
    sales = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8001"],
        cwd=SALES_DIR, env=env_sales,
        stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
    )
    try:
        _wait("http://127.0.0.1:8002/health")
        _wait("http://127.0.0.1:8001/health")

        s, p = _call("POST", "http://127.0.0.1:8002/api/v1/products", {
            "codigo": "E2E-1", "nombre": "E2E", "precio": "10.00",
            "cantidad_inicial": 5})
        assert s == 201, (s, p)
        pid = p["id"]

        s, v = _call("POST", "http://127.0.0.1:8001/api/v1/sales", {
            "items": [{"producto_id": pid, "cantidad": 2}]})
        assert s == 201, (s, v)
        assert v["total"] in ("20.00", 20, 20.0), v
        assert v["items"][0]["subtotal"] in ("20.00", 20, 20.0), v

        s, st = _call("GET", f"http://127.0.0.1:8002/api/v1/products/{pid}/stock")
        assert s == 200 and st["cantidad"] == 3, (s, st)

        s, _ = _call("POST", "http://127.0.0.1:8001/api/v1/sales", {
            "items": [{"producto_id": pid, "cantidad": 10}]})
        assert s == 409, s

        s, _ = _call("POST", "http://127.0.0.1:8001/api/v1/sales", {
            "items": [{"producto_id": 9999, "cantidad": 1}]})
        assert s == 404, s

        s, st = _call("GET", f"http://127.0.0.1:8002/api/v1/products/{pid}/stock")
        assert st["cantidad"] == 3, st  # 409/404 no mutaron

        print("E2E OK: venta 201 total=20.00, stock 5->3, 409 y 404 verificados")
        return 0
    finally:
        stock.terminate()
        sales.terminate()


if __name__ == "__main__":
    raise SystemExit(main())
