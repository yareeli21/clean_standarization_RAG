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
    objetivo     TEXT,
    razon        TEXT,
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

-----------TABLA USUARIOS PARA LA AUTENTICACION DE USUARIO--------------

CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    usuario VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    creado_en TIMESTAMP DEFAULT NOW()
);

-- -- DATOS INICIALES: KPIS BY ADMINISTRATOR(LAYLA) -----------------------

INSERT INTO kpi
(nombre, descripcion, objetivo, razon)
VALUES
(
                        ' Estado de acreditación y clasificaciones',
                        ' El número y el estatus de las acreditaciones, así como la posición que ocupa una institución en las distintas clasificaciones educativas, pueden ser un indicador significativo de su reputación y calidad.',
                        ' Aumentar',
                        ' Una mejor clasificación y un mayor número de acreditaciones mejoran la reputación y la credibilidad.'
                        ),
                        (
                        ' Selectividad de admisión',
                        ' El porcentaje de solicitantes admitidos puede ser un indicador de la reputación y el atractivo de una institución. Una tasa de admisión más baja suele indicar una mayor selectividad.',
                        ' Quédese abajo',
                        ' Una menor tasa de admisión indica una mayor selectividad y prestigio.'
                        ),
                        (
                        ' Tasa de donaciones de exalumnos',
                        ' Para las instituciones de educación superior, la tasa de donaciones de los exalumnos puede ser un indicador de satisfacción mucho después de la graduación y, a menudo, constituye un componente fundamental de los ingresos de la institución.',
                        ' Aumentar',
                        ' Una tasa más alta sugiere satisfacción de los exalumnos y apoyo institucional a largo plazo.'
                        ),
                        (
                        ' Tasas de asistencia',
                        ' Los índices de asistencia pueden ser un indicador temprano del compromiso y la satisfacción de los estudiantes, y también pueden correlacionarse con el éxito académico.',
                        ' Aumentar',
                        'Una mayor asistencia demuestra la implicación y el compromiso de los estudiantes.'
                        ),
                        (
                        ' Tamaño promedio de la clase',
                        ' Este indicador clave de rendimiento (KPI) mide el número promedio de estudiantes por clase, lo que puede indicar el nivel de atención individual que recibe cada estudiante.',
                        ' Quédese abajo',
                        ' Las clases con menos alumnos mejoran la interacción entre estudiantes y profesores, así como la calidad del aprendizaje.'
                        ),
                        (
                        ' Costo promedio de la matrícula',
                        ' El costo promedio de la matrícula puede indicar la posición de mercado del proveedor educativo. Unas tarifas más altas pueden significar una posición de prestigio, pero también pueden limitar el número potencial de estudiantes.',
                        ' Quédese abajo',
                        ' Una matrícula más baja mejora la accesibilidad y la competitividad.'
                        ),
                        (
                        ' Promedio de años para graduarse',
                        ' El tiempo promedio que tarda un estudiante en completar su curso puede indicar la dificultad del programa, su flexibilidad y la capacidad de la institución para facilitar la graduación a tiempo.',
                        ' Disminuir a',
                        ' Reducir la duración de los periodos de graduación mejora la eficiencia y reduce los costes para los estudiantes.'
                        ),
                        (
                        ' Resultados de las pruebas de referencia',
                        'Las puntuaciones medias de los estudiantes en pruebas de referencia como el SAT, el ACT, el GMAT, etc., pueden indicar la capacidad académica del alumnado.',
                        ' Aumentar',
                        ' Las puntuaciones más altas indican un mejor rendimiento académico y una mejor preparación.'
                        ),
                        (
                        ' Estadísticas de seguridad en el campus',
                        ' Las medidas de seguridad en el campus, como la tasa de delincuencia, pueden ser un indicador fundamental del bienestar estudiantil y pueden afectar la reputación de una institución.',
                        ' Quédese abajo',
                        ' Unos índices de delincuencia más bajos crean un entorno de aprendizaje más seguro.'
                        ),
                        (
                        ' Relación entre consejero y estudiante',
                        ' Este indicador clave de rendimiento (KPI) en las escuelas, especialmente en el nivel de secundaria, puede indicar el nivel de apoyo disponible para los estudiantes en lo que respecta a la planificación académica, las solicitudes de ingreso a la universidad y los problemas socioemocionales.',
                        ' Quédese abajo',
                        ' Una menor proporción de alumnos por alumno garantiza un mejor apoyo y orientación para los estudiantes.'
                        ),
                        (
                        ' Tasa de finalización de cursos (educación en línea)',
                        ' Al igual que la tasa de abandono, este indicador clave de rendimiento (KPI) es especialmente relevante para los proveedores de educación en línea. Mide el porcentaje de estudiantes que completan un curso en línea en comparación con el número total de estudiantes matriculados.',
                        ' Aumentar',
                        'Una tasa más alta refleja la participación de los estudiantes y la eficacia del programa.'
                        ),
                        (
                        ' Índice de matriculación/finalización de cursos',
                        ' El número de estudiantes que completan un curso en comparación con los que se inscribieron. Un índice alto podría indicar que el contenido del curso es atractivo, el nivel de dificultad es adecuado y el curso aporta valor a los estudiantes.',
                        ' Aumentar',
                        ' Un índice alto indica un contenido del curso eficaz y una buena perseverancia por parte de los estudiantes.'
                        ),
                        (
                        ' Tasas de impago de préstamos estudiantiles',
                        ' Una tasa más baja indica que los graduados de la institución suelen ser financieramente estables después de graduarse, lo que repercute positivamente en el valor de la educación recibida.',
                        ' Disminuir a',
                        ' Las bajas tasas de impago reflejan la estabilidad financiera de los graduados.'
                        ),
                        (
                        ' Métricas de diversidad',
                        ' Los indicadores de diversidad de estudiantes y profesorado, como la raza, el género, la nacionalidad, etc., pueden reflejar la inclusividad de una institución y su atractivo para un amplio espectro demográfico.',
                        ' Aumentar',
                        ' Una mayor diversidad fomenta la inclusión y un entorno de aprendizaje más enriquecedor.'
                        ),
                        (
                        ' Tasa de abandono',
                        'Esta métrica representa el porcentaje de estudiantes que abandonan el programa antes de finalizarlo. Una alta tasa de abandono podría indicar insatisfacción con el programa, dificultades con los cursos u otros problemas institucionales.',
                        ' Disminuir a',
                        ' Un menor índice de abandono escolar indica una mejor retención y apoyo a los estudiantes.'
                        ),
                        (
                        ' Tamaño de la dotación',
                        ' Para muchas instituciones de educación superior, el tamaño de su patrimonio puede ser un indicador clave de su salud financiera y sostenibilidad.',
                        ' Aumentar',
                        ' Un mayor patrimonio fortalece la sostenibilidad financiera.'
                        ),
                        (
                        ' Actividades extracurriculares',
                        ' El número y la variedad de actividades extracurriculares disponibles para los estudiantes pueden indicar el compromiso de la institución con la educación integral y la participación estudiantil.',
                        ' Aumentar',
                        ' Una mayor variedad de actividades mejora la vida estudiantil y fomenta la participación.'
                        ),
                        (
                        ' Tasa de publicación del profesorado',
                        'Para las instituciones de educación superior e investigación, la frecuencia con la que los miembros del profesorado publican artículos de investigación en revistas de prestigio puede ser una medida importante del rigor académico y el enfoque de investigación de la institución.',
                        ' Aumentar',
                        ' Un mayor número de publicaciones mejora la reputación de la institución en materia de investigación.'
                        ),
                        (
                        ' Cualificación del profesorado y tasa de rotación',
                        ' La calidad del profesorado desempeña un papel fundamental en el éxito de cualquier institución educativa. Una menor rotación de personal, junto con una mayor cualificación del profesorado, puede ser un indicador de la buena salud de la institución.',
                        ' Aumentar / Disminuir a',
                        ' Una mayor cualificación mejora la calidad de la enseñanza; una menor rotación de personal garantiza la estabilidad.'
                        ),
                        (
                        ' Resultados de la investigación del profesorado',
                        ' La cantidad y la calidad de los artículos académicos y otros resultados de investigación del profesorado pueden indicar el calibre intelectual y el prestigio de una institución, particularmente en la educación superior.',
                        ' Aumentar',
                        ' Una mayor producción científica mejora el prestigio institucional.'
                        ),
                        (
                        ' Tasa de graduación',
                        'El porcentaje de estudiantes que completan sus estudios en un plazo determinado. Una alta tasa de graduación puede indicar un plan de estudios sólido y métodos de enseñanza eficaces.',
                        ' Aumentar',
                        ' Una tasa más alta refleja la eficacia del programa y el éxito de los estudiantes.'
                        ),
                        (
                        ' Colaboraciones con la industria y oportunidades de prácticas profesionales',
                        ' El número de acuerdos de colaboración con la industria y de prácticas profesionales puede indicar las oportunidades prácticas que se ofrecen a los estudiantes y la integración de la institución con el sector industrial.',
                        ' Aumentar',
                        ' Un mayor número de colaboraciones mejora la preparación para el empleo y las conexiones con la industria.'
                        ),
                        (
                        ' Gasto en instrucción por estudiante equivalente a tiempo completo (ETC)',
                        ' Este indicador clave de rendimiento (KPI) permite comprender cuánto invierte una institución en sus servicios de enseñanza por estudiante, lo que puede ser una señal de la calidad educativa.',
                        ' Aumentar',
                        ' Un mayor gasto por alumno indica una mejor asignación de recursos.'
                        ),
                        (
                        ' Tasa de colocación laboral',
                        'Para muchas instituciones educativas, especialmente las de formación profesional y superior, un indicador clave de éxito es el porcentaje de graduados que consiguen empleo en su campo de estudio dentro de un plazo determinado después de graduarse.',
                        ' Aumentar',
                        ' Los mayores índices de colocación laboral reflejan el éxito profesional de los graduados.'
                        ),
                        (
                        ' Métricas de participación del alumno (para plataformas en línea)',
                        ' Esto podría incluir medidas como la duración promedio de la sesión, la tasa de rebote, las páginas por sesión, etc. Un mayor nivel de interacción suele ser una señal positiva.',
                        ' Aumentar',
                        ' Una mayor participación se traduce en una mejor experiencia de aprendizaje.'
                        ),
                        (
                        ' Recursos de la biblioteca',
                        ' La cantidad y la calidad de los recursos disponibles en la biblioteca de la institución, incluidos libros, artículos de investigación y recursos digitales, pueden ser un indicador del apoyo a la excelencia académica.',
                        ' Aumentar',
                        ' Una biblioteca con una colección más rica favorece el éxito académico.'
                        ),
                        (
                        ' Valor de por vida de un estudiante',
                        ' Este indicador clave de rendimiento (KPI) ayuda a comprender los ingresos totales que genera un estudiante promedio a lo largo de su relación con la institución.',
                        ' Aumentar',
                        'Un mayor valor mejora la salud financiera institucional.'
                        ),
                        (
                        ' Número de programas acreditados',
                        ' El número de programas que han sido acreditados por los organismos pertinentes puede ser un indicador de la calidad de la institución y de su adhesión a los estándares académicos.',
                        ' Aumentar',
                        ' Un mayor número de programas acreditados aumenta la credibilidad.'
                        ),
                        (
                        ' Número de cursos/programas ofrecidos',
                        ' La variedad de programas educativos que ofrece una institución puede ser un indicio de su adaptabilidad y de su capacidad para atender a un alumnado diverso.',
                        ' Aumentar',
                        ' La diversidad de la oferta académica atrae a más estudiantes.'
                        ),
                        (
                        ' Relación entre la matrícula en línea y la matrícula presencial',
                        ' Ante la creciente tendencia del aprendizaje digital, especialmente tras la pandemia de Covid-19, es importante analizar la capacidad de la empresa para atraer y retener a estudiantes en línea.',
                        ' Aumentar',
                        ' El creciente número de inscripciones en línea refleja adaptabilidad y alcance.'
                        ),
                        (
                        ' Acuerdos de asociación',
                        'Este indicador clave de rendimiento (KPI) mide la cantidad de acuerdos que una institución educativa tiene con otras instituciones o empresas. Esto puede ser un signo de reconocimiento y demanda de los servicios que ofrece la institución.',
                        ' Aumentar',
                        ' Un mayor número de acuerdos fomenta la colaboración y mejora la reputación.'
                        ),
                        (
                        ' Tasa de aprobación de los exámenes de certificación',
                        ' Para las instituciones que ofrecen cursos que conducen a certificaciones profesionales, el índice de aprobados puede ser una medida significativa de la eficacia de sus programas.',
                        ' Mantenerse arriba',
                        ' Un índice de aprobación consistentemente alto indica la eficacia del programa.'
                        ),
                        (
                        ' Patentes concedidas',
                        ' Para las instituciones de investigación, el número de patentes concedidas es una medida importante de su productividad investigadora y su capacidad de innovación.',
                        ' Aumentar',
                        ' Un mayor número de patentes pone de relieve la innovación y el impacto de la investigación.'
                        ),
                        (
                        ' Porcentaje de profesorado con título de posgrado',
                        ' Este indicador clave de rendimiento (KPI) muestra la proporción de profesores con el título más alto en su campo (como un doctorado). Un porcentaje más alto puede ser un indicador de la calidad del profesorado.',
                        ' Aumentar',
                        'Un profesorado más cualificado mejora la calidad académica.'
                        ),
                        (
                        ' Porcentaje de estudiantes a tiempo parcial',
                        ' La proporción de estudiantes que estudian a tiempo parcial puede ofrecer información valiosa sobre la flexibilidad de los programas de la institución y la composición demográfica de su alumnado.',
                        ' Quédese abajo',
                        ' Un porcentaje menor puede indicar una preferencia por la dedicación a tiempo completo.'
                        ),
                        (
                        ' Porcentaje de estudiantes que reciben ayuda financiera',
                        ' Esto puede indicar la accesibilidad de la institución para estudiantes de diversos estratos socioeconómicos.',
                        ' Aumentar',
                        ' Una mayor ayuda mejora el acceso y la asequibilidad.'
                        ),
                        (
                        ' Tasa de estudios de posgrado',
                        ' La tasa de graduados que continúan sus estudios. Este puede ser un indicador clave para las instituciones que ofrecen programas preuniversitarios o de formación básica.',
                        ' Aumentar',
                        ' Una tasa más alta indica un sólido progreso académico.'
                        ),
                        (
                        ' Oportunidades de desarrollo profesional para el profesorado',
                        'El grado de oportunidades para el desarrollo profesional del profesorado, como años sabáticos, conferencias, becas de investigación, etc., puede indicar la calidad y la satisfacción del profesorado, lo que afecta indirectamente a los resultados de los estudiantes.',
                        ' Aumentar',
                        ' Ofrecer más oportunidades mejora el desarrollo y la retención del profesorado.'
                        ),
                        (
                        ' Tasa de incidentes disciplinarios',
                        ' Este indicador clave de rendimiento (KPI) mide el número de incidentes disciplinarios reportados en relación con el total del alumnado. Un índice elevado puede indicar problemas con la cultura o la gestión del campus.',
                        ' Disminuir a',
                        ' Un menor número de incidentes indica un entorno más seguro en el campus.'
                        ),
                        (
                        ' Proporción de estudiantes nacionales e internacionales',
                        ' Este indicador clave de rendimiento (KPI) muestra la capacidad de una institución para atraer estudiantes extranjeros, lo que puede diversificar las fuentes de ingresos y mejorar la reputación de la institución.',
                        ' Balance',
                        ' Una combinación equilibrada garantiza la diversidad y la competitividad global.'
                        ),
                        (
                        ' Financiación y subvenciones para la investigación',
                        'Este indicador clave de rendimiento (KPI), de particular importancia para la educación superior, representa la cantidad de financiación que una institución recibe para la investigación. Indica la capacidad investigadora y la reputación de la institución.',
                        ' Aumentar',
                        ' Una mayor financiación fortalece las capacidades de investigación.'
                        ),
                        (
                        ' Ingresos procedentes de la formación continua',
                        ' Para las instituciones que ofrecen formación continua, los ingresos derivados de estos programas pueden ser un indicador de su capacidad para atraer y satisfacer las necesidades de los estudiantes no tradicionales o de aquellos que buscan formación a lo largo de toda la vida.',
                        ' Aumentar',
                        ' Un mayor nivel de ingresos refleja una demanda de aprendizaje permanente.'
                        ),
                        (
                        ' Ingresos por licencias y patentes',
                        ' Para las universidades centradas en la investigación, los ingresos derivados de la concesión de licencias de los resultados de la investigación o de las patentes pueden ser una fuente de ingresos importante y un indicador de la solidez investigadora de la institución.',
                        ' Aumentar',
                        ' Unos mayores ingresos favorecen la comercialización de la investigación.'
                        ),
                        (
                        ' Ingresos por estudiante',
                        'Esto indica el ingreso promedio generado por cada estudiante. Ayuda a evaluar la efectividad de la estrategia de precios de una empresa y el valor general que los estudiantes obtienen de los servicios educativos.',
                        ' Aumentar',
                        ' Un valor más alto indica eficiencia financiera.'
                        ),
                        (
                        ' Número de estudiantes matriculados',
                        ' Esto representa el número de estudiantes matriculados en una institución o programa. Es un indicador clave de la demanda de los productos o servicios de una empresa y tiene un impacto directo en su potencial de ingresos.',
                        ' Aumentar',
                        ' Un mayor número de estudiantes indica crecimiento institucional y demanda.'
                        ),
                        (
                        ' Disponibilidad de alojamiento para estudiantes',
                        ' En las instituciones tradicionales con campus, el número de estudiantes que pueden alojarse en las residencias universitarias puede indicar la capacidad de la institución y su habilidad para atraer estudiantes residentes.',
                        ' Aumentar',
                        ' Más opciones de vivienda facilitan la vida estudiantil en el campus.'
                        ),
                        (
                        ' Uso de los servicios de salud mental estudiantil',
                        'La frecuencia con la que los estudiantes utilizan los servicios de salud mental puede ofrecer información valiosa sobre el bienestar del alumnado y la eficacia de los servicios de apoyo de la institución.',
                        ' Balance',
                        ' Un uso moderado garantiza que los servicios estén disponibles, pero sin sobrecargarlos.'
                        ),
                        (
                        ' Tasa de retención estudiantil',
                        ' El porcentaje de estudiantes que se renuevan de un semestre a otro. Una alta tasa de retención puede indicar la capacidad de una empresa para brindar una educación de calidad y una buena satisfacción estudiantil, lo que puede generar una sólida reputación y un aumento en la matrícula futura.',
                        ' Mantenerse arriba',
                        ' Una alta tasa de retención refleja una gran satisfacción estudiantil.'
                        ),
                        (
                        ' Índices de satisfacción estudiantil',
                        ' Estas puntuaciones, que suelen obtenerse mediante encuestas, miden la satisfacción general de los estudiantes con su experiencia educativa. Esto puede abarcar aspectos como el contenido de los cursos, la calidad de la enseñanza, los servicios de apoyo y las instalaciones del campus.',
                        ' Mantenerse arriba',
                        ' Las puntuaciones altas indican experiencias positivas por parte de los estudiantes.'
                        ),
                        (
                        ' Servicios de apoyo estudiantil',
                        'La variedad y la calidad de los servicios de apoyo al estudiante, como la orientación profesional, las tutorías, los servicios de salud mental, etc., pueden ser un indicador importante de la satisfacción estudiantil y del apoyo institucional en general.',
                        ' Aumentar',
                        ' Una mayor oferta de servicios mejora el éxito académico y el bienestar de los estudiantes.'
                        ),
                        (
                        ' Relación alumno-profesor',
                        ' Esta métrica permite evaluar la calidad de la educación impartida. Un índice menor puede significar una atención más personalizada para los estudiantes, lo que se traduce en mejores resultados de aprendizaje.',
                        ' Quédese abajo',
                        ' Una menor proporción de alumnos por clase mejora la atención individual de cada estudiante.'
                        ),
                        (
                        ' Tasa de participación en programas de estudios en el extranjero',
                        ' El índice de participación de los estudiantes en programas de estudios en el extranjero puede ser un indicador de las alianzas globales de la institución y de la amplitud de su experiencia educativa.',
                        ' Aumentar',
                        ' Una mayor participación refleja oportunidades de aprendizaje a nivel global.'
                        ),
                        (
                        ' Tipos de transferencia',
                        ' Para los colegios comunitarios e instituciones similares, un indicador clave de éxito es la tasa de estudiantes que se transfieren a instituciones de cuatro años.',
                        ' Disminuir a',
                        'Las tasas más bajas sugieren que los estudiantes están completando sus programas en sus instituciones de origen.'
                        ),
                        (
                        ' Uso de analítica del aprendizaje',
                        ' El grado en que una institución utiliza datos y análisis para mejorar la enseñanza y el aprendizaje puede ser un indicador de su innovación y dedicación al éxito académico.',
                        ' Aumentar',
                        ' Un mayor uso de la analítica mejora la toma de decisiones basada en datos.'
                        ),
                        (
                        ' Crecimiento interanual en las admisiones',
                        ' Este indicador clave de rendimiento (KPI) mide la variación interanual en las admisiones de nuevos estudiantes. Un crecimiento rápido puede indicar una creciente demanda de la oferta educativa de la empresa.',
                        ' Aumentar',
                        ' El crecimiento constante indica una creciente demanda y una mejor reputación.'
                        ),
                        (
                        ' Tasas de asistencia',
                        ' Los índices de asistencia pueden ser un indicador temprano del compromiso y la satisfacción de los estudiantes, y también pueden correlacionarse con el éxito académico.',
                        ' Aumentar',
                        'Una mayor asistencia demuestra la implicación y el compromiso de los estudiantes.'
                        ),
                        (
                        ' Tamaño promedio de la clase',
                        ' Este indicador clave de rendimiento (KPI) mide el número promedio de estudiantes por clase, lo que puede indicar el nivel de atención individual que recibe cada estudiante.',
                        ' Quédese abajo',
                        ' Las clases con menos alumnos mejoran la interacción entre estudiantes y profesores, así como la calidad del aprendizaje.'
                        ),
                        (
                        ' Estadísticas de seguridad en el campus',
                        ' Las medidas de seguridad en el campus, como la tasa de delincuencia, pueden ser un indicador fundamental del bienestar estudiantil y pueden afectar la reputación de una institución.',
                        ' Quédese abajo',
                        ' Unos índices de delincuencia más bajos crean un entorno de aprendizaje más seguro.'
                        ),
                        (
                        ' Índice de matriculación/finalización de cursos',
                        ' El número de estudiantes que completan un curso en comparación con los que se inscribieron. Un índice alto podría indicar que el contenido del curso es atractivo, el nivel de dificultad es adecuado y el curso aporta valor a los estudiantes.',
                        ' Aumentar',
                        ' Un índice alto indica un contenido del curso eficaz y una buena perseverancia por parte de los estudiantes.'
                        ),
                        (
                        ' Métricas de diversidad',
                        ' Los indicadores de diversidad de estudiantes y profesorado, como la raza, el género, la nacionalidad, etc., pueden reflejar la inclusividad de una institución y su atractivo para un amplio espectro demográfico.',
                        ' Aumentar',
                        ' Una mayor diversidad fomenta la inclusión y un entorno de aprendizaje más enriquecedor.'
                        ),
                        (
                        ' Tasa de abandono',
                        'Esta métrica representa el porcentaje de estudiantes que abandonan el programa antes de finalizarlo. Una alta tasa de abandono podría indicar insatisfacción con el programa, dificultades con los cursos u otros problemas institucionales.',
                        ' Disminuir a',
                        ' Un menor índice de abandono escolar indica una mejor retención y apoyo a los estudiantes.'
                        ),
                        (
                        ' Actividades extracurriculares',
                        ' El número y la variedad de actividades extracurriculares disponibles para los estudiantes pueden indicar el compromiso de la institución con la educación integral y la participación estudiantil.',
                        ' Aumentar',
                        ' Una mayor variedad de actividades mejora la vida estudiantil y fomenta la participación.'
                        ),
                        (
                        ' Tasa de graduación',
                        'El porcentaje de estudiantes que completan sus estudios en un plazo determinado. Una alta tasa de graduación puede indicar un plan de estudios sólido y métodos de enseñanza eficaces.',
                        ' Aumentar',
                        ' Una tasa más alta refleja la eficacia del programa y el éxito de los estudiantes.'
                        ),
                        (
                        ' Colaboraciones con la industria y oportunidades de prácticas profesionales',
                        ' El número de acuerdos de colaboración con la industria y de prácticas profesionales puede indicar las oportunidades prácticas que se ofrecen a los estudiantes y la integración de la institución con el sector industrial.',
                        ' Aumentar',
                        ' Un mayor número de colaboraciones mejora la preparación para el empleo y las conexiones con la industria.'
                        ),
                        (
                        ' Tasa de colocación laboral',
                        'Para muchas instituciones educativas, especialmente las de formación profesional y superior, un indicador clave de éxito es el porcentaje de graduados que consiguen empleo en su campo de estudio dentro de un plazo determinado después de graduarse.',
                        ' Aumentar',
                        ' Los mayores índices de colocación laboral reflejan el éxito profesional de los graduados.'
                        ),
                        (
                        ' Recursos de la biblioteca',
                        ' La cantidad y la calidad de los recursos disponibles en la biblioteca de la institución, incluidos libros, artículos de investigación y recursos digitales, pueden ser un indicador del apoyo a la excelencia académica.',
                        ' Aumentar',
                        ' Una biblioteca con una colección más rica favorece el éxito académico.'
                        ),
                        (
                        ' Número de cursos/programas ofrecidos',
                        ' La variedad de programas educativos que ofrece una institución puede ser un indicio de su adaptabilidad y de su capacidad para atender a un alumnado diverso.',
                        ' Aumentar',
                        ' La diversidad de la oferta académica atrae a más estudiantes.'
                        ),
                        (
                        ' Porcentaje de profesorado con título de posgrado',
                        ' Este indicador clave de rendimiento (KPI) muestra la proporción de profesores con el título más alto en su campo (como un doctorado). Un porcentaje más alto puede ser un indicador de la calidad del profesorado.',
                        ' Aumentar',
                        'Un profesorado más cualificado mejora la calidad académica.'
                        ),
                        (
                        ' Porcentaje de estudiantes que reciben ayuda financiera',
                        ' Esto puede indicar la accesibilidad de la institución para estudiantes de diversos estratos socioeconómicos.',
                        ' Aumentar',
                        ' Una mayor ayuda mejora el acceso y la asequibilidad.'
                        ),
                        (
                        ' Tasa de estudios de posgrado',
                        ' La tasa de graduados que continúan sus estudios. Este puede ser un indicador clave para las instituciones que ofrecen programas preuniversitarios o de formación básica.',
                        ' Aumentar',
                        ' Una tasa más alta indica un sólido progreso académico.'
                        ),
                        (
                        ' Oportunidades de desarrollo profesional para el profesorado',
                        'El grado de oportunidades para el desarrollo profesional del profesorado, como años sabáticos, conferencias, becas de investigación, etc., puede indicar la calidad y la satisfacción del profesorado, lo que afecta indirectamente a los resultados de los estudiantes.',
                        ' Aumentar',
                        ' Ofrecer más oportunidades mejora el desarrollo y la retención del profesorado.'
                        ),
                        (
                        ' Tasa de incidentes disciplinarios',
                        ' Este indicador clave de rendimiento (KPI) mide el número de incidentes disciplinarios reportados en relación con el total del alumnado. Un índice elevado puede indicar problemas con la cultura o la gestión del campus.',
                        ' Disminuir a',
                        ' Un menor número de incidentes indica un entorno más seguro en el campus.'
                        ),
                        (
                        ' Proporción de estudiantes nacionales e internacionales',
                        ' Este indicador clave de rendimiento (KPI) muestra la capacidad de una institución para atraer estudiantes extranjeros, lo que puede diversificar las fuentes de ingresos y mejorar la reputación de la institución.',
                        ' Balance',
                        ' Una combinación equilibrada garantiza la diversidad y la competitividad global.'
                        ),
                        (
                        ' Número de estudiantes matriculados',
                        ' Esto representa el número de estudiantes matriculados en una institución o programa. Es un indicador clave de la demanda de los productos o servicios de una empresa y tiene un impacto directo en su potencial de ingresos.',
                        ' Aumentar',
                        ' Un mayor número de estudiantes indica crecimiento institucional y demanda.'
                        ),
                        (
                        ' Uso de los servicios de salud mental estudiantil',
                        'La frecuencia con la que los estudiantes utilizan los servicios de salud mental puede ofrecer información valiosa sobre el bienestar del alumnado y la eficacia de los servicios de apoyo de la institución.',
                        ' Balance',
                        ' Un uso moderado garantiza que los servicios estén disponibles, pero sin sobrecargarlos.'
                        ),
                        (
                        ' Índices de satisfacción estudiantil',
                        ' Estas puntuaciones, que suelen obtenerse mediante encuestas, miden la satisfacción general de los estudiantes con su experiencia educativa. Esto puede abarcar aspectos como el contenido de los cursos, la calidad de la enseñanza, los servicios de apoyo y las instalaciones del campus.',
                        ' Mantenerse arriba',
                        ' Las puntuaciones altas indican experiencias positivas por parte de los estudiantes.'
                        ),
                        (
                        ' Servicios de apoyo estudiantil',
                        'La variedad y la calidad de los servicios de apoyo al estudiante, como la orientación profesional, las tutorías, los servicios de salud mental, etc., pueden ser un indicador importante de la satisfacción estudiantil y del apoyo institucional en general.',
                        ' Aumentar',
                        ' Una mayor oferta de servicios mejora el éxito académico y el bienestar de los estudiantes.'
                        ),
                        (
                        ' Relación alumno-profesor',
                        ' Esta métrica permite evaluar la calidad de la educación impartida. Un índice menor puede significar una atención más personalizada para los estudiantes, lo que se traduce en mejores resultados de aprendizaje.',
                        ' Quédese abajo',
                        ' Una menor proporción de alumnos por clase mejora la atención individual de cada estudiante.'
                        ),
                        (
                        ' Crecimiento interanual en las admisiones',
                        ' Este indicador clave de rendimiento (KPI) mide la variación interanual en las admisiones de nuevos estudiantes. Un crecimiento rápido puede indicar una creciente demanda de la oferta educativa de la empresa.',
                        ' Aumentar',
                        ' El crecimiento constante indica una creciente demanda y una mejor reputación.'
                        );


INSERT INTO USUARIOS 
(usuario, password_hash )
VALUES
('admin','\$2b\$12\$Tv4.xxi0qVZPSGSVNjFvUOzXA2O1Kw7wJtvAYYlHU9UZwzdjholbm');


ALTER TABLE instrumento_procesado
ADD COLUMN IF NOT EXISTS usuario_id INTEGER REFERENCES usuarios(id);

