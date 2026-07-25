**Paso a paso para correr lo del robot que  se conecta a drive por console.cloud**

# INDAGATA - Guia de arranque completa (desde cero)

Sigue estos pasos EN ORDEN. No te saltes ninguno la primera vez.

---

## 1. Clonar el repositorio

```powershell
cd C:\proyectos
git clone https://github.com/yareeli21/clean_standarization_RAG.git
cd clean_standarization_RAG
git checkout feature/interfaz-base
git pull origin feature/interfaz-base
```

## 2. Crear y activar tu entorno virtual (EN LA RAIZ del proyecto)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Si te marca error de permisos:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

Confirma que tu terminal diga `(.venv) PS C:\proyectos\clean_standarization_RAG>`
- sin `interfaz\` en la ruta. Si lo ves ahi, es el venv equivocado.

## 3. Instalar todas las dependencias

```powershell
pip install -r requirements.txt
```

## 4. Levantar PostgreSQL con Docker

```powershell
cd docker
docker compose up -d
cd ..
```

Esto crea **tu propia** base de datos local, con la estructura y los
KPIs de ejemplo que ya vienen escritos en `sql/init.sql`.

**Importante sobre cómo funciona esta sincronización:** `init.sql`
SOLO se ejecuta la primera vez que Docker crea el volumen de la base de
datos. Si alguien del equipo agrega un KPI nuevo directo a `init.sql` y
hace `git push`, el resto del equipo necesita hacer `git pull` **y**
forzar que Docker recree su base de datos para que el cambio se refleje:

```powershell
cd docker
docker compose down -v
docker compose up -d
cd ..
```

El `-v` borra el volumen viejo y obliga a que `init.sql` se ejecute
de nuevo completo. Sin este paso, aunque tengas el archivo actualizado,
tu base de datos local sigue con los datos viejos.

**Esta estrategia sirve bien para catálogos que el equipo controla a
mano (como la lista de KPIs), pero NO sincroniza nada que la app genere
sola con el uso diario** (instrumentos subidos, historial de chats del
RAG, etc.) - eso sigue siendo local y aislado por computadora hasta que
en algún momento se centralice la base de datos en la nube.

## 5. Pide, por WhatsApp (nunca por git), estos 2 archivos y 3 datos:

**Archivo 1:** `oauth_credentials.json` -> colocalo exactamente en:
```
interfaz\backend\core\oauth_credentials.json
```

**Archivo 2:** confirma que tu `.env` (en la raiz del proyecto) tenga
todo esto:

```
DB_HOST=localhost
DB_PORT=5433
DB_NAME=aprende_rag
DB_USER=aprende
DB_PASSWORD=aprende123

GOOGLE_DRIVE_FOLDER_ENCUESTAS=<lo del .env>
GOOGLE_DRIVE_FOLDER_ENTREVISTAS=<lo del .env>
GOOGLE_DRIVE_FOLDER_PRUEBAS=<lo del .env>

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
```

**Dato 3:** pedir que agregue tu correo de Gmail a la lista de
"Usuarios de prueba" en Google Cloud Console - sin esto, cuando
intentes iniciar sesion mas adelante te va a salir "Acceso bloqueado". Pero no debería pasar porque todos vamos a entrar con el de tetoragembedding@gmail.com

## 6. Ollama - OPCIONAL por ahora, no lo necesitas para empezar

Ollama solo hace falta para la burbuja de chat que pide metadatos
justo despues de subir un instrumento. Esa función existe en el código
pero **el prompt específico de qué preguntar todavía no está definido**,
así que por ahora no es indispensable tenerlo corriendo.

**Si no tienes Ollama activo:** todo lo demás funciona normal (subir,
ver, previsualizar, eliminar instrumentos). Solo si abres la burbuja de
metadatos y escribes algo, te va a salir un mensaje de error tipo "no
se pudo contactar al modelo" - no rompe el resto de la app, simplemente
esa parte específica no responde.

**Cuando sí quieran usarlo** (una vez que cada uno defina las preguntas de
metadatos por tipo de instrumento):
```powershell
ollama pull llama3.1
ollama serve
```
Se deja corriendo en una terminal aparte mientras se usa la app.

## 7. Crear tu propia rama de trabajo

```powershell
git checkout -b feature/pantalla-login-kpis
```
(Arturo usa en su lugar: `git checkout -b feature/pantalla-chat-ia`)

**Nunca trabajes directo sobre `feature/interfaz-base`** - esa es la
base compartida, cada quien avanza en la suya y luego se integra por
Pull Request.

## 8. Correr el proyecto

```powershell
cd interfaz
python index.py
```

Esto abre tu navegador solo, en `http://127.0.0.1:8000`.

## 9. La PRIMERA vez que subas un archivo en la pantalla "Cargar"

Se va a abrir tu navegador pidiendote iniciar sesion con Google -
**usa la cuenta compartida del equipo**, no tu cuenta personal. Acepta
los permisos que te pida. Despues de esta primera vez, tu computadora
recuerda la sesion sola (se crea un archivo `token.json`, automatico,
no lo tocas) y no te vuelve a pedir iniciar sesion.

**Si te sale "Acceso bloqueado: INDAGATA no completo verificacion"** ->
avisar, falta agregar tu correo a usuarios de prueba (paso 5).

---

## Que SI puedes hacer

- Subir instrumentos -> se guardan en la carpeta de Drive compartida
  segun su tipo (Encuestas / Entrevistas / Pruebas estandarizadas)
- Ver en "Datasets originales" TODO lo que existe en Drive en ese
  momento, aunque lo haya subido otro integrante - se revisa en vivo
  cada vez que abres la pantalla
- Previsualizar el contenido de un CSV directo en la interfaz (clic en
  la tarjeta del dataset)
- Ver en "Tus instrumentos cargados" solo lo que TU subiste
- Eliminar solo tus propios instrumentos (se borran de Drive y de tu
  base de datos local a la vez)
- Ver los mismos KPIs de catalogo que el resto del equipo, siempre y
  cuando todos tengan el `init.sql` actualizado y hayan recreado su
  base de datos tras el ultimo cambio (ver paso 4)

## Que NO puedes hacer (y por que)

- **No ves KPIs que otro integrante haya agregado directo a su propia
  base de datos** sin pasar por `init.sql` + `git push` + que tu
  recrees tu volumen de Docker - no hay sincronizacion automatica
- **No puedes eliminar instrumentos que subio otro integrante** - el
  boton de eliminar solo existe para lo que esta en tu propia BD
- **No hay estado de procesamiento completo de instrumentos ajenos** -
  solo ves su nombre, tipo y fecha (tomado de Drive), no su historial
  completo de limpieza/estandarizacion
- **El chat de metadatos no responde si no tienes Ollama corriendo** -
  y aun si lo tienes, las preguntas que hace todavia son genericas,
  falta definir el prompt especifico por tipo de instrumento

Todo esto se resolveria centralizando PostgreSQL en un servicio en la
nube (por ejemplo Supabase) en una fase posterior - por ahora, para el
prototipo, cada quien trabaja con su copia local y Drive es lo unico
verdaderamente compartido en tiempo real.

---

## Errores comunes y su solucion

**"ModuleNotFoundError: No module named 'psycopg'"**
-> `pip install "psycopg[binary]"` - nota los corchetes, no es lo
mismo que `psycopg2-binary`.

**"ModuleNotFoundError" de cualquier otra libreria**
-> Confirma que tu venv este activado (`Get-Command python` debe
apuntar a `...\clean_standarization_RAG\.venv\Scripts\python.exe`, no
a otra ruta), luego `pip install -r requirements.txt` de nuevo.

**Los archivos de `interfaz/` desaparecieron de tu carpeta**
-> Estas en otra rama. Revisa con `git branch` (el asterisco marca en
cual estas) y regresa con `git checkout feature/interfaz-base` o a tu
propia rama de pantalla.

**Cambiaste codigo pero no ves el cambio en el navegador**
-> `Ctrl + C` para detener el servidor, y `python index.py` de nuevo.
Refrescar el navegador no basta para cambios en archivos `.py`.

**"Acceso bloqueado: INDAGATA no completo el proceso de verificacion"**
-> Tu correo no esta en la lista de usuarios de prueba en Google
Cloud. Pedir que te agregue.

**No ves los archivos que subio un companero**
-> Revisa el panel "Datasets originales" (no "Tus instrumentos
cargados") - solo ese panel consulta Drive en vivo.

**Error al previsualizar un archivo ("no se pudo obtener")**
-> Confirma que tu `oauth_credentials.json` este en su lugar y que ya
completaste el login por navegador al menos una vez.

**El chat de metadatos dice "no se pudo contactar al modelo"**
-> Es normal si no tienes Ollama corriendo. No afecta nada mas de la
app; esa funcion esta pendiente de definirse por completo.