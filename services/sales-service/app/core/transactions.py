"""Commit de la transacción del request antes de enviar la respuesta.

FastAPI >= 0.106 ejecuta el código posterior al `yield` de una dependencia
DESPUÉS de enviar la respuesta, así que commitear en `get_db` confirmaba la
escritura cuando el cliente ya tenía su 2xx: una lectura inmediata devolvía el
estado anterior y un fallo de commit no podía reportarse (verificado contra
Postgres: 10/10 lecturas obsoletas sin espera, 0/10 con 300 ms).

Este `APIRoute` commitea cuando el endpoint terminó y todavía no se envió nada.
Si el endpoint levanta, no commitea: `get_db` hace rollback.

Es opt-in: cada `APIRouter` que declare endpoints de escritura tiene que pasar
`route_class=CommitBeforeResponseRoute`. Como `get_db` ya no commitea, un
router nuevo que lo olvide pierde sus escrituras en silencio; cualquier router
de escritura debe cubrirse.

El commit va al threadpool para no bloquear el event loop: `db.commit()` es
sincrónico y una espera de lock retendría al worker entero. El teardown de
`get_db` corría en el threadpool, y esto conserva esa propiedad.
"""

from fastapi import Request, Response
from fastapi.routing import APIRoute
from starlette.concurrency import run_in_threadpool


class CommitBeforeResponseRoute(APIRoute):
    """Commit de la sesión del request después del endpoint, antes de responder."""

    def get_route_handler(self):
        original_handler = super().get_route_handler()

        async def handler(request: Request) -> Response:
            response = await original_handler(request)
            db = getattr(request.state, "db", None)
            if db is not None and db.in_transaction():
                await run_in_threadpool(db.commit)
            return response

        return handler
