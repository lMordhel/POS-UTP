"""Guardián del contrato de entorno (SPEC S6, odd/tasks/correctitud-sprint1.md).

`.env.example` es la plantilla versionada del servicio: lo único que un clon
nuevo tiene para saber qué variables existen y qué pide cada una. Si `Settings`
gana una variable y la plantilla no se actualiza, el repo miente y el que clona
no se entera.

Estos tests leen **solo los nombres de las claves**; nunca comparan ni imprimen
valores.
"""

from pathlib import Path

from app.core.config import Settings

ENV_EXAMPLE = Path(__file__).resolve().parents[2] / ".env.example"
PREFIX = "SALES_"

# POS_ENV no es campo de Settings: get_settings() lo lee con os.getenv y decide
# el fail-fast de secretos en producción.
EXTRA_KEYS = {"POS_ENV"}

# POS_LOG_LEVEL lo lee logging_config.py, no Settings.
KEYS_DE_OTROS_MODULOS = {"POS_LOG_LEVEL"}


def declared_keys() -> set[str]:
    """Claves declaradas en la plantilla, ignorando comentarios y líneas vacías."""
    keys = set()
    for line in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
        entry = line.strip()
        if not entry or entry.startswith("#") or "=" not in entry:
            continue
        keys.add(entry.split("=", 1)[0].strip())
    return keys


def test_env_example_existe() -> None:
    assert ENV_EXAMPLE.is_file(), f"Falta la plantilla {ENV_EXAMPLE}"


def test_env_example_declara_todas_las_variables_de_settings() -> None:
    esperadas = {f"{PREFIX}{campo}" for campo in Settings.model_fields} | EXTRA_KEYS
    faltantes = esperadas - declared_keys()
    assert not faltantes, f"Faltan en .env.example: {sorted(faltantes)}"


def test_env_example_no_declara_variables_que_nadie_lee() -> None:
    conocidas = (
        {f"{PREFIX}{campo}" for campo in Settings.model_fields}
        | EXTRA_KEYS
        | KEYS_DE_OTROS_MODULOS
    )
    desconocidas = declared_keys() - conocidas
    assert not desconocidas, f"Claves que ningún componente lee: {sorted(desconocidas)}"
