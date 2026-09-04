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
- **Decisión sobre el historial de Git: no tomada por este agente, y no ejecutada ninguna acción
  sobre el historial.** Los cinco identificadores retirados del `HEAD` en este cambio siguen
  presentes en los commits anteriores del historial público de este repositorio. Retirarlos del
  historial exige `git filter-repo` (o equivalente), reescritura de hashes, coordinación de force-push
  y, muy probablemente, invalidar cualquier fork o clon existente — es una decisión que sólo puede
  tomar el propietario del dato, no una consecuencia automática de este WRK-TASK. Queda como acción
  pendiente y explícita, no como riesgo aceptado tácitamente.
