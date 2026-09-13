---
id: DOC-RAG-003
type: spec
layer: documentation
scope: persistent
status: draft
confidence: medium
version: 0.2.0
created: 2026-09-13
updated: 2026-09-13
owner: rag-docs-team
dependencies:
  - id: RFC-004
    relation: implements
  - id: ADR-RAG-013
    relation: implements
  - id: ADR-RAG-014
    relation: implements
  - id: DOC-RAG-002
    relation: extends
  - id: RULE-002
    relation: constrained-by
tags: [documentation, fabric, operations, security, cost]
---

# DOC-RAG-003 — Operación de la plataforma Fabric

## Intent

Mantener una guía verificable para montar, operar y desmontar el perfil opcional de Fabric sin
exponer secretos ni identificadores del entorno.

## Definition

La documentación cubrirá:

- Prerrequisitos: capacidad Fabric (Trial o F-SKU), workspace dedicado y corpus sintético.
- Identidad: service principal de Entra ID con certificado, rol de mínimo privilegio en el
  workspace, y habilitación del uso de APIs de Fabric por service principals, que hace una persona
  administradora del tenant.
- Definiciones de items versionadas en `fabric/` y desplegadas con Fabric CLI (`fab import`); el
  repositorio es la fuente de verdad. Git integration con GitHub queda opcional (requiere ajuste de
  tenant y una conexión con PAT) y no la usa el bootstrap.
- Environment con el wheel del proyecto (`uv build`) y extra opcional `[fabric]`; no activar
  outbound access protection.
- Variable library para parámetros por entorno, sin valores sensibles versionados.
- Gate `scripts/verify-fabric.ps1`: cuándo se ejecuta, credenciales introducidas por la persona
  usuaria y nunca en CI obligatorio (`WRK-TASK-100`).
- Worker de inferencia local (`ADR-RAG-014`): ventana batch, arranque, parada y dead-letter.
- Monitorización de consumo de capacidad (CU) y teardown completo del workspace.

## Modelo de entornos

Un workspace por entorno, actualizado en cada release; nunca un workspace por versión. Las
versiones viven en tags de Git y en `fabric/`; los datos se separan por fingerprint (tabla física y
alias, `RULE-004`) y por `corpus_version`. El entorno actual es un único workspace `rag-docs` en la
capacidad Trial; un `prod` futuro sería otro workspace desplegado desde el mismo `fabric/`.

## Montaje (WRK-TASK-099)

### 1. Prerrequisitos manuales

- Capacidad Fabric activa (Trial o F-SKU).
- Persona administradora del tenant: ajuste "Service principals can call Fabric public APIs"
  habilitado, preferiblemente restringido a un grupo de seguridad con el service principal. Crear
  workspaces con service principal no es necesario: el workspace lo crea una persona.
- Service principal de Entra ID de un solo tenant, sin roles RBAC de Azure, con certificado cuya
  clave privada vive sólo en el equipo del operador.
- Herramientas: Fabric CLI (`uv tool install ms-fabric-cli`), Azure CLI y `uv`.
- Sesiones: `az login --tenant <tenant> --allow-no-subscriptions` y `fab auth login` como persona
  administradora del workspace. Contraseña y MFA las introduce siempre la persona.

### 2. Fichero de entorno local

Fuera del repositorio (por ejemplo, en el perfil del usuario), nunca versionado:

```text
FABRIC_TENANT_ID=<tenant-id>
FABRIC_CLIENT_ID=<client-id>
FABRIC_CLIENT_CERT_PATH=<ruta al .pem>
FABRIC_CAPACITY_NAME=<nombre de la capacidad>
FABRIC_WORKSPACE_NAME=rag-docs
```

### 3. Bootstrap idempotente

```powershell
./fabric/bootstrap.ps1 -EnvFile <ruta a fabric.env>
```

El script, con `fab exists` antes de cada creación:

1. Crea el workspace `rag-docs` en la capacidad (`fab mkdir … -P capacityName=…`).
2. Crea `ragdocs_eval.Lakehouse`, `ragdocs_vectors.SQLDatabase`, `ragdocs_env.Environment` y
   `ragdocs_params.VariableLibrary`.
3. Importa la variable library desde `fabric/ragdocs_params.VariableLibrary` (`fab import -f`).
4. Resuelve el objectId del service principal (`az ad sp show`) y le asigna **Contributor** en el
   workspace (`fab acl set`).
5. Construye el wheel (`uv build --wheel`), lo sube como librería custom del Environment y publica
   (`fabric/tools/fabric_api.py publish-wheel`, REST de Fabric, porque `fab` 1.7 no sube
   librerías). La publicación tarda varios minutos.
6. Verifica, autenticando como service principal con certificado, que ve los cuatro items
   (`fabric/tools/fabric_api.py check-access --as sp`).

### Items y parámetros

