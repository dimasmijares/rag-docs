---
id: WRK-TASK-099
type: spec
layer: work-task
scope: ephemeral
status: archived
confidence: medium
version: 0.2.0
created: 2026-09-13
updated: 2026-09-13
owner: rag-docs-team
parent: WRK-PLAN-013
activates: [ARCH-002, DOC-RAG-003, RULE-002]
dependencies:
  - id: WRK-TASK-097
    relation: depends-on
  - id: RFC-004
    relation: depends-on
tags: [fabric, bootstrap, identity, environment]
---

# WRK-TASK-099 — Bootstrap del workspace Fabric

## Objective

Montar de forma reproducible el workspace Fabric del perfil opcional, con identidad de mínimo
privilegio y sin secretos versionados.

## File Scope

Incluye la carpeta `fabric/` (desplegada con Fabric CLI; ver Evidence), el extra opcional `[fabric]`
en `pyproject.toml` (y `uv.lock` regenerado por `uv`), el build del wheel para el Environment y
`specs/documentation/DOC-RAG-003-*`. Excluye el backend vectorial y cualquier dato no sintético.

## Acceptance Criteria

- [x] Lakehouse, SQL database y Environment con el wheel del proyecto existen y están descritos en
      `DOC-RAG-003`.
- [x] La variable library contiene sólo parámetros no sensibles; ningún ID de tenant, cliente o
      workspace se versiona.
- [x] El service principal tiene el rol mínimo necesario en el workspace; la habilitación del tenant
      la confirma la persona administradora.
- [x] `fabric/` pasa el gate público ampliado de `WRK-TASK-097`.
- [x] `scripts/verify.ps1` no requiere el extra `[fabric]`.

## Evidence

- Decisión del propietario (2026-09-13), antes de ejecutar:
  - Opción A: el repositorio es la fuente de verdad y el despliegue se hace con Fabric CLI
    (`fab import`) en lugar de Git integration. GitHub sync está deshabilitado en el tenant y
    requeriría un PAT; queda opcional y documentado en `DOC-RAG-003`. Por eso el File Scope ya no
    dice "sincronizada por Git integration".
  - Un único workspace estable `rag-docs` por entorno, no uno por versión.
  - Service principal con rol Contributor.
- Entorno creado con `fab` 1.7 (sesión de la persona administradora) en la capacidad Trial:
  - workspace `rag-docs`;
  - `ragdocs_eval.Lakehouse`, `ragdocs_vectors.SQLDatabase`, `ragdocs_env.Environment` y
    `ragdocs_params.VariableLibrary`.

  Fabric añade automáticamente los `SQLEndpoint` de Lakehouse y SQL database.
- Environment: wheel `rag_docs-0.3.0-py3-none-any.whl` (`uv build --wheel`) subido como librería
  custom y publicado con `fabric/tools/fabric_api.py publish-wheel`, porque `fab` 1.7 no sube
  librerías. Lo hizo el propio service principal, lo que prueba que Contributor basta.
  `publishDetails`: `sparkLibraries` y `sparkSettings` en `Success` (19:23 → 19:29 UTC), runtime 1.3.
  La exportación del Environment lista `Libraries/CustomLibraries/rag_docs-0.3.0-py3-none-any.whl`.
  La importación del paquete dentro de una sesión Spark se verificará con los primeros notebooks
  (`WRK-TASK-101`/`102`).
- Variable library: `fabric/ragdocs_params.VariableLibrary/variables.json`, con 8 variables de tipo
  String no sensibles: nombres de items, `corpus_version`, modelo y revisión de embeddings,
  `vector_backend`, `vector_search_mode`. Importada con `fab import -f` y verificada exportándola de
  nuevo. Sin IDs de tenant, cliente ni workspace; los items se resuelven por nombre. El `.platform`
  solo contiene `logicalId`.
- Identidad:
  - El objectId del service principal se resuelve en tiempo de ejecución (`az ad sp show`) y se le
    asigna Contributor con `fab acl set`. `fab acl dir` muestra Admin (persona) y Contributor
    (service principal).
  - `fabric_api.py check-access --as sp` con `CertificateCredential` ve los cuatro items.
  - Habilitación del tenant, confirmada por la persona administradora y leída con la API de admin en
    solo lectura: "Service principals can call Fabric public APIs"
    (`ServicePrincipalAccessPermissionAPIs`) activado. La creación de workspaces por service
    principals está desactivada y no es necesaria.
  - El service principal no tiene roles de Azure.
- Secretos e identificadores: todos en un `fabric.env` fuera del repo (`FABRIC_TENANT_ID`,
  `FABRIC_CLIENT_ID`, `FABRIC_CLIENT_CERT_PATH`, `FABRIC_CAPACITY_NAME`, `FABRIC_WORKSPACE_NAME`).
  Ni scripts ni documentación imprimen o versionan IDs o tokens.
- `fabric/bootstrap.ps1`: bootstrap idempotente de todo lo anterior. Ejecutado por segunda vez sobre
  el entorno existente (`-SkipWheel`): termina en 0 sin crear duplicados. Esa ejecución destapó y
  corrigió un defecto: `fab exists` devuelve `true` más una línea vacía.
- `pyproject.toml`: extra opcional `[fabric]` (`azure-identity`) y `uv.lock` regenerado con `uv lock`.
  `scripts/verify.ps1` sigue en verde sin instalar el extra; `fabric/tools/fabric_api.py` importa
  `azure.identity` solo al ejecutarse.
- `specs/documentation/DOC-RAG-003-fabric-platform-operations.md` (0.2.0): modelo de entornos,
  prerrequisitos, fichero de entorno con marcadores, bootstrap, items y parámetros, mínimo
  privilegio y alternativa más estricta, verificación y desmontaje.
- Gate público (`WRK-TASK-097`): `scripts/check-public-safety.ps1` supera todo el repositorio y los
  ficheros de `fabric/`.
- No se versionan el `.dacpac` de la SQL database (binario, esquema a cargo de `WRK-TASK-100`) ni el
  wheel.
