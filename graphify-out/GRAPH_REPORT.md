# Graph Report - .  (2026-07-23)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 114 nodes · 132 edges · 35 communities (34 shown, 1 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4d9f17eb`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- limpieza_encuesta.py
- instrumentos.py
- db.py
- cargar.py
- chat.py
- cargar
- index.py
- rag_service.py

## God Nodes (most connected - your core abstractions)
1. `ejecutar_query()` - 8 edges
2. `fase_automatica()` - 8 edges
3. `main()` - 8 edges
4. `ejecutar_comando()` - 6 edges
5. `_obtener_instrumentos()` - 5 edges
6. `cargar()` - 5 edges
7. `fase_asistida()` - 5 edges
8. `procesar_carga()` - 4 edges
9. `buscar_instrumentos()` - 4 edges
10. `procesar_login()` - 4 edges

## Surprising Connections (you probably didn't know these)
- `_obtener_instrumentos()` --calls--> `ejecutar_query()`  [EXTRACTED]
  interfaz/backend/routers/instrumentos.py → interfaz/backend/core/db.py
- `ver_catalogo_kpis()` --calls--> `ejecutar_query()`  [EXTRACTED]
  interfaz/backend/routers/kpis.py → interfaz/backend/core/db.py
- `procesar_login()` --calls--> `ejecutar_query()`  [EXTRACTED]
  interfaz/backend/routers/login.py → interfaz/backend/core/db.py
- `procesar_carga()` --calls--> `ejecutar_comando()`  [EXTRACTED]
  interfaz/backend/routers/cargar.py → interfaz/backend/core/db.py
- `crear_usuario()` --calls--> `ejecutar_comando()`  [EXTRACTED]
  interfaz/backend/scripts/crear_usuario.py → interfaz/backend/core/db.py

## Import Cycles
- None detected.

## Communities (35 total, 1 thin omitted)

### Community 0 - "limpieza_encuesta.py"
Cohesion: 0.12
Nodes (24): calcular_calidad(), capitalizacion_controlada(), construir_perfil_para_llm(), detectar_plataforma(), _es_num(), exportar(), fase_asistida(), fase_automatica() (+16 more)

### Community 1 - "instrumentos.py"
Cohesion: 0.20
Nodes (10): Configuración central de la interfaz. Aquí se definen rutas base y settings que, Entrypoint de la interfaz web (FastAPI + Jinja2).  Para correr en desarrollo,, buscar_instrumentos(), _obtener_instrumentos(), _preparar_instrumentos(), Request, Router: Catálogo de instrumentos Responsable de esta pantalla: Yare  Ya conec, Agrega campos derivados: tipo legible, slug para CSS y código de catálogo. (+2 more)

### Community 2 - "db.py"
Cohesion: 0.23
Nodes (10): ejecutar_query(), obtener_conexion(), Regresa una conexion nueva a PostgreSQL., Ejecuta un SELECT y regresa una lista de dicts.     Si la base de datos aun no, verificar_password(), Request, ver_catalogo_kpis(), procesar_login() (+2 more)

### Community 3 - "cargar.py"
Cohesion: 0.24
Nodes (9): ejecutar_comando(), Ejecuta un INSERT/UPDATE/DELETE. Regresa True si se ejecuto bien., hashear_password(), procesar_carga(), Request, Router: Cargar instrumento Responsable de esta pantalla: [asignar integrante], ver_formulario_carga(), crear_usuario() (+1 more)

### Community 4 - "chat.py"
Cohesion: 0.29
Nodes (7): BaseModel, consultar_rag(), ConsultaRequest, Request, Router: Chat de IA (consulta RAG)  Responsable de esta pantalla: [asignar inte, # TODO: reemplazar por llamada real a rag_backend.rag_service.consultar(...), ver_chat_ia()

### Community 5 - "cargar"
Cohesion: 0.33
Nodes (7): cargar(), _leer_csv(), _leer_excel(), _limpiar_nombre_col(), Lee el archivo y devuelve (headers, filas_como_strings)., Detecta encoding y separador con estrategia robusta., Elimina saltos de línea, espacios múltiples, espacios al inicio/fin     y corri

### Community 6 - "index.py"
Cohesion: 0.50
Nodes (3): abrir_navegador(), Punto de entrada único de la interfaz.  Uso: desde interfaz/, en PowerShell:, Espera un momento a que el servidor arranque y abre el navegador.

## Knowledge Gaps
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ejecutar_query()` connect `db.py` to `instrumentos.py`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Why does `ejecutar_comando()` connect `cargar.py` to `db.py`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **Should `limpieza_encuesta.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12 - nodes in this community are weakly interconnected._