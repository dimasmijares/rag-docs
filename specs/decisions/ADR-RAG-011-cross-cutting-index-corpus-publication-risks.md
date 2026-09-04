---
id: ADR-RAG-011
type: adr
layer: adr
scope: persistent
status: proposed
confidence: medium
version: 0.2.0
created: 2026-09-04
updated: 2026-09-04
owner: rag-docs-team
dependencies:
  - id: RFC-002
    relation: depends-on
  - id: ARCH-002
    relation: implements
  - id: FEAT-RAG-004
    relation: implements
  - id: RULE-002
    relation: constrained-by
  - id: RULE-004
    relation: constrained-by
  - id: DOM-RAG-001
    relation: constrained-by
tags: [architecture-decision, risk, fingerprint, corpus, public-safety, connectors, review]
---

# ADR-RAG-011 — Riesgos transversales: versionado del índice, corpus sintético y gate de publicación

## Context

Tres riesgos atraviesan las seis releases y ninguno tiene hoy un artefacto propio que los gobierne.
Los tres comparten una característica: fallan en silencio y se manifiestan como otra cosa (una
regresión de calidad, un resultado de benchmark raro, un commit aparentemente inocuo).

**Riesgo 1 — versionado del índice y de los embeddings.** `RULE-004` es `active` y su enforcement
llega en `WRK-TASK-036`, dos releases después. Mientras tanto la salvaguarda es una frase en el
README. En el código, `ensure_collection` retorna en cuanto la colección existe: cambiar
`embedding_model` en `.env` por otro modelo de la misma dimensión escribe vectores incompatibles en
la colección existente sin ningún error, y la consulta devuelve resultados plausibles y erróneos.
Los componentes del fingerprint están además dispersos e invisibles: los prefijos `passage:` y
`query:` viven dentro de `SentenceTransformerEmbedder`, `chunk_tokens` y `chunk_overlap` son
enteros en `Settings`, y la versión del extractor no existe como concepto.

**Riesgo 2 — compatibilidad del corpus sintético.** Los gold sets se resuelven contra
`relative_path`, `locator` y `section` (`evaluation.py`, `_matches_evidence`). Cualquier cambio en
extracción o chunking desplaza los locators y convierte un cambio de pipeline en una caída de
`recall_at_k` indistinguible de una regresión de calidad. `benchmark.py` ya verifica un manifiesto
con `_verify_manifest`, que es la base correcta pero cubre el corpus, no la relación entre corpus,
gold set y fingerprint. `v1.1.0` agrava el problema: OCR, tablas e imágenes cambian el contenido
extraído del propio corpus.

**Riesgo 3 — coste del gate `public-safety` con conectores corporativos.** El gate actual es una
denylist de rutas más una búsqueda de patrones sobre ficheros candidatos de Git. Para una PoC con
`local_folder` es barato y eficaz. Con conectores corporativos (`WRK-TASK-018`, `050`, `051`) el
riesgo se desplaza fuera de su alcance: a logs, trazas, atributos de span, fixtures y grabaciones
de peticiones, respuestas de error y volcados de depuración. Un gate sobre ficheros versionados no
ve nada de eso.

Y hay un problema inmediato, no futuro: `scripts/check-public-safety.ps1` contiene en claro, dentro
de un repositorio público, la lista de identificadores corporativos derivados que su patrón
«identificador derivado conocido» busca. El control publica exactamente aquello de lo que protege,
y la lista crece con cada hallazgo. La estrategia de denylist es autodestructiva a medio plazo.

## Options Considered

**Para el riesgo 1:** (a) mantener el enforcement en `v1.1.0` y confiar en la disciplina del
operador; (b) enforcement mínimo inmediato —persistir el fingerprint y rechazar la escritura o la
consulta ante discrepancia— dejando alias, validación previa y ventana de rollback para
`WRK-TASK-036`; (c) adelantar `WRK-TASK-036` entera.

**Para el riesgo 2:** (a) versionar sólo el corpus; (b) versionar corpus y gold set de forma
conjunta y exigir que todo informe de evaluación declare `corpus_version` e `index_fingerprint`,
rechazando comparaciones entre versiones distintas; (c) congelar el corpus, que hace inviable
`v1.1.0`.

**Para el riesgo 3:** (a) ampliar la denylist con cada conector nuevo; (b) mantener el gate de Git
como está y añadir controles de naturaleza distinta para el contenido en tránsito, sacando la lista
de identificadores del repositorio; (c) sustituir el gate por revisión manual.

## Decision

**Riesgo 1: opción (b), enforcement mínimo inmediato.** `IndexFingerprint` se materializa como
objeto de valor en `rag_docs.contracts` (`ADR-RAG-010`), se persiste asociado a la colección y se
comprueba antes de escribir **y** antes de consultar. Ante discrepancia se falla con un error
explícito de la taxonomía, nunca se degrada. El nombre físico de colección pasa a derivar del
fingerprint y el nombre lógico configurado (`qdrant_collection`) se convierte en alias.
`WRK-TASK-036` conserva la migración con validación previa, cambio atómico de alias y ventana de
rollback. La comprobación es de pocas decenas de líneas y elimina hoy una clase entera de resultados
silenciosamente erróneos.

