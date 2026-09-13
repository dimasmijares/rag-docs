---
id: ADR-RAG-014
type: adr
layer: adr
scope: persistent
status: accepted
confidence: medium
version: 1.0.0
created: 2026-09-13
updated: 2026-09-13
owner: rag-docs-team
dependencies:
  - id: RFC-004
    relation: constrained-by
  - id: ADR-RAG-008
    relation: extends
  - id: ADR-RAG-013
    relation: depends-on
  - id: ARCH-002
    relation: implements
  - id: RULE-001
    relation: constrained-by
  - id: RULE-002
    relation: constrained-by
tags: [architecture-decision, fabric, inference, queue, security, evaluation]
---

# ADR-RAG-014 — Inferencia local para Fabric mediante modelo pull

## Context

`RFC-004` mantiene el LLM en el equipo local (Ollama sobre GPU doméstica) y prohíbe APIs de pago.
Algunas cargas batch de Fabric necesitan ese LLM. Los notebooks de Fabric no pueden usar el
on-premises data gateway, de modo que la única forma de que Fabric *llame* al equipo es exponer un
endpoint local a Internet. Activator, además, puede emitir eventos duplicados.

## Options Considered

1. **Tailscale Funnel**: expone un puerto local públicamente; superficie de ataque abierta y
   dependencia de un tercero en la ruta de datos.
2. **Cloudflare Tunnel con Access**: mitiga el acceso, pero sigue siendo un endpoint entrante y
   añade cuenta, configuración y secretos de un tercero.
3. **ngrok**: equivalente a (1), con URLs efímeras y límites de plan gratuito.
4. **VPN con managed private endpoint**: requiere recursos Azure de pago y red gestionada.
5. **Modelo pull**: Fabric encola peticiones en una tabla y un worker local sólo saliente las reclama.

## Decision

**Opción 5, modelo pull.**

- Fabric escribe peticiones en una tabla de cola en la SQL database del perfil (`ADR-RAG-013`).
- Un worker local, autenticado como service principal de Entra ID con mínimo privilegio, reclama
  peticiones con lease (`UPDLOCK, READPAST`), llama a Ollama y escribe el resultado. Cero puertos
  entrantes.
- Idempotencia por effect-key (mismo principio que `ADR-RAG-008`): reclamar dos veces la misma
  petición produce un único resultado.
- Timeout de visibilidad, reintentos con backoff, tope explícito y dead-letter con motivo estructurado.
- El worker se arranca sólo durante una ventana batch, para acotar consumo de capacidad (CU) y del
  equipo local.
- Ni logs ni métricas incluyen contenido documental, prompts ni respuestas.

**Usos autorizados** (cualquier otro requiere nuevo ADR):

- *Enriquecimiento contextual*: cabeceras de contexto generadas por el LLM que sólo alimentan el
  embedding, en columna separada; nunca se citan como evidencia (`RULE-001`) y su versión forma
  parte del fingerprint.
- *LLM-as-judge*: puntuación batch de respuestas del benchmark, que complementa y nunca sustituye las
  métricas deterministas.
- *Candidatos de gold set*: preguntas candidatas con revisión humana obligatoria antes de entrar en
  un gold set y guardia contra fuga entre `dev` y `validation`.

## Consequences

- La latencia de estas cargas es de minutos, no interactiva; ninguna consulta de usuario pasa por la
  cola.
- El equipo local debe estar encendido durante la ventana batch; si no lo está, las peticiones
  esperan o llegan a dead-letter sin corromper estado.
- La cola necesita su propia suite de contrato ejecutable sin infraestructura.
- El service principal requiere que el tenant habilite el uso de APIs de Fabric por service
  principals; la habilitación la hace una persona administradora, nunca un agente.

## Work Impact

Crear en `WRK-PLAN-014`: `WRK-TASK-110` (cola y worker), `111` (enriquecimiento), `112`
(LLM-as-judge) y `113` (candidatos de gold set).
