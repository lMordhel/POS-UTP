"""Configuración de logging de proceso (SPEC-OPS-002, S5).

Antes nadie configuraba el root logger: `app.access` emitía INFO a un root sin
handlers, así que en producción los access logs se descartaban y sólo
sobrevivían los WARNING+ del `lastResort` de la stdlib.

No se usa `logging.basicConfig` a propósito: se saltea *todo* el trabajo cuando
el root ya tiene handlers (uvicorn, pytest), incluido el nivel, así que la
configuración quedaría a merced del orden de import. Acá el handler se marca y
se instala exactamente una vez.
"""

import logging
import os
import sys

DEFAULT_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
HANDLER_MARKER = "pos_stderr_handler"


def configure_logging() -> None:
    """Instala el handler de stderr una sola vez y fija el nivel del proceso.

    `POS_LOG_LEVEL` (default `INFO`) va sin prefijo de servicio: es una decisión
    de despliegue, igual que `POS_ENV`.
    """
    root = logging.getLogger()
    if not any(getattr(h, HANDLER_MARKER, False) for h in root.handlers):
        handler = logging.StreamHandler(sys.stderr)
        setattr(handler, HANDLER_MARKER, True)
        handler.setFormatter(logging.Formatter(DEFAULT_FORMAT))
        root.addHandler(handler)
    root.setLevel(os.getenv("POS_LOG_LEVEL", "INFO").upper())
