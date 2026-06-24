# clean_standarization_RAG

#Módulo de limpieza y estandarización para la consulta de datos mediante RAG
Trabajo terminal 

#¿Qué es este proyecto?
Sistema para procesar instrumentos de recolección de datos educativos (encuestas, entrevistas y pruebas de estandarización) a través de un pipeline de:

1. **limpieza**: normalización de archivos crudos (el formato depende el tipo de instrumento)
2. **estandarización**: generación de JSON enriqeucido con metadatos 
3. **vectorización**: chunking semántido y carga a ChromaDB
4. **consulta RAG**: respuestas en lenguaje natural sobre los datos 

#Stack tecnológico

componente 

tecnología

versión

Lenguaje: python 3.12.5
API: FastAPI 0.115.0
Base de datos relacional: PostgreSQL 16
Base de datos vectorial: ChromaDB 0.5.23
Embeddings: sentence-transformers 3.2.1
LLM local: Ollama + llama3.2:3b
Evaluación RAG: RAGAS 0.2.6
Contenedores: Docker desktop

#Requisitos previos 

Instalar antes de clonar el proyecto:

- [Python 3.12](https://www.python.org/downloads/release/python-3128/) — marcar con palomita "Add to PATH"
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Ollama](https://ollama.com/download/windows)
- [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) — seleccionar "Desarrollo de escritorio con C++"
- [Git](https://git-scm.com/)

> **Importante:** clonar el proyecto en una ruta **sin acentos ni espacios**,
> por ejemplo `C:\proyectos\`. Rutas como `C:\Users\usuario\Documents\` pueden
> causar errores en psycopg y otras librerías por la codificación de caracteres
> especiales en Windows.

##INSTALACIÓN

### 1. Clonar el repositorio

en powershell poner:

```
git clone https://github.com/yareeli21/clean_standarization_RAG.git
cd clean_standarization_RAG
```


### 2. Crear y activar el entorno virtual

```bash
python -m venv .venv
.venv\Scripts\activate
```

El prompt debe cambiar a `(.venv)` — indica que el entorno está activo.

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copia el archivo de ejemplo y llena tus valores:

```bash
copy .env.example .env
```

Edita `.env` con tus credenciales:

```env
PG_USER=aprende
PG_PASSWORD=tu_contraseña
PG_DB=aprende_rag
PG_HOST=localhost
PG_PORT=5432

CHROMA_PATH=./data/chroma

OLLAMA_URL=http://localhost:11434

EMBEDDING_MODEL=paraphrase-multilingual-mpnet-base-v2
LLM_MODEL=llama3.2:3b
LLM_MODEL_COMPARACION=mistral:latest
```

>El archivo `.env` nunca se sube a GitHub — contiene credenciales privadas.

### 5. Levantar PostgreSQL con Docker

```bash
cd docker
docker compose --env-file ../.env up -d
```

Verificar que el contenedor está corriendo:

```bash
docker ps
```

Debe aparecer `aprende_postgres` con status `healthy`.

### 6. Bajar el modelo LLM con Ollama

```bash
ollama pull llama3.2:3b --insecure
ollama pull mistral:latest --insecure
```
> Si tu red bloquea el registro de Ollama, usa `--insecure` como flag.

---

## Verificar instalación

Abre Jupyter y ejecuta el notebook de prueba de conexiones:

```bash
jupyter notebook
```

Navega a `notebooks/00_test_connections.ipynb` y ejecuta todas las celdas.  

##Estructura del proyecto

clean_standarization_RAG/

├── docker/

│   └── docker-compose.yml       # PostgreSQL en contenedor

├── sql/

│   └── init.sql                 # Esquema de 6 tablas

├── src/

│   ├── cleaning/                # Módulo de limpieza

│   ├── standarization/          # Módulo de estandarización

│   ├── vectorization/           # Chunking semántico + ChromaDB

│   ├── rag/                     # Pipeline de consulta RAG

│   └── api/                     # FastAPI

├── notebooks/

│   └── 00_test_connections.ipynb

├── data/

│   ├── raw/                     # Archivos originales (no versionados)

│   ├── processed/               # JSONs estandarizados (no versionados)

│   └── samples/                 # Datos de prueba

├── tests/

├── .env.example                 # Plantilla de variables de entorno

└── requirements.txt

---

## Colecciones ChromaDB

| Colección | Contenido |
|---|---|
| `col_encuestas` | Chunks de encuestas (ítem-respondente) |
| `col_entrevistas` | Chunks de entrevistas (par pregunta-respuesta) |
| `col_pruebas_estandarizadas` | Chunks de pruebas (sustentante-sección) |

---

## Tablas PostgreSQL

| Tabla | Descripción |
|---|---|
| `instrumento_procesado` | Registro central de instrumentos ingresados |
| `kpi` | Catálogo de indicadores educativos |
| `pregunta_kpi` | Asignación LLM de KPIs a preguntas |
| `prompt` | Catálogo de prompts del pipeline |
| `documento_vectorizado` | Registro de chunks en ChromaDB |
| `rag_log` | Log de consultas RAG |

---

## Notas de implementación

- **Python 3.14 no es compatible** con este stack — usar Python 3.12
- **ChromaDB corre embebido** — no requiere contenedor Docker
- **Ollama corre como servicio de Windows** — no en Docker
- El archivo `.env` debe guardarse **sin BOM** (UTF-8 sin marca de orden de bytes)