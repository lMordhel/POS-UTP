# SPEC-FRONT-009 — Vistas legibles de Productos, Usuarios y Auditoría

## Metadata

- ID: SPEC-FRONT-009
- Requirement: ERF-04, ERF-05, ERF-06, ERF-08, ERF-09, ERF-10 (transversal de catálogo, stock, usuarios y auditoría)
- Service: Frontend
- Status: VALIDATED
- Version: 1.0.0
- Priority: Media

## Objective

Hacer que las vistas de **Productos**, **Usuarios** y **Auditoría de inventario** se
entiendan a la primera, sin knowledge previo del sistema, y que los datos que
muestren se puedan leer de un vistazo.

## Problem

Verificación en ejecución del 2026-10-21 (Vite 6.4.3 + FastAPI + PostgreSQL en
contenedores, con ego-browser):

1. Las tres vistas eran las únicas que **no aplicaban el sistema de estilos** del
   proyecto: tablas y botones nativos, sin jerarquía visual ni separación entre
   secciones.
2. Los formularios de alta y edición no tenían **etiqueta visible**: el usuario
   veía «Código», «Nombre», «Precio» y «Stock inicial» solo como placeholder, sin
   saber qué significaba «Stock inicial» ni qué formato esperaba el código.
3. Los formularios de alta aparecían **siempre abiertos** encima de la tabla, y
   los de edición y ajuste se renderizaban «en el aire», sin panel que los
   delimite: el usuario no sabía si estaba viendo datos o un formulario.
4. **Faltaba contexto**: ninguna vista explicaba qué era, qué se podía hacer ni
   qué significaban sus datos. En Usuarios no se explicaba la diferencia entre
   `admin` y `cajero`; en Auditoría se mostraba `svc-sales` o `1` como actor y
   `venta:19` como motivo, sin traducirlos.
5. La **auditoría no mostraba la fecha** del movimiento, aunque la API la entrega
   (`created_at`), y no ofrecía ninguna cifra resumen.
6. No había **estados vacíos** ni contadores: un filtro sin resultados y un
   catálogo vacío se veían igual que un error.

## Scope

* Sistema de estilos compartido para encabezado de sección, tarjetas de
  formulario, campos con etiqueta, badges, tira de resumen, tabla legible y
  estado vacío.
* Reestructuración de la vista de Productos (contexto, alta colapsable, catálogo
  con estados visibles y jerarquía de acciones).
* Reestructuración de la vista de Usuarios (leyenda de roles, alta colapsable,
  estados y roles con etiqueta).
* Reestructuración de la vista de Auditoría (fecha, motivo y actor traducidos,
  tira de resumen y filtro con estado).
* Corrección del `box-sizing` de los controles nativos del proyecto.

## Out of Scope

* Rediseño de las vistas de **Nueva venta** y **Ventas** (ya aplican el sistema
  de estilos de SPEC-FRONT-005/006/008).
* Persistir el estado de los filtros en la URL: la navegación por pestañas es
  por estado, sin router (SPEC-FRONT-001, sin React Router por alcance
  académico).
* Pruebas de interfaz automatizadas: sin runner de tests-UI (ADR-014, ADR-015,
  ADR-016).
* Cambios de API, de esquema de datos o de permisos.

## Actors

* Administrador de la microempresa (`admin`): gestiona catálogo, usuarios,
  existencias y auditoría.
* Vendedor o encargado de ventas (`cajero`): consulta el catálogo.

## Functional Requirements

* FR-01: Cada vista debe abrir con un encabezado que diga **qué es** la vista y
  **qué se puede hacer** en ella.
* FR-02: Todo control de formulario debe tener **etiqueta visible** y, cuando
  el formato no sea obvio, una pista con un ejemplo.
* FR-03: Los formularios de alta deben estar **cerrados por defecto** y abrirse
  con una acción explícita; los formularios de edición y ajuste deben aparecer
  en un panel delimitado, con título y acción de cancelar.
* FR-04: Los estados que el usuario debe interpretar (activo/inactivo,
  con/sin stock, rol) deben mostrarse con una **etiqueta visual**, no con un
  «Sí»/«No» suelto.
* FR-05: Las acciones deben tener **jerarquía**: la principal destacada, la
  destructiva diferenciada, y el rótulo debe ser explícito («Ajustar stock»,
  «Ver detalle»).
