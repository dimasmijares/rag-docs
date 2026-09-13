---
id: WRK-TASK-097
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
activates: [DOC-RAG-002, RULE-002]
dependencies:
  - id: RFC-004
    relation: depends-on
tags: [public-safety, security, fabric, ci]
---

# WRK-TASK-097 — Gate público para artefactos Fabric

## Objective

Ampliar el gate `public-safety` para que ningún artefacto Fabric pueda versionar datos, outputs,
credenciales ni identificadores del entorno.

## File Scope

Incluye `scripts/check-public-safety.ps1`, `scripts/test-public-safety.ps1`, sus fixtures negativas
y el workflow de CI si cambia la invocación. Excluye crear artefactos Fabric reales.

## Acceptance Criteria

- [x] Se escanean `.ipynb`, `.platform` y PBIP/TMDL; un notebook con outputs se rechaza.
- [x] Se rechazan cadenas de conexión con credenciales y GUIDs de tenant o workspace fuera de una
      lista de marcadores de ejemplo.
- [x] Cada patrón nuevo tiene una fixture negativa que falla y una positiva que pasa.
- [x] El gate sigue sin contener en claro los identificadores que protege (`WRK-TASK-092`).

## Evidence

- `scripts/check-public-safety.ps1` añade a las extensiones escaneadas `.ipynb`, `.platform`,
  `.pbip`, `.pbir`, `.pbism`, `.bim`, `.tmdl`, `.pq` y `.sql`. Cada `.ipynb` se parsea como JSON:
  una celda con `outputs` no vacío produce `notebook con outputs` y un JSON inválido
  `notebook ilegible` (nunca se acepta sin inspeccionar).
- Patrones de contenido nuevos:
  - `cadena de conexión con credenciales`: `Password`/`Pwd`/`AccountKey`/`SharedAccessKey`/
    `SharedAccessSignature`/`Client Secret` con valor literal dentro de un segmento `;`. Los valores
    marcador (`<...>`, `{...}`, `${...}`, `$env:...`, `%...%`, `***`) se admiten.
  - `URL con credenciales`: usuario y secreto literales antes de `@` en una URL con esquema, con la misma
    excepción de marcadores.
  - `GUID de tenant o workspace fuera de marcadores de ejemplo`: GUID en la misma línea (hasta 60
    caracteres) que `tenant`, `workspace`, `lakehouse`, `warehouse`, `capacity`, `directory`,
    `groups/`, una URL de OneLake o `login.microsoftonline.com/`. Marcadores admitidos: los GUID de
    un único dígito repetido `0`, `1`, `a` y `f`. `logicalId` de `.platform` queda fuera a propósito:
    es un identificador lógico de item portable entre workspaces, no del entorno.
  - `endpoint SQL de Fabric`: host real `*.datawarehouse|database.fabric.microsoft.com`; un marcador
    como `<sql-endpoint>` pasa.
- Rutas nuevas rechazadas como `ruta privada candidata`: `.pbi/localSettings.json`, `.pbi/cache.abf`,
  cualquier `_delta_log/` y ficheros `.parquet`/`.abf` (datos materializados de lakehouse o modelo).
- `scripts/test-public-safety.ps1` añade `Assert-GatePasses` y, por patrón nuevo, una fixture
  negativa con su mensaje esperado y una positiva: notebook con outputs / ilegible frente a limpio;
  `.platform` con `workspaceId` real frente a marcador (con `logicalId` aleatorio en ambos); URL de
  login con tenant real frente a marcador; TMDL con endpoint real frente a `<sql-endpoint>`;
  cadena de conexión con contraseña literal frente a `<secret>`; URL con credencial frente a
  `${DB_PASSWORD}`; cuatro rutas PBIP/Delta privadas frente a `.pbi/editorSettings.json`,
  `definition.pbir` y un `.pbip` limpio. Todos los valores sensibles se construyen en tiempo de
  ejecución (GUID con `[guid]::NewGuid()`), por lo que el propio script de test pasa el gate.
- Criterio `WRK-TASK-092`: el test comprueba que `check-public-safety.ps1` sólo contiene GUIDs de
  marcador y ningún identificador derivado cargado desde `PUBLIC_SAFETY_IDENTIFIERS` o
  `config/public-safety-identifiers.local.txt`; la carga externa de identificadores no cambia.
- Compatibilidad: `System.IO.Path.GetRelativePath` (sólo .NET Core) se sustituye por un cálculo de
  ruta relativa, de modo que el test corre también en Windows PowerShell 5.1 además de `pwsh` en CI.
- Defecto previo corregido, detectado por la fixture `.platform` en CI (`pwsh` en Linux): el gate
  usaba `Get-Item` sin `-Force`, así que en Linux los ficheros con punto inicial (`.platform`,
  `.gitignore`, `.dockerignore`, `.env.example`) se omitían en silencio del escaneo de contenido.
  Ahora se leen con `-Force`.
- El workflow de CI no cambia: ya invoca ambos scripts en el job `public-safety`.
- Verificado localmente: `scripts/check-public-safety.ps1` supera los 289 archivos candidatos del
  repositorio sin falsos positivos; `scripts/test-public-safety.ps1` supera todas las
  comprobaciones negativas y positivas; `scripts/verify.ps1` en verde.
- `WRK-SPEC-013` y `WRK-PLAN-013` pasan a `active` para abrir la release `v0.4.0`.
