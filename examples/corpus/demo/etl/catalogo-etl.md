# Catálogo de ETL

## ETL_CLIENTES_DIARIA

La ETL `ETL_CLIENTES_DIARIA` carga `CLIENTE_MAESTRO` desde `CRM_ORACLE` cada día a las
02:00. Su definición técnica está en `procesos/clientes/etl_clientes_diaria`.

## ETL_CONTRATOS_SEMANAL

La ETL `ETL_CONTRATOS_SEMANAL` consolida contratos activos cada domingo a las 06:00.

## Gobierno del orquestador

El equipo Plataforma de Datos mantiene `ORQ_DATAOPS` y aprueba sus cambios de calendario.
