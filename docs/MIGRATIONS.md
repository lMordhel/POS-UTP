# Migraciones — POS-UTP (SPEC-OPS-001)

Cada servicio versiona su esquema con Alembic (propiedad de datos: un
historial por DB). Fuente de comportamiento: `SPEC-OPS-001`.

## Layout por servicio

```text
services/<svc>/alembic.ini            # solo para CLI (la URL real sale de settings)
services/<svc>/alembic/env.py         # metadata + URL desde settings
services/<svc>/alembic/script.py.mako # plantilla de revisiones
services/<svc>/alembic/versions/      # <rev>_*.py con upgrade() + downgrade()
```

## Comandos (desde `services/<svc>`)

```powershell
# Nueva revisión tras cambiar modelos (revisar el diff generado)
py -m alembic revision --autogenerate -m "descripcion"

# Aplicar en local / Postgres
py -m alembic upgrade head

# Retroceder SOLO en dev/tests (en prod, solo hacia adelante — BR-01)
py -m alembic downgrade base
```

## Arranque (`init_db`: adoptar-o-migrar)

1. DB vacía → `upgrade head`.
2. DB pre-Alembic con tablas → `create_all` (rellena huecos), luego `stamp head` (adopta, conserva datos).
3. Con versión → `upgrade head` (normalmente no-op).
4. Tabla `alembic_version` vacía (resto de upgrade caído) → se trata como caso 2.
5. Múltiples heads → error de arranque (linealizar antes).

## Sellar una DB vieja a mano

```powershell
py -m alembic stamp head   # solo si el esquema ya equivale a la baseline
```

## Reglas

- Una revisión = un cambio de esquema revisable, con `downgrade()` funcional.
- Sin seeds de negocio en migraciones (solo bootstrap de admin en código).
- Tests: `test_migrations.py` por servicio (head limpio, adopción con datos, downgrade).
