---
id: WRK-TASK-073
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-PLAN-011
activates: [ARCH-002, FEAT-RAG-003, DOC-RAG-002, RULE-002, RULE-003]
dependencies:
  - id: WRK-TASK-070
    relation: depends-on
  - id: WRK-TASK-071
    relation: depends-on
  - id: WRK-TASK-072
    relation: depends-on
tags: [rbac, network-policy, pod-security, certificates]
---

# WRK-TASK-073 — Seguridad Kubernetes

## Objective

Aplicar ServiceAccounts, RBAC, NetworkPolicies, Pod Security y certificados internos.

## Acceptance Criteria

- [ ] Cada workload usa una identidad y permisos mínimos.
- [ ] Red deny-by-default permite sólo flujos documentados.
- [ ] Pods cumplen perfil restringido viable y root filesystem protegido.
- [ ] Servicios rechazan tokens o certificados no autorizados.

## Evidence

Pendiente.
