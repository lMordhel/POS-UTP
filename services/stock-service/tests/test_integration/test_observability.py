"""AC-OBS02 (SPEC-OPS-002): logs, métricas y salud en Stock — AAA."""
import json
import logging

import pytest

import app.main as main_module


def _count(text: str, name: str, route: str | None = None, status: str | None = None) -> float:
    total = 0.0
    for line in text.splitlines():
        if not line.startswith(name + "{"):
            continue
        if route is not None and f'route="{route}"' not in line:
            continue
        if status is not None and f'status="{status}"' not in line:
            continue
        total += float(line.rsplit(" ", 1)[1])
    return total


@pytest.mark.integration
def test_request_id_echo_and_generated(client):
    """AC-OBS02-01."""
    resp = client.get("/health", headers={"X-Request-ID": "abc-123"})
    assert resp.headers.get("x-request-id") == "abc-123"
    resp2 = client.get("/health")
    assert resp2.headers.get("x-request-id")


@pytest.mark.integration
def test_metrics_groups_by_template(client, admin_headers):
    """AC-OBS02-02: /1 y /2 suman en la misma serie plantilla."""
    before = client.get("/metrics").text
    client.get("/api/v1/products/1", headers=admin_headers)
    client.get("/api/v1/products/2", headers=admin_headers)
    after = client.get("/metrics").text
    delta = _count(after, "http_requests_total", "app.api.v1.endpoints.products.get_product") - _count(
        before, "http_requests_total", "app.api.v1.endpoints.products.get_product"
    )
    assert delta == 2


@pytest.mark.integration
def test_metrics_latency_and_info(client):
    """AC-OBS02-03."""
    body = client.get("/metrics").text
    assert "http_request_duration_seconds_sum" in body
    assert "http_request_duration_seconds_count" in body
    assert 'app_info{version="1.0.0"} 1' in body
    assert "text/plain" in client.get("/metrics").headers.get("content-type", "")


@pytest.mark.integration
def test_ready_ok_and_unready(client, monkeypatch):
    """AC-OBS02-04."""
    ok = client.get("/ready")
    assert ok.status_code == 200 and ok.json() == {"status": "ok"}
    monkeypatch.setattr(main_module, "check_db", lambda: False)
    down = client.get("/ready")
    assert down.status_code == 503 and down.json() == {"status": "unready"}


@pytest.mark.integration
def test_access_log_json(client, caplog):
    """AC-OBS02-05."""
    with caplog.at_level(logging.INFO, logger="app.access"):
        client.get("/health", headers={"X-Request-ID": "log-1"})
    records = [r for r in caplog.records if r.name == "app.access"]
    assert records
    entry = json.loads(records[-1].message)
    assert entry["method"] == "GET" and entry["route"] == "app.main.health"
    assert entry["status"] == 200 and entry["request_id"] == "log-1"
    assert isinstance(entry["duration_ms"], int)
