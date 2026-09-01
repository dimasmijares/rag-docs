# Repository agent instructions

## KDD source of truth

Treat `specs/**` as the source of truth for objectives, dependencies, scope, acceptance criteria
and Evidence. Follow the canonical iteration protocol in
`specs/documentation/DOC-RAG-002-platform-operations.md`; do not duplicate that protocol in task
prompts or individual WRK-TASK files.

Before selecting work, synchronize `main`, inspect open pull requests, and run KDD `validate`,
`orphans` and `context`. Only select tasks whose dependencies are terminal on `main`.

## Agentic orchestration

Use subagents for bounded, independent workstreams when this reduces wall-clock time without
conflicting edits. Prefer parallel read-only analysis before shared-file implementation. The
primary agent owns synthesis, shared-file edits, integration, validation and the final result.

A singular request to execute the next task completes one ready WRK-TASK. A request to continue
the active release authorizes multiple iterations in series; after every merge, synchronize
`main` and recompute readiness from the DAG.

Independent DAG-ready tasks may run concurrently only when the user authorizes multiple tasks,
their implementation scopes do not overlap, and neither depends directly or transitively on the
other. Use a separate worktree, `codex/wrk-task-NNN-slug` branch and pull request for each task.
Start with at most two concurrent WRK-TASKs. Keep at most one active WRK-TASK in each checkout;
the coordinator owns reconciliation of shared KDD plan files.

Merge concurrent pull requests one at a time. Before merging the next one, update it from the new
`main`, resolve integration drift and rerun all required checks. Never implement a dependent task
until its dependencies are merged and terminal. If dependencies, scopes or integration order are
uncertain, serialize the work.

## Completion

For every task, keep changes inside its declared scope, run proportional tests plus all repository
gates, complete criteria and Evidence, and merge only when required checks are green. Verify the
merge and synchronize `main` before declaring the iteration complete. Record separable discovered
work as a new WRK-TASK instead of silently expanding scope.
