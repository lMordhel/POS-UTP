# Trazabilidad — POS-UTP

Relación obligatoria: `ERF → SPEC → AC → Endpoint → Service → Test`.

| ERF | Specification | Service | Acceptance Criteria | Endpoint | Tests | Status |
|---|---|---|---|---|---|---|
| ERF-01 | SPEC-SALES-001 | Sales | AC-ERF01-01, AC-ERF01-02, AC-ERF01-03, AC-ERF01-04 | POST /api/v1/sales | services/sales-service/tests/test_integration/test_sales.py (13 passed) + infra/e2e_check.py (E2E real OK) | Validated |
| ERF-02 | SPEC-STOCK-001 | Stock | AC-ERF02-01, AC-ERF02-02, AC-ERF02-03 | GET /api/v1/products, GET /api/v1/products/{id} | services/stock-service/tests/test_integration/test_product_read.py | Validated |
| ERF-03 | SPEC-SALES-002 | Sales | AC-ERF03-01, AC-ERF03-02, AC-ERF03-03 | POST /api/v1/sales (líneas) | services/sales-service/tests/test_integration/test_sales.py (13 passed) | Validated |
| ERF-04 | SPEC-STOCK-002 | Stock | AC-ERF04-01, AC-ERF04-02 | GET /api/v1/products/{id}/stock | services/stock-service/tests/test_integration/test_stock.py | Validated |
| ERF-05 | SPEC-STOCK-003 | Stock | AC-ERF05-01, AC-ERF05-02, AC-ERF05-03 | PATCH /api/v1/products/{id}/stock | services/stock-service/tests/test_integration/test_stock.py | Validated |
| ERF-06 | SPEC-STOCK-004 | Stock | AC-ERF06-01..AC-ERF06-05 | POST /api/v1/products, PUT /api/v1/products/{id}, DELETE /api/v1/products/{id} | services/stock-service/tests/test_integration/test_products.py (12 passed) | Validated |
| ERF-07 | SPEC-SALES-003 | Sales | AC-ERF07-01, AC-ERF07-02, AC-ERF07-03 | GET /api/v1/sales, GET /api/v1/sales/{id} | services/sales-service/tests/test_integration/test_sales.py (13 passed) | Validated |
| ERF-08 | SPEC-STOCK-005 | Stock | AC-ERF08-01, AC-ERF08-02 | GET /api/v1/products | services/stock-service/tests/test_integration/test_product_read.py | Validated |
| ERF-09 | SPEC-AUTH-001 | Sales | AC-AUTH01-01, AC-AUTH01-02, AC-AUTH01-03, AC-AUTH01-09, AC-AUTH01-10 | POST /api/v1/auth/login, POST /api/v1/auth/refresh | services/sales-service/tests/test_integration/test_auth.py (11 passed) + E2E con login | Validated |
| ERF-10 | SPEC-AUTH-001 | Sales + Stock | AC-AUTH01-04, AC-AUTH01-05, AC-AUTH01-06, AC-AUTH01-07, AC-AUTH01-08 | RBAC en endpoints Stock + Sales, POST/GET/PATCH /api/v1/users | test_auth.py + test_rbac.py (Stock, 4 passed) + suites existentes con headers | Validated |

Notas:

* ERF-01..ERF-08 validados con tests en verde; ERF-09/10 aprobados 2026-10-12 (SPEC-AUTH-001 1.0.0, implementación en curso).
* Futuro mapeo AC → test (ej. `AC-ERF05-01 → test_update_stock_valid_quantity`)
  ya sugerido en cada SPEC.
* Transversal: SPEC-ARCH-001 cubre ERF-01..ERF-08 a nivel de arquitectura.
