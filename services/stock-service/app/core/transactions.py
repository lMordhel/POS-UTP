"""Commit de la transacción del request antes de enviar la respuesta.

FastAPI >= 0.106 ejecuta el código posterior al `yield` de una dependencia
DESPUÉS de enviar la respuesta, así que commitear en `get_db` confirmaba la
escritura cuando el cliente ya tenía su 2xx: una lectura inmediata devolvía el
estado anterior y un fallo de commit no podía reportarse (verificado contra
Postgres: 10/10 lecturas obsoletas sin espera, 0/10 con 300 ms).

Este `APIRoute` commitea cuando el endpoint terminó bien y todavía no se envió
nada. Si el endpoint levanta, no commitea: `get_db` hace rollback. Es un punto
único, así que un endpoint nuevo no puede olvidarse de commitear.
"""

from fastapi import Request, Response
from fastapi.routing import APIRoute


class CommitBeforeResponseRoute(APIRoute):
    """Commit de la sesión del request después del endpoint, antes de responder."""

    def get_route_handler(self):
        original_handler = super().get_route_handler()

        async def handler(request: Request) -> Response:
            response = await original_handler(request)
            db = getattr(request.state, "db", None)
            if db is not None and db.in_transaction():
                db.commit()
            return response

        return handler
