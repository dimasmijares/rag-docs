# Suite de contrato de VectorStore

`test_vector_store_contract.py` define lo que cualquier backend de `VectorStorePort` e
`IndexPublicationPort` debe cumplir (`ADR-RAG-013`, `WRK-TASK-096`): round-trip de chunks,
fingerprint vinculado y rechazo sin vínculo, `prune_document`, prefiltro de ámbito, `update_acl`
sin tocar vectores, `scan_chunks`, publicación y rollback. Solo usa métodos de los puertos.

## Gate por defecto

`scripts/verify.ps1` y CI la ejecutan contra Qdrant `:memory:` (parámetro `qdrant-memory`), sin
Docker ni credenciales.

## Enganche live (opcional)

Para ejecutarla contra un backend real, define `RAG_DOCS_CONTRACT_LIVE_FACTORY` con la forma
`paquete.modulo:factoria`. `factoria(logical_name)` recibe un nombre lógico único por test y devuelve
un store vacío que implementa ambos puertos. La factoría obtiene sus credenciales del entorno de la
persona que la ejecuta; nunca se versionan.

```powershell
$env:RAG_DOCS_CONTRACT_LIVE_FACTORY = 'mi_paquete.backends:contract_store'
uv run --no-sync pytest tests/contract -m live
Remove-Item Env:RAG_DOCS_CONTRACT_LIVE_FACTORY
```

Sin esa variable el parámetro `live` no existe, así que `scripts/verify.ps1` nunca lo ejecuta. El
gate del perfil Fabric (`scripts/verify-fabric.ps1`, `WRK-TASK-100`) es quien lo usará con
`FabricSqlVectorStore`.
