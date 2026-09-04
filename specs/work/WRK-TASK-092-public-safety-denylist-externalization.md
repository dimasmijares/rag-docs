---
id: WRK-TASK-092
type: spec
layer: work-task
scope: ephemeral
status: completed
confidence: medium
version: 0.2.0
created: 2026-09-04
updated: 2026-09-04
owner: rag-docs-team
parent: WRK-PLAN-012
activates: [DOC-RAG-002, RULE-002]
dependencies:
  - id: WRK-TASK-029
    relation: depends-on
  - id: ADR-RAG-011
    relation: depends-on
tags: [public-safety, privacy, gate, denylist]
---

# WRK-TASK-092 — Saneamiento del gate de publicación

## Objective

Sacar del repositorio público la lista de identificadores corporativos derivados que
`scripts/check-public-safety.ps1` incrusta en claro, sin perder capacidad de detección en CI.

## File Scope

Incluye `scripts/check-public-safety.ps1`, `scripts/test-public-safety.ps1`, `.gitignore`, el
workflow de calidad y la documentación del gate. Excluye `src/**`, `specs/**` salvo Evidence,
corpus y gold sets.

## Acceptance Criteria

- [x] El script carga los identificadores derivados desde un fichero local ignorado por Git o desde
      un secreto de CI, y la lista versionada queda vacía.
- [x] La ausencia del fichero produce una advertencia visible, nunca un falso verde silencioso.
- [x] CI ejecuta el gate con la lista completa cargada desde secreto.
- [x] Los tests del gate siguen demostrando detección usando identificadores sintéticos.
- [x] La decisión sobre el historial de Git queda registrada de forma explícita en Evidence, se
      actúe o no sobre él.

## Evidence

- `scripts/check-public-safety.ps1` ya no contiene ningún identificador corporativo derivado en
  claro. `Get-DerivedIdentifierPattern` construye el patrón en tiempo de ejecución a partir de:
  (a) la variable de entorno `PUBLIC_SAFETY_IDENTIFIERS` (identificadores separados por `|`), o
  (b) `config/public-safety-identifiers.local.txt`, ya cubierto por el patrón `config/**/*.local.*`
  de `.gitignore` (verificado con `git check-ignore -v`). Si ninguna de las dos fuentes tiene
  contenido, se emite `Write-Warning` visible y el gate continúa sin esa detección, nunca en verde
  silencioso.
- `config/public-safety-identifiers.example.txt` documenta el formato con un identificador de
  ejemplo, no real.
- Los cinco identificadores previamente en claro se movieron a
  `config/public-safety-identifiers.local.txt` (no versionado) en el checkout local y al secreto de
  repositorio `PUBLIC_SAFETY_IDENTIFIERS` vía `gh secret set` (confirmado con `gh secret list`,
  actualizado 2026-09-04T10:00:22Z).
- `.github/workflows/quality-gates.yml`, job `public-safety`, paso "Reject private paths and
  identifiers": inyecta `env: PUBLIC_SAFETY_IDENTIFIERS: ${{ secrets.PUBLIC_SAFETY_IDENTIFIERS }}`.
- `scripts/test-public-safety.ps1` añade un caso que fija `PUBLIC_SAFETY_IDENTIFIERS` a un
  identificador sintético (`SYNTHETIC_DERIVED_IDENTIFIER_FOR_TEST`) y exige que el gate lo detecte
  con el mensaje `identificador derivado conocido`; no depende de ningún dato real.
- Verificado localmente: `scripts/check-public-safety.ps1` supera 232 archivos candidatos con la
  lista local cargada; renombrando temporalmente el fichero local, el mismo comando emite la
  advertencia visible y sigue sin dar falso verde de detección; `scripts/test-public-safety.ps1`
  supera las tres comprobaciones negativas (IPv4 privada, ruta privada candidata, identificador
  derivado sintético).
- **Decisión sobre el historial de Git: tomada por el propietario el 2026-09-04, ejecutada.** Se
  reescribió con `git filter-repo --replace-text` sobre un mirror completo (31 commits), sustituyendo
  los cinco identificadores por marcadores `REDACTED_IDENTIFIER_N` en cada blob donde aparecían.
  Reescritos y forzados `main`, la rama `codex/adr-rag-007-011-roadmap-realignment` y el tag
  `v0.2.0`. `main` requirió que el propietario desactivara temporalmente "Do not allow force pushes"
  en la protección de rama para aceptar el push; se restaura tras el merge de esta PR. Verificado con
  `git grep` commit a commit sobre un clon limpio recién clonado del remoto: cero coincidencias en
  todo el historial público tras el push. Residuo aceptado y explícito: cualquier fork o clon hecho
  antes de esta reescritura conserva los commits antiguos con los identificadores en claro.