| Item | Propósito |
|---|---|
| `ragdocs_eval.Lakehouse` | Plano de evaluación en Delta (`WRK-TASK-102`) |
| `ragdocs_vectors.SQLDatabase` | Ledger y tablas vectoriales derivadas (`ADR-RAG-013`, `WRK-TASK-100`) |
| `ragdocs_env.Environment` | Runtime Spark 1.3 con el wheel `rag_docs` |
| `ragdocs_params.VariableLibrary` | Nombres de items, `corpus_version`, modelo y revisión de embeddings, backend y modo de búsqueda |

La variable library sólo contiene valores no sensibles; los notebooks resuelven items por nombre,
nunca por ID.

### Mínimo privilegio

- Contributor es el rol mínimo que permite escribir en la SQL database y en tablas Delta del
  Lakehouse; Viewer o compartir items no dan escritura en el Lakehouse.
- Alternativa más estricta si el Lakehouse deja de escribirse desde el service principal: Viewer en
  el workspace más `GRANT` por esquema en la SQL database.
- El service principal no tiene roles de Azure, ni Admin/Member en el workspace, ni permisos de
  APIs de administración.

## Verificación

- `fabric/tools/fabric_api.py check-access --as sp` termina en 0 con los cuatro items en `ok`.
- `fab get rag-docs.Workspace/ragdocs_env.Environment -q properties.publishDetails` muestra
  `state: Success`.
- `scripts/check-public-safety.ps1` supera `fabric/` (`WRK-TASK-097`).
- `scripts/verify.ps1` sigue en verde sin el extra `[fabric]` ni credenciales.

## Backend vectorial y walking skeleton (WRK-TASK-100/101)

### Gate Fabric

```powershell
./scripts/verify-fabric.ps1 -EnvFile <ruta a fabric.env>                    # contrato
./scripts/verify-fabric.ps1 -EnvFile <ruta a fabric.env> -WalkingSkeleton   # recorrido completo
```

- Lo ejecuta la persona operadora con su `fabric.env`; nunca `scripts/verify.ps1` ni CI.
- Resuelve servidor y base de datos de `ragdocs_vectors` por REST y los guarda en `fabric.env`
  (`FABRIC_SQL_SERVER`, `FABRIC_SQL_DATABASE`) sin imprimirlos. Autentica como service principal
  con certificado y restaura las variables de entorno al terminar.
- Contrato: `tests/contract -m live` contra `FabricSqlVectorStore`, limpiando cada índice creado.
- `-WalkingSkeleton`:
  1. `scripts/publish_index_to_fabric.py` indexa el corpus sintético en local con el embedder
     fijado, copia chunks y vectores a un candidato en Fabric SQL del mismo fingerprint y lo valida
     (mismos chunks, mismos top hits, score ±1e-4). Solo entonces publica el alias y comprueba que
     el digest publicado es el local.
  2. `scripts/migration_drill.py --backend fabric_sql` migra a otro chunking, verifica que una
     vinculación obsoleta rechaza la consulta y hace rollback. Empieza y termina con el índice
     `migration_drill` limpio.
  3. Arranca la API local con `RAG_DOCS_VECTOR_BACKEND=fabric_sql` y exige que
     `GET /api/sources` declare `vector_backend: fabric_sql`. Después ejecuta `rag-docs-eval` con
     Ollama sobre el smoke gold set, que verifica la compatibilidad del fingerprint antes de
     puntuar.

  Los logs quedan en `_build/verify-fabric/`, ignorado por Git.

### API local servida desde Fabric

En el `.env` local (nunca versionado):

```text
RAG_DOCS_VECTOR_BACKEND=fabric_sql
RAG_DOCS_FABRIC_SQL_SERVER=<servidor>
RAG_DOCS_FABRIC_SQL_DATABASE=<base de datos>
RAG_DOCS_FABRIC_SQL_CREDENTIAL=azure_cli
```

- `azure_cli` usa la sesión de `az login` de la persona. `certificate` usa el service principal
  (`RAG_DOCS_FABRIC_TENANT_ID`, `RAG_DOCS_FABRIC_CLIENT_ID`, `RAG_DOCS_FABRIC_CLIENT_CERT_PATH`).
- Hay que instalar el extra con `uv sync --extra fabric`.
- El índice se publica antes con `scripts/publish_index_to_fabric.py`; la API solo consulta. La
  búsqueda es exacta (`vector_search_mode: exact`), así que la latencia no se compara con Qdrant.

## Desmontaje

Irreversible; lo ejecuta la persona operadora:

```powershell
fab acl del rag-docs.Workspace -I <objectId del service principal> -f
fab rm rag-docs.Workspace -f
```

Borrar el workspace elimina todos sus items y datos. Si el perfil se abandona, revocar además el
certificado del service principal o borrar la app registration en Entra ID.

## Acceptance Criteria

- Un entorno nuevo se monta desde cero siguiendo la guía, sin pasos implícitos.
- No se documentan secretos, certificados, IDs de tenant, cliente o workspace ni rutas personales.
- El teardown elimina todos los artefactos y la identidad deja de tener acceso.
- `scripts/verify.ps1` y el quickstart Compose siguen funcionando sin Fabric.