* FR-06: La vista de Usuarios debe **explicar qué puede hacer cada rol**.
* FR-07: La vista de Auditoría debe mostrar la **fecha** del movimiento, traducir
  el motivo (`venta:19` → «Venta #19») y el actor (`svc-sales` → «Servicio de
  ventas», id de usuario → nombre de usuario), y ofrecer una **tira de resumen**
  con los movimientos, las unidades sumadas, las restadas y el saldo neto.
* FR-08: Las vistas deben manejar el **estado vacío** (sin catálogo, sin
  usuarios, sin movimientos, sin resultados de búsqueda) con un mensaje que diga
  qué hacer a continuación.

## Acceptance Criteria

### AC-FRONT09-01 — Contexto de la vista

Given el administrador abre Productos, Usuarios o Auditoría
When la vista carga
Then debe mostrar título, una descripción de para qué sirve y cuántas filas hay.

### AC-FRONT09-02 — Formularios con etiqueta

Given se abre el alta de producto, de usuario o el ajuste de stock
When se miran los campos
Then cada uno debe tener etiqueta visible y, los de formato ambiguo, una pista
con ejemplo; el texto de la etiqueta debe estar asociado al control.

### AC-FRONT09-03 — Formularios en panel

Given el administrador pulsa «Nuevo producto», «Nuevo usuario», «Editar» o
«Ajustar stock»
When se abre el formulario
Then debe aparecer en un panel con título y descripción, con acciones de
guardar y cancelar; el alta debe estar cerrada hasta que se pulse su botón.

### AC-FRONT09-04 — Estados legibles

Given el catálogo tiene productos activos, inactivos y sin existencias
When se muestra la tabla
Then cada estado debe tener una etiqueta visible y el stock 0 debe destacarse
como «Sin stock».

### AC-FRONT09-05 — Acciones con jerarquía

Given una fila con acciones
When se mira la columna de acciones
Then los rótulos deben ser explícitos y la acción destructiva debe estar
diferenciada del resto.

### AC-FRONT09-06 — Roles explicados

Given el administrador abre Usuarios
When consulta «¿Qué hace cada rol?»
Then debe ver qué puede hacer `admin` y qué puede hacer `cajero`.

### AC-FRONT09-07 — Auditoría legible

Given hay movimientos de inventario
When se abre Auditoría
Then cada fila debe mostrar la fecha en formato es-PE de 24 horas, el motivo
traducido, el actor identificado y el saldo de existencias; debe existir una
tira de resumen con los totales de la página.

### AC-FRONT09-08 — Estados vacíos

Given no hay productos, usuarios, movimientos o resultados de búsqueda
When se muestra la vista
Then debe aparecer un mensaje que explique el motivo y qué hacer a continuación.

## Verification

Los AC se verifican por **ejecución en navegador** (ego-browser sobre la
aplicación en marcha), recorriendo las tres vistas y capturando el estado del
DOM y el texto renderizado. Se verify también el camino funcional (alta de
producto, ajuste de stock y alta de usuario) para confirmar que los formularios
siguen invocando la API como antes. No hay runner de tests-UI en el proyecto
(ADR-014, ADR-015, ADR-016); es la misma excepción documentada en
SPEC-FRONT-003 y SPEC-FRONT-008.

## Traceability

Requirement: ERF-04, ERF-05, ERF-06, ERF-08, ERF-09, ERF-10 (transversal)
Endpoint: los de la API (sin cambios de contrato)
Service: Frontend (presentación); sin cambios en Sales ni Stock
Tests: verificación manual en navegador (AC-FRONT09-01..08); sin tests-UI.

## Change History

| Version | Date | Change | Reason |
|---|---|---|---|
| 1.0.0 | 2026-10-21 | IMPLEMENTED → VALIDATED | AC-FRONT09-01..08 verificados en ejecución (sin errores de consola) y camino funcional comprobado |
| 1.0.0 | 2026-10-21 | APPROVED 1.0.0 | Decisión explícita del usuario (2026-10-21): «mejora Productos, Usuarios y Auditoría; no se entiende a nivel de usuario» |
| 0.1.0 | 2026-10-21 | Initial specification (DRAFT) | Análisis en ejecución de la legibilidad de las tres vistas |
