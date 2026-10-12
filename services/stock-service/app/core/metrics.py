"""Métricas mínimas en formato Prometheus (SPEC-OPS-002, sin dependencias).

En memoria y por proceso (1 réplica; ver BR-02 de la SPEC).
"""
import threading

APP_VERSION = "1.0.0"

_lock = threading.Lock()
_counts: dict[tuple[str, str, str], int] = {}
_latency: dict[tuple[str, str, str], list[float]] = {}


def observe(method: str, route: str, status: int, duration_s: float) -> None:
    key = (method, route, str(status))
    with _lock:
        _counts[key] = _counts.get(key, 0) + 1
        cell = _latency.setdefault(key, [0, 0.0])
        cell[0] += 1
        cell[1] += duration_s


def render() -> str:
    with _lock:
        counts = dict(_counts)
        latency = {k: tuple(v) for k, v in _latency.items()}
    lines = [
        "# HELP http_requests_total Total de requests HTTP.",
        "# TYPE http_requests_total counter",
    ]
    for (method, route, status), count in sorted(counts.items()):
        lines.append(f'http_requests_total{{method="{method}",route="{route}",status="{status}"}} {count}')
    lines += [
        "# HELP http_request_duration_seconds Duración de requests HTTP en segundos.",
        "# TYPE http_request_duration_seconds summary",
    ]
    for (method, route, status), (count, total) in sorted(latency.items()):
        labels = f'method="{method}",route="{route}",status="{status}"'
        lines.append(f"http_request_duration_seconds_count{{{labels}}} {count}")
        lines.append(f"http_request_duration_seconds_sum{{{labels}}} {total:.6f}")
    lines += [
        "# HELP app_info Información de la aplicación.",
        "# TYPE app_info gauge",
        f'app_info{{version="{APP_VERSION}"}} 1',
    ]
    return "\n".join(lines) + "\n"