**Riesgo 2: opción (b), versionado conjunto y comparabilidad explícita.** Se extiende el manifiesto
que ya valida `benchmark.py` para que cubra corpus, gold sets y su compatibilidad declarada con un
rango de fingerprints. Todo informe de evaluación y de benchmark registra `corpus_version`,
`index_fingerprint` y el snapshot de configuración efectiva (`ADR-RAG-008`). Comparar dos informes
con tripletas distintas exige una declaración explícita de re-baseline y no puede presentarse como
regresión ni como mejora. `v1.1.0` publica un corpus `v2` con material multimodal y **conserva el
`v1`** como serie de regresión, en lugar de mutarlo.

**Riesgo 3: opción (b), dos controles de naturaleza distinta.**

1. El gate de Git se mantiene tal cual —es barato y sigue siendo correcto para su alcance— pero la
   lista de identificadores derivados sale del repositorio a un fichero local o secreto de CI
   cargado por el script, con la lista pública vacía por defecto. El gate deja de publicar aquello
   que protege y deja de crecer sin límite en abierto.
2. Se añade un control estructural sobre el contenido en tránsito, que es donde vive el riesgo real
   con conectores: logging estructurado con allowlist de campos, con test que falla si un logger
   emite un campo no declarado; prohibición de que las respuestas de error de conectores incluyan
   contenido documental; atributos de span sin contenido por defecto, verificado por test
   (invariante ya declarado en `ARCH-002`); y fixtures de conector generados exclusivamente a
   partir del corpus sintético, nunca grabados desde un sistema corporativo real.

El coste de mantener el gate no crece por la vía de la denylist —que es la que se abandona— sino
por la vía de tres o cuatro tests estructurales que se escriben una vez y se aplican a todos los
conectores futuros. Ese coste es aceptable y acotado.

## Consequences

El enforcement inmediato del fingerprint **invalida las colecciones locales existentes**: cualquier
índice construido antes del cambio no tendrá fingerprint persistido y deberá reconstruirse o
marcarse manualmente. Es exactamente el tipo de fricción que el enforcement existe para provocar,
pero conviene anunciarlo.

La política de comparabilidad hará que algunas comparaciones deseadas dejen de ser posibles sin
trabajo extra. Es el resultado buscado: hoy esas comparaciones se hacen y son inválidas sin que
nadie lo note.

Sacar la lista de identificadores del repositorio significa que el gate protege menos en un clon
limpio sin el fichero local. Se compensa haciendo que CI cargue la lista desde secreto y que la
ausencia del fichero sea una advertencia visible, no un fallo silencioso. Hay además un residuo
histórico: los identificadores ya están en el historial de Git público y eliminarlos del `HEAD` no
los borra del historial. Esa valoración corresponde al propietario.

## Work Impact

Aplicado en el grafo KDD:

- Creada `WRK-TASK-092` en `v0.3.0` y colocada como primera tarea sin dependencias internas:
  externalización de los identificadores derivados, advertencia visible ante ausencia del fichero,
  carga desde secreto en CI y decisión sobre el historial registrada en Evidence.
- `WRK-TASK-036` se traslada íntegra a `v0.3.0` con el enforcement incorporado a sus criterios. No
  se divide en `036a`/`036b`: separar fingerprint y alias duplicaría el trabajo de migración.
- Creada `WRK-TASK-086` en `v0.3.0`: manifiesto conjunto de corpus, gold sets y fingerprint, y
  política de comparabilidad en `evaluation.py` y `benchmark.py`.
- Creada `WRK-TASK-087` en `v2.0.0`, dependiente de `092` y `050`: logging con allowlist de campos,
  errores de conector sin contenido, atributos de span sin contenido y fixtures sintéticos, con esos
  criterios heredados por cualquier conector futuro.
- `WRK-SPEC-007` y `WRK-PLAN-007` adoptan la política de corpus aditivo con conservación de la serie
  de regresión.
- `WRK-TASK-014` registra en el informe si el benchmark reutilizó estado persistente.

## Human Checkpoint

**Resuelto el 2026-09-04.** Los identificadores se retiraron del `HEAD` en `WRK-TASK-092` y,
además, el propietario autorizó explícitamente reescribir el historial de Git. Se ejecutó con
`git filter-repo --replace-text` sobre un mirror completo del repositorio (31 commits, 3 refs:
`main`, la rama de esta misma PR y el tag `v0.2.0`), sustituyendo los cinco identificadores por
marcadores `REDACTED_IDENTIFIER_N` en cada blob donde aparecían. Verificado con `git grep` commit a
commit sobre un clon limpio del remoto tras el push: cero coincidencias en todo el historial
público. El *push* a `main` requirió desactivar temporalmente "Do not allow force pushes" en la
protección de rama, ejecutado por el propietario; la protección se restaura después de este merge.
Residuo aceptado y explícito: cualquier fork o clon hecho antes de esta reescritura conserva los
commits antiguos con los identificadores en claro; no hay manera de revocar eso retroactivamente,
sólo de no perpetuarlo desde este punto en adelante.

**PARAR antes de `WRK-TASK-087`** para confirmar con el propietario del dato qué se considera
publicable en logs y trazas de un conector corporativo. La política de allowlist de campos es una
decisión de gobierno del dato, no una preferencia técnica.
