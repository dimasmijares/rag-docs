---
name: release-loop
description: >-
  Ejecuta en serie las WRK-TASK de la release activa sin supervisión humana,
  parando siempre en un checkpoint seguro (entre tareas, con main sincronizado y
  árbol limpio) y dejando margen de presupuesto de tokens para no cortarse en un
  punto crítico. Úsala para peticiones tipo "continúa la release activa hasta
  cerrarla", "ejecuta las tareas de la release" o "sigue con el plan de release".
---

# release-loop

Bucle autónomo para completar una release KDD (`WRK-SPEC` + `WRK-PLAN`) tarea a tarea,
con parada segura antes de agotar el presupuesto de la sesión.

## Antes de empezar

1. `git checkout main; git pull --ff-only`.
2. `gh pr list --state open` — anota PRs abiertas propias de la release.
3. `./scripts/kdd.ps1 validate` y `./scripts/kdd.ps1 orphans`.
4. Identifica la release activa (status `active` en `WRK-SPEC`/`WRK-PLAN`) y su tabla de
   Task Decomposition. Sigue el protocolo de iteración de `AGENTS.md` y
   `specs/documentation/DOC-RAG-002-platform-operations.md`; no lo dupliques aquí.

## Bucle

Repite mientras queden WRK-TASK no terminales en la release **y** el chequeo de presupuesto
(abajo) dé verde:

1. **Elige** la siguiente WRK-TASK cuyas dependencias estén *todas* merged y terminales en
   `main`. Si ninguna lo está, para: hay PRs pendientes de merge o el DAG necesita revisión.
2. `./scripts/kdd.ps1 context -Id WRK-TASK-NNN` para cargar dependencias y specs activados.
3. Rama `codex/wrk-task-NNN-slug`. Implementa **solo** dentro del File Scope declarado.
4. Si la tarea necesita Qdrant u Ollama, arráncalos (ver `CLAUDE.md`). Si no arrancan de
   verdad, para y avisa; no simules resultados.
5. Cumple los Acceptance Criteria, completa la sección Evidence y sube `status` a `completed`
   (o `archived` según el lifecycle). Actualiza la tabla del `WRK-PLAN`.
6. `./scripts/verify.ps1` en verde localmente.
7. PR contra `main`. Espera a que **todos** los checks de CI pasen.
8. Merge (`gh pr merge <n> --squash --delete-branch`), luego `git checkout main; git pull --ff-only`.
9. Vuelve al paso de chequeo de presupuesto.

## Chequeo de presupuesto (antes de cada iteración)

Estima el margen restante con la **primera** fuente disponible:

1. **Reminder de sesión.** Si en el contexto reciente hay un aviso
   `<total_tokens> … left`, úsalo. Para si el valor cae por debajo del **15 %** del que
   había al inicio de esta invocación, o por debajo de un suelo absoluto de seguridad.
2. **ccusage** (opcional, terceros). Si el comando está disponible:
   `npx -y ccusage@latest blocks --active --json`. Mira el bloque de 5 h activo y su
   proyección (`projection.totalTokens`, `remainingMinutes`). Para si la proyección se
   acerca al techo configurado en `.claude/budget.local.json` (`{ "blockTokenCeiling": N }`),
   o si `remainingMinutes` es menor que lo que suele tardar una iteración completa.
   No instales ccusage ni lo añadas como dependencia del repo; si no está, sáltalo.
3. **Sin señal fiable.** Aplica un tope duro: como máximo **3** WRK-TASK completadas por
   invocación. Al alcanzarlo, para y reporta.

Ante la duda, **para**. El coste de una parada temprana es una sesión más; el de quedarse
sin tokens a mitad de un `git push` o una edición es un estado sucio que un humano tiene
que desenredar.

## Parada segura

Sólo son puntos seguros:

- Justo después de un merge, con `main` sincronizado y `git status` limpio.
- Antes de crear la rama de la siguiente tarea.

**Nunca** pares con: árbol de trabajo sucio, fichero a medio editar, rama local con commits
sin PR, o una PR abierta que ibas a iterar. Si el presupuesto se agota en mitad de una
tarea:

- Si falta **poco** para el merge (CI verde, solo queda mergear): termina esa tarea y para.
- Si la tarea está **empezada**: `git checkout main`, borra la rama local
  (`git branch -D codex/wrk-task-NNN-slug`), deja `main` limpio. La tarea se retomará de cero.

## Al parar (siempre)

Reporta, en el chat, de forma compacta:

- Tareas completadas y mergeadas en esta invocación (con nº de PR).
- Estado exacto: rama actual, `git status`, PRs abiertas.
- Siguiente WRK-TASK lista y sus dependencias.
- Motivo de la parada (presupuesto / CI / decisión humana / infra / release completa).
- Prompt para reanudar: `Continúa la release activa hasta cerrarla.`

No arranques trabajo nuevo después de decidir parar.

## Escala a un humano (no sigas solo) si

- Una tarea requiere una decisión de diseño nueva (ADR) o un cambio transversal (RFC).
- CI falla dos veces por la misma causa tras un intento de arreglo.
- Las dependencias, el orden de integración o el File Scope son ambiguos.
- Un servicio local necesario no arranca y no es trivial resolverlo.
