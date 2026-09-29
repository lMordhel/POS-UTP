"""AC-ERF06 tests for SPEC-STOCK-004 (skill python-testing-patterns: AAA, one behavior per test)."""

import pytest


@pytest.mark.integration
def test_create_product_valid_returns_201_with_initial_stock(client):
    """AC-ERF06-01: crear producto válido → 201 con inventario inicial."""
    response = client.post(
        "/api/v1/products",
        json={
            "codigo": "P-100",
            "nombre": "Café molido",
            "descripcion": "Bolsa 500g",
            "precio": "25.90",
            "cantidad_inicial": 50,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["codigo"] == "P-100"
    assert body["stock"] == 50
    assert body["activo"] is True


@pytest.mark.integration
def test_create_product_duplicate_codigo_returns_409(client, sample_product):
    """AC-ERF06-02: código duplicado → 409 sin crear registros."""
    response = client.post(
        "/api/v1/products",
        json={
            "codigo": sample_product["codigo"],
            "nombre": "Duplicado",
            "precio": "5.00",
            "cantidad_inicial": 1,
        },
    )
    assert response.status_code == 409


@pytest.mark.integration
def test_update_product_valid_keeps_stock(client, sample_product):
    """AC-ERF06-03: PUT actualiza catálogo sin alterar cantidad."""
    response = client.put(
        f"/api/v1/products/{sample_product['id']}",
        json={"nombre": "Nombre nuevo", "precio": "12.00"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["nombre"] == "Nombre nuevo"
    assert body["stock"] == sample_product["stock"]


@pytest.mark.integration
def test_update_product_unknown_id_returns_404(client):
    response = client.put("/api/v1/products/9999", json={"nombre": "X"})
    assert response.status_code == 404


@pytest.mark.integration
def test_deactivate_product_marks_inactive(client, sample_product):
    """AC-ERF06-04: DELETE lógico → activo=false."""
    response = client.delete(f"/api/v1/products/{sample_product['id']}")
    assert response.status_code == 200
    assert response.json()["activo"] is False


@pytest.mark.integration
def test_deactivate_unknown_id_returns_404(client):
    assert client.delete("/api/v1/products/9999").status_code == 404


@pytest.mark.integration
@pytest.mark.parametrize(
    "payload",
    [
        {"codigo": "", "nombre": "X", "precio": "5.00"},  # código vacío
        {"codigo": "P-X", "nombre": "", "precio": "5.00"},  # nombre vacío
        {"codigo": "P-X", "nombre": "X", "precio": "0"},  # precio <= 0
        {"codigo": "P-X", "nombre": "X", "precio": "-1"},  # precio negativo
        {"codigo": "P-X", "nombre": "X", "precio": "5.00", "cantidad_inicial": -1},
    ],
    ids=["empty-codigo", "empty-nombre", "zero-precio", "negative-precio", "negative-cantidad"],
)
def test_create_product_invalid_returns_422(client, payload):
    """AC-ERF06-05: validaciones → 422."""
    assert client.post("/api/v1/products", json=payload).status_code == 422


@pytest.mark.integration
def test_get_product_unknown_id_returns_404(client):
    assert client.get("/api/v1/products/9999").status_code == 404
