-- ============================================================
-- Aprende RAG - Esquema PostgreSQL
-- Registro operativo del pipeline de limpieza,
-- estandarizacion y consulta basado en RAG
-- ============================================================

-- -- GRUPO 1: Gestion de instrumentos ------------------------

CREATE TABLE IF NOT EXISTS instrumento_procesado (
    id                  SERIAL PRIMARY KEY,
    nombre              VARCHAR(255) NOT NULL,
    plataforma          VARCHAR(100),
    ruta_crudo          TEXT,
    ruta_json           TEXT,
    ruta_sav            TEXT,
    hash_md5            VARCHAR(32) UNIQUE,
    metadatos           JSONB,
    estado              VARCHAR(50) DEFAULT 'ingresado',
    -- estados: ingresado, limpio, estandarizado, vectorizado
    fecha_procesamiento TIMESTAMP DEFAULT NOW()
);

-- -- GRUPO 2: Catalogo de indicadores ------------------------

CREATE TABLE IF NOT EXISTS kpi (
    id           SERIAL PRIMARY KEY,
    nombre       VARCHAR(255) NOT NULL,
    descripcion  TEXT,
    formula      TEXT,
    umbral_bajo  NUMERIC,
    umbral_medio NUMERIC,
    umbral_alto  NUMERIC,
    unidad       VARCHAR(50),
    activo       BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS pregunta_kpi (
    id               SERIAL PRIMARY KEY,
    instrumento_id   INTEGER REFERENCES instrumento_procesado(id),
    kpi_id           INTEGER REFERENCES kpi(id),
    id_variable      VARCHAR(50),
    -- identificador de la pregunta en el instrumento (ej. P_01)
    score_inferencia NUMERIC(4,3),
    -- confianza del LLM en la asignacion (0.000 a 1.000)
    fecha            TIMESTAMP DEFAULT NOW()
);

-- -- GRUPO 3: Catalogo de prompts ----------------------------

CREATE TABLE IF NOT EXISTS prompt (
    id        SERIAL PRIMARY KEY,
    tipo      VARCHAR(100) NOT NULL,
    -- chunking, metadatos, kpi_inferencia, query, contextualizacion
    version   VARCHAR(20),
    contenido TEXT NOT NULL,
    fecha     TIMESTAMP DEFAULT NOW(),
    activo    BOOLEAN DEFAULT TRUE
);

-- -- GRUPO 4: Vectorizacion y consulta -----------------------

CREATE TABLE IF NOT EXISTS documento_vectorizado (
    id                  SERIAL PRIMARY KEY,
    instrumento_id      INTEGER REFERENCES instrumento_procesado(id),
    prompt_id           INTEGER REFERENCES prompt(id),
    -- version del prompt que genero este chunk
    vector_id           VARCHAR(255),
    -- ID del punto en ChromaDB
    col_id              VARCHAR(100),
    -- coleccion ChromaDB: col_encuestas, col_entrevistas, col_pruebas_estandarizadas
    tipo_chunk          VARCHAR(100),
    -- resumen_instrumento, unidad_semantica
    activo              BOOLEAN DEFAULT TRUE,
    fecha_vectorizacion TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rag_log (
    id               SERIAL PRIMARY KEY,
    pregunta         TEXT NOT NULL,
    contexto         TEXT,
    -- chunks recuperados enviados al LLM como contexto
    respuesta        TEXT,
    modelo_llm       VARCHAR(100),
    modelo_embedding VARCHAR(100),
    latencia_ms      INTEGER,
    fecha            TIMESTAMP DEFAULT NOW()
);
