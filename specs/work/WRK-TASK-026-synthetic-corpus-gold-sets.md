---
id: WRK-TASK-026
type: spec
layer: work-task
scope: ephemeral
status: archived
confidence: medium
version: 1.0.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-PLAN-005
activates: [DOM-RAG-001, FEAT-RAG-001, DOC-RAG-002, RULE-002]
dependencies:
  - id: WRK-TASK-024
    relation: depends-on
  - id: WRK-TASK-079
    relation: depends-on
  - id: WRK-TASK-080
    relation: depends-on
tags: [corpus, evaluation, synthetic, gold-set]
---

# WRK-TASK-026 — Corpus y gold sets sintéticos

## Objective

Ampliar un corpus multiformato completamente sintético y separar preguntas de desarrollo y
validación para evitar ajuste al test.

## File Scope

Incluye `examples/corpus/demo/**`, `evaluation/**`, el generador de corpus, sus tests y la
documentación estrictamente necesaria. Excluye retrieval, generación, modelos reales y datos
locales ignorados. No cambia contratos runtime ni requiere `src/**`.

## Dataset Contract

Los archivos canónicos serán `evaluation/gold-set.dev.yaml` y
`evaluation/gold-set.validation.yaml`. Ambos declaran en raíz `schema_version`, `corpus_version`,
`split` y `cases`. Cada caso declara como mínimo:

- `id`, `category`, `question`, `expected_status` y `expected_language`;
- `target_fact_ids` estables para detectar contaminación entre splits;
- `required_facts` para casos grounded;
- `expected_documents` y, cuando proceda, `expected_any_documents` para alternativas
  documentales equivalentes;
- `expected_locators` por documento y `equivalence_group` cuando aplique.

Las categorías mínimas son `single_hop`, `compound` y `negative`. Los negativos usan
`expected_status: insufficient_evidence`, documentos, hechos y localizadores esperados vacíos. El
esquema preserva los campos que consume el evaluador actual; sus metadatos adicionales no cambian
el contrato runtime.

Los localizadores se expresan según los extractores actuales: `page` para PDF, `slide` para PPTX,
`sheet` y `cell_range` para XLSX, `section` y opcionalmente `table` para DOCX, `section` para
Markdown, y ruta documental para TXT. Todos los paths son relativos a
`examples/corpus/demo` y usan `/`.

Cada entrada de `expected_locators` contiene `document` y, según el formato, `locator`, `section`
o ambos. TXT usa sólo `document`, porque su extractor actual produce una unidad documental sin
locator adicional.

## Minimum Coverage Matrix

- Desarrollo contiene al menos 16 casos; validación, al menos 8.
- Cada split referencia los seis formatos PDF, DOCX, PPTX, XLSX, TXT y Markdown.
- Desarrollo contiene al menos 4 `single_hop`, 3 `compound`, 2 `negative` y 2 preguntas no
  españolas; validación contiene al menos 2 de cada categoría y 1 pregunta no española.
- Existen al menos dos `equivalence_group` documentales distintos, uno ejercitado exclusivamente
  en desarrollo y otro exclusivamente en validación.
- Categoría, idioma, formato y equivalencia son dimensiones solapables; los mínimos no tienen que
  sumar el total de casos.

## Split Isolation and Determinism

Los splits no comparten `id`, preguntas normalizadas, `target_fact_ids` ni
`equivalence_group`. Un test automatizado comprueba esas intersecciones, unicidad y esquema; la
Evidence registra además revisión de paráfrasis semánticamente equivalentes.

El generador acepta un directorio de salida y fija orden, timestamps, propiedades de documento,
metadatos ZIP y saltos de línea. `examples/corpus/demo/manifest.sha256` incluye versión del corpus,
versión del esquema y SHA-256 de cada fixture, con paths ordenados; no incluye el propio
manifiesto en el cálculo.

Una prueba genera el corpus en dos directorios temporales independientes y exige el mismo conjunto
de paths y hashes. La generación canónica se contrasta contra el manifiesto y una segunda
ejecución no deja diferencias en Git.

## Acceptance Criteria

- [x] Los gold sets cumplen el esquema versionado y la matriz mínima de 16 casos de desarrollo y
  8 de validación.
- [x] Los splits no comparten IDs, preguntas normalizadas, hechos objetivo, grupos equivalentes ni
  referencias privadas; Evidence confirma revisión semántica de paráfrasis.
- [x] Hay casos single-hop, compuestos, multilingües, negativos y dos grupos documentales
  equivalentes aislados entre splits.
- [x] PDF, DOCX, PPTX, XLSX, TXT y Markdown, junto con sus paths y localizadores soportados, quedan
  representados en ambos splits.
- [x] El manifiesto SHA-256 versionado y dos generaciones en directorios independientes producen
  exactamente los mismos paths y bytes, y la regeneración canónica no ensucia Git.
- [x] `gold-set.yaml` permanece como smoke set compatible hasta la consolidación de `v0.2.0`.

## Suggested Agentic Decomposition

Antes de editar archivos compartidos pueden analizarse en paralelo: inventario y diseño de splits;
normalización determinista de contenedores PDF/Office; y esquema, manifiesto y tests de
contaminación. El agente principal consolida los tres resultados y conserva la implementación e
integración final.

## Evidence

- El corpus `0.2.0` contiene doce fixtures sintéticos: un juego de desarrollo y otro ATLAS de
  validación, ambos con PDF, DOCX, PPTX, XLSX, TXT y Markdown. El manifiesto `schema_version: 1.0`
  enumera sus doce SHA-256 en orden y excluye el propio manifiesto.
- `gold-set.dev.yaml` aporta 16 casos y `gold-set.validation.yaml`, 8. Las pruebas validan esquema,
  mínimos por categoría e idioma, paths permitidos, los seis formatos, localizadores extraídos y
  aislamiento de IDs, preguntas normalizadas, hechos objetivo y grupos equivalentes.
- La revisión semántica confirmó que no hay paráfrasis equivalentes entre splits: desarrollo usa
  únicamente el dominio de ETL de clientes y validación el dominio ATLAS. Las equivalencias
  deliberadas `eq-dev-client-flow` y `eq-val-atlas-restore` permanecen dentro de su split.
- El generador acepta `--output-dir` y `--check`, fija propiedades y timestamps, normaliza miembros
  OOXML y saltos de línea, y usa una allowlist de fixtures. Dos directorios temporales producen los
  mismos 13 paths y bytes; `--check` confirma que el árbol canónico coincide.
- La QA visual inspeccionó las cuatro diapositivas, las cuatro páginas PDF y las tres hojas XLSX;
  se corrigieron anchos truncados y los decks superaron el detector de overflow. LibreOffice no
  estaba disponible para rasterizar DOCX, por lo que se aplicó el fallback estructural: ambos DOCX
  abren y sus secciones/tablas se validan mediante los extractores automatizados.
- Gates locales: 42 tests, Ruff, `git diff --check` y seguridad pública sobre 201 candidatos en
  verde; KDD validó 125 specs y 863 relaciones, cero huérfanos, contexto coherente y lifecycle
  válido. `gold-set.yaml` conserva sus cuatro casos smoke y no se modificó `src/**`.
- La PR `#5` superó `kdd`, `python-quality`, `public-safety`, `dependency-review` y `secret-scan`
  en el run `33553848668` antes del cierre de lifecycle.
