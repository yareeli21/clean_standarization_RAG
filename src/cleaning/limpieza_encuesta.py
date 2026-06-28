
import sys, os, re, json, csv, hashlib, io
from datetime import datetime
from collections import defaultdict

try:
    import pandas as pd
    PANDAS_OK = True
except ImportError:
    PANDAS_OK = False


# ─── Configuración de plataformas ─────────────────────────────────────────────

# Columnas de sesión: coincidencia EXACTA sobre nombre normalizado (strip + lower)
# para evitar que "id" matchee con "actividad"
SESION_EXACTA = {
    "google": {
        "marca temporal", "timestamp", "correo electrónico",
        "dirección de correo electrónico", "email address", "email",
    },
    "microsoft": {
        "hora de inicio", "hora de finalización", "hora de completado",
        "start time", "completion time", "correo electrónico",
        "email", "name", "nombre", "id",
    },
    "limesurvey": {
        "submitdate", "id", "lastpage", "startlanguage", "seed",
        "id de respuesta", "última página", "lenguaje inicial",
        "semilla", "datestamp", "ipaddr", "refurl",
        "response id", "date submitted", "last page",
        "start language", "date started", "date last action",
    },
}

# Señales heurísticas para detectar plataforma (más allá de columnas de sesión)
SENALES_PLATAFORMA = {
    "google":      ["marca temporal", "timestamp"],
    "microsoft":   ["hora de inicio", "hora de finalización", "id"],
    "limesurvey":  ["submitdate", "seed", "lastpage", "response id", "date submitted"],
}

TRADUCCIONES_BASICAS = {
    "yes": "Sí", "no": "No", "y": "Sí", "n": "No",
}

# ─── UTILIDADES DE NORMALIZACIÓN ─────────────────────────────────────────────

def registrar_transformacion(metricas, fila, columna,
                             transformacion,
                             valor_original,
                             valor_nuevo):

    if valor_original == valor_nuevo:
        return

    metricas["trazabilidad"].append({
        "fila": fila,
        "columna": columna,
        "transformacion": transformacion,
        "antes": valor_original,
        "despues": valor_nuevo
    })


def normalizar_texto_basico(texto: str) -> str:
    """
    Normalización léxica superficial:
      · elimina saltos
      · colapsa espacios múltiples
      · trim
    """

    if not texto:
        return texto

    texto = texto.replace("\n", " ")
    texto = texto.replace("\r", " ")

    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def capitalizacion_controlada(texto: str) -> str:
    """
    Capitaliza preservando siglas.
    """

    if not texto:
        return texto

    palabras = texto.split()

    resultado = []

    for p in palabras:

        # preservar siglas/acrónimos
        if p.isupper() and len(p) <= 5:
            resultado.append(p)

        else:
            resultado.append(
                p[:1].upper() + p[1:].lower()
            )

    return " ".join(resultado)
# ─── INGESTA ──────────────────────────────────────────────────────────────────

def cargar(ruta: str) -> tuple[list[str], list[list[str]]]:
    """Lee el archivo y devuelve (headers, filas_como_strings)."""
    ext = os.path.splitext(ruta)[1].lower()
    if ext in (".xlsx", ".xls", ".ods"):
        return _leer_excel(ruta, ext)
    return _leer_csv(ruta)


def _leer_excel(ruta: str, ext: str) -> tuple[list[str], list[list[str]]]:
    if not PANDAS_OK:
        raise ImportError("Instala: pip install pandas openpyxl xlrd")
    engine = {".xlsx": "openpyxl", ".xls": "xlrd", ".ods": "odf"}.get(ext, "openpyxl")
    df = pd.read_excel(ruta, engine=engine, dtype=str)
    df.columns = [_limpiar_nombre_col(str(c)) for c in df.columns]
    nulos = {"nan", "nat", "none", "<na>"}
    filas = [
        [("" if str(v).lower() in nulos else str(v).strip()) for v in row]
        for _, row in df.iterrows()
    ]
    return list(df.columns), filas


def _leer_csv(ruta: str) -> tuple[list[str], list[list[str]]]:
    """Detecta encoding y separador con estrategia robusta."""
    raw = None
    for enc in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
        try:
            with open(ruta, "r", encoding=enc, errors="replace") as f:
                raw = f.read()
            break
        except Exception:
            continue
    if raw is None:
        raise IOError(f"No se pudo leer '{ruta}'")

    raw = raw.replace("\r\n", "\n").replace("\r", "\n")

    # Estrategia 1: CSV estándar RFC-4180
    for sep in [",", ";", "\t", "|"]:
        try:
            reader = csv.reader(io.StringIO(raw), delimiter=sep)
            rows = list(reader)
            if len(rows) >= 2:
                n = len(rows[0])
                if n > 1 and sum(1 for r in rows[1:] if len(r) == n) / max(len(rows)-1, 1) > 0.7:
                    headers = [_limpiar_nombre_col(h) for h in rows[0]]
                    filas = [[v.strip() for v in r] for r in rows[1:] if any(v.strip() for v in r)]
                    return headers, filas
        except Exception:
            continue

    # Estrategia 2: filas envueltas en comillas externas (tipo performance.csv)
    lineas = [l for l in raw.split("\n") if l.strip()]
    sep = max([",", ";", "\t", "|"], key=lambda s: lineas[0].count(s))

    def desenvolver(linea: str) -> list[str]:
        if linea.startswith('"') and linea.endswith('"'):
            linea = linea[1:-1]
        linea = linea.replace('""', "\x01")
        partes = linea.split(sep)
        return [p.replace("\x01", "").strip() for p in partes]

    headers = [_limpiar_nombre_col(h) for h in desenvolver(lineas[0])]
    n = len(headers)
    filas = []
    for l in lineas[1:]:
        fila = desenvolver(l)
        if len(fila) >= n:
            filas.append(fila[:n])
        else:
            filas.append(fila + [""] * (n - len(fila)))
    return headers, filas


def _limpiar_nombre_col(nombre: str) -> str:
    """Elimina saltos de línea, espacios múltiples, espacios al inicio/fin
    y corrige encoding de caracteres especiales comunes en Windows."""
    nombre = nombre.replace("\n", " ").replace("\r", " ")
    nombre = re.sub(r"[ \t]+", " ", nombre)
    # Corregir caracteres mal codificados frecuentes en exports Windows
    reemplazos = {
        "Ã¡": "á", "Ã©": "é", "Ã­": "í", "Ã³": "ó", "Ãº": "ú",
        "Ã±": "ñ", "Ã\x81": "Á", "Ã\x89": "É", "Ã\x8d": "Í",
        "Ã\x93": "Ó", "Ã\x9a": "Ú", "Ã\x91": "Ñ",
        "â€™": "'", "â€œ": '"', "â€": '"', "Â¿": "¿", "Â¡": "¡",
    }
    for mal, bien in reemplazos.items():
        nombre = nombre.replace(mal, bien)
    return nombre.strip()


# ─── DETECCIÓN DE PLATAFORMA ──────────────────────────────────────────────────

def detectar_plataforma(headers: list[str]) -> str:
    """
    Devuelve la plataforma más probable basada en coincidencias exactas
    de nombres de columna normalizados.
    """
    hl = {h.lower().strip() for h in headers}
    puntos = {}
    for plat, cols_sesion in SESION_EXACTA.items():
        puntos[plat] = sum(1 for c in cols_sesion if c in hl)
    # Bonus por señales específicas
    for plat, senales in SENALES_PLATAFORMA.items():
        for s in senales:
            if s in hl:
                puntos[plat] = puntos.get(plat, 0) + 2

    mejor = max(puntos, key=lambda k: puntos[k])
    return mejor if puntos[mejor] > 0 else "otro"


# ─── FASE AUTOMÁTICA ──────────────────────────────────────────────────────────

def fase_automatica(
    headers: list[str], filas: list[list[str]],
    plataforma: str, log: list
) -> tuple[list[str], list[list[str]], dict]:
    """
    Aplica todas las transformaciones deterministas sin intervención del investigador.
    """
    metricas = {
        "n_original": len(filas),
        "n_columnas_original": len(headers),
        "transformaciones": defaultdict(int),
        "tipos": {},
        "nulos": {},
        "duplicados": [],
        "imposibles": [],
        "trazabilidad": [],
    }
    filas = [list(f) for f in filas]

    # A1: Eliminar columnas de sesión de la plataforma detectada
    sesion_cols = SESION_EXACTA.get(plataforma, set())
    elim = [i for i, h in enumerate(headers) if h.lower().strip() in sesion_cols]
    if elim:
        log.append(f"[A1] Columnas de sesión eliminadas: {[headers[i] for i in elim]}")
        headers = [h for i, h in enumerate(headers) if i not in set(elim)]
        filas = [[v for i, v in enumerate(f) if i not in set(elim)] for f in filas]

    # A2: LimeSurvey — Y/N → Sí/No
    if plataforma == "limesurvey":
        cnt = 0
        for j in range(len(headers)):
            vals = {f[j].strip().upper() for f in filas if f[j].strip()}
            if vals and vals <= {"Y", "N"}:
                for f in filas:
                    v = f[j].strip().upper()
                    if v == "Y": f[j] = "Sí"; cnt += 1
                    elif v == "N": f[j] = "No"; cnt += 1
        if cnt: log.append(f"[A2] Y/N → Sí/No: {cnt} celdas")

        # Detectar grupos de opción múltiple por patrón col[opcion]
        # Agrupa columnas que comparten el mismo prefijo antes del [
        grupos_om = {}
        for h in headers:
            m = re.match(r'^(.+?)\[(.+)\]$', h)
            if m:
                prefijo = m.group(1).strip()
                grupos_om.setdefault(prefijo, []).append(h)
        if grupos_om:
            n_grupos = len(grupos_om)
            log.append(f"[A2b] LimeSurvey — {n_grupos} grupo(s) de opción múltiple detectados: "
                       f"{list(grupos_om.keys())[:5]}")
            metricas["grupos_opcion_multiple_limesurvey"] = {
                k: v for k, v in grupos_om.items()
            }

    # A3: Traducción inglés→español (para plataformas fuera del español o "otro")
    if plataforma in ("limesurvey", "otro"):
        cnt = 0
        for f in filas:
            for j, v in enumerate(f):
                trad = TRADUCCIONES_BASICAS.get(v.lower().strip())
                if trad: f[j] = trad; cnt += 1
        if cnt: log.append(f"[A3] Traducción en→es: {cnt} valores")

    # A4: Capitalización y espacios residuales en valores
# A4: Normalización textual básica + capitalización controlada
    cnt = 0

    for i, f in enumerate(filas):

        for j, v in enumerate(f):

            original = v

            # limpieza superficial
            v2 = normalizar_texto_basico(v)

            # capitalización solo en texto
            if v2 and not _es_num(v2):
                v2 = capitalizacion_controlada(v2)

            if v2 != original:

                registrar_transformacion(
                    metricas,
                    fila=i,
                    columna=headers[j],
                    transformacion="normalizacion_textual",
                    valor_original=original,
                    valor_nuevo=v2
                )

                cnt += 1

            f[j] = v2

    metricas["transformaciones"]["normalizacion_textual"] = cnt

    log.append(
        f"[A4] Normalización textual: {cnt} celdas ajustadas"
    )

    # A5: Inferencia de tipos
    tipos = {}
    for j, col in enumerate(headers):
        vals = [f[j] for f in filas if f[j].strip()]
        tipos[col] = _inferir_tipo(vals)
    metricas["tipos"] = tipos
    log.append(f"[A5] Tipos inferidos para {len(tipos)} columnas")

    # A6: Normalizar decimales coma→punto en numéricas/escala
    cnt = 0
    for j, col in enumerate(headers):
        if tipos[col] in ("numerica", "escala"):
            for f in filas:
                if "," in f[j] and _es_num(f[j].replace(",", ".")):
                    f[j] = f[j].replace(",", "."); cnt += 1
    if cnt: log.append(f"[A6] Decimales normalizados: {cnt}")

    # A7: Clasificar nulos
    # A7: Clasificación heurística de nulos
    for j, col in enumerate(headers):

        tot = len(filas)

        n_null = sum(
            1 for f in filas
            if not f[j].strip()
        )

        pct = round(
            n_null / tot * 100, 2
        ) if tot else 0

        if n_null == 0:
            tipo_null = "ninguno"

        elif pct < 5:
            tipo_null = "esporadico"

        elif pct >= 50:
            tipo_null = "posiblemente_condicional"

        else:
            tipo_null = "persistente"

        metricas["nulos"][col] = {
            "n": n_null,
            "pct": pct,
            "tipo": tipo_null
        }
    n_cols_nulos = sum(1 for d in metricas["nulos"].values() if d["n"] > 0)
    log.append(f"[A7] Nulos: {n_cols_nulos} columnas con al menos un nulo")

    # A8: Duplicados exactos
    hashes: dict = {}
    for i, f in enumerate(filas):
        h = hashlib.md5("|".join(f).encode()).hexdigest()
        if h in hashes: metricas["duplicados"].append((hashes[h], i))
        else: hashes[h] = i
    log.append(f"[A8] Duplicados exactos: {len(metricas['duplicados'])} pares")

    # A9: Valores imposibles en numéricas/escala
# A9: Valores imposibles y atípicos
    for j, col in enumerate(headers):

        if tipos[col] not in (
            "numerica",
            "calificacion",
            "escala"
        ):
            continue

        nums_idx = []

        for i, f in enumerate(filas):

            if f[j].strip():

                try:
                    nums_idx.append(
                        (i, float(f[j].replace(",", ".")))
                    )

                except ValueError:
                    pass

        if len(nums_idx) < 5:
            continue

        nums = [v for _, v in nums_idx]

        media = sum(nums) / len(nums)

        std = (
            sum((x - media) ** 2 for x in nums)
            / len(nums)
        ) ** 0.5

        minv = min(nums)
        maxv = max(nums)

        for i, v in nums_idx:

            razon = None

            if v < 0 and minv >= 0:

                razon = (
                    f"Valor negativo inesperado ({v})"
                )

            elif std > 0 and abs(v - media) > 4 * std:

                razon = (
                    f"Valor atípico extremo ±4σ: "
                    f"{v} (μ={media:.2f}, σ={std:.2f})"
                )

            if razon:

                metricas["imposibles"].append({
                    "fila": i,
                    "col": col,
                    "valor": v,
                    "razon": razon,
                    "media": round(media, 2),
                    "desviacion_estandar": round(std, 2),
                    "rango": [minv, maxv]
                })

    log.append(
        f"[A9] Valores imposibles/atípicos: "
        f"{len(metricas['imposibles'])}"
    )

    return headers, filas, metricas
def _inferir_tipo(vals: list[str]) -> str:

    if not vals:
        return "texto_libre"

    vals_limpios = [
        v.strip()
        for v in vals
        if v.strip()
    ]

    # Binaria
    unicos_lower = {
        v.lower()
        for v in vals_limpios
    }

    if unicos_lower <= {
        "sí", "si", "no",
        "yes", "y", "n",
        "verdadero", "falso",
        "true", "false"
    }:
        return "binaria"

    # Numéricas
    try:

        nums = [
            float(v.replace(",", "."))
            for v in vals_limpios
        ]

        rango = max(nums) - min(nums)
        unicos = len(set(nums))

        # Escala lineal
        if (
            all(n == int(n) for n in nums)
            and unicos <= 10
            and max(nums) <= 10
            and rango <= 10
        ):
            return "escala"

        # Calificación
        if min(nums) >= 0 and max(nums) <= 100:
            return "calificacion"

        return "numerica"

    except ValueError:
        pass

    # Fecha
    patrones_fecha = 0

    for v in vals_limpios[:50]:

        if re.match(r"^\d{4}-\d{2}-\d{2}", v):
            patrones_fecha += 1

        elif re.match(r"^\d{1,2}/\d{1,2}/\d{2,4}$", v):
            patrones_fecha += 1

    if len(vals_limpios) > 0:

        if patrones_fecha / len(vals_limpios[:50]) >= 0.7:
            return "fecha"

    # Categórica
    cardinalidad = len(set(vals_limpios))

    if 3 <= cardinalidad <= 15:
        return "categorica"

    # Texto corto/largo
    promedio = (
        sum(len(v) for v in vals_limpios)
        / len(vals_limpios)
    )

    if promedio < 60:
        return "texto_corto"

    return "texto_largo"


def _es_num(v: str) -> bool:
    try: float(v.replace(",", ".")); return True
    except (ValueError, AttributeError): return False


# ─── MÉTRICAS DE CALIDAD ──────────────────────────────────────────────────────

def calcular_calidad(metricas: dict, headers: list[str], filas: list[list[str]]) -> dict:
    tot = len(filas) * len(headers) if filas and headers else 1
    nulos_tot = sum(d["n"] for d in metricas["nulos"].values())
    return {
        "n_respondentes": len(filas),
        "n_columnas": len(headers),
        "pct_completitud": round((1 - nulos_tot / tot) * 100, 2),
        "pct_nulos": round(nulos_tot / tot * 100, 2),
        "n_duplicados": len(metricas["duplicados"]),
        "n_imposibles": len(metricas["imposibles"]),
        "cols_mas_nulos": sorted(
            [(c, d["pct"]) for c, d in metricas["nulos"].items() if d["n"] > 0],
            key=lambda x: -x[1])[:5],
    }


# ─── REVISIÓN DE COLUMNAS ─────────────────────────────────────────────────────

def revisar_columnas(
    headers: list[str], filas: list[list[str]], log: list
) -> tuple[list[str], list[list[str]], dict]:
    """
    El investigador clasifica cada columna:
      p — pregunta (pasa a estandarización)
      d — dato de contexto (id, folio, etc.) — documentado, no genera chunk
      e — eliminar

    Heurística:
      - Nombre > 25 chars → asumida pregunta sin preguntar
      - Nombre corto/sospechoso → muestra muestra de valores para decidir
    """
    print("\n" + "═"*66)
    print("  REVISIÓN DE COLUMNAS")
    print("═"*66)
    print("  ¿Qué representa cada columna tras la limpieza automática?")
    print("  [p] pregunta  [d] dato de contexto (no es pregunta)  [e] eliminar\n")

    roles: dict[str, str] = {}

    obvias = [h for h in headers if len(h) > 25]
    dudosas = [h for h in headers if len(h) <= 25]

    if obvias:
        print(f"  Columnas marcadas automáticamente como preguntas ({len(obvias)}):")
        for h in obvias:
            print(f"    ✓ {h[:72]}")
            roles[h] = "p"

    if dudosas:
        print(f"\n  Columnas que necesitan clasificación ({len(dudosas)}):\n")
        for h in dudosas:
            j = headers.index(h)
            muestra = sorted({f[j].strip() for f in filas[:20] if f[j].strip()})[:6]
            print(f"  ┌─ Columna: {h!r}")
            print(f"  │  Muestra de valores: {muestra}")
            while True:
                r = input("  └─ ¿Qué es? [p/d/e]: ").strip().lower()
                if r in ("p", "d", "e"):
                    roles[h] = r
                    break
                print("     Escribe p, d o e.")
            print()

    # Aplicar eliminaciones y reconstruir filas
    elim_set = {h for h, rol in roles.items() if rol == "e"}
    dato_set = {h for h, rol in roles.items() if rol == "d"}

    if elim_set:
        idx_elim = {i for i, h in enumerate(headers) if h in elim_set}
        log.append(f"[COL] Columnas eliminadas: {list(elim_set)}")
        headers = [h for i, h in enumerate(headers) if i not in idx_elim]
        filas = [[v for i, v in enumerate(f) if i not in idx_elim] for f in filas]
        print(f"\n  ✓ {len(elim_set)} columna(s) eliminada(s): {list(elim_set)}")

    if dato_set:
        log.append(f"[COL] Columnas de contexto (no pregunta): {list(dato_set)}")
        print(f"  · {len(dato_set)} columna(s) de contexto documentadas: {list(dato_set)}")

    n_preg = sum(1 for r in roles.values() if r == "p")
    n_dato = sum(1 for r in roles.values() if r == "d")
    n_elim = len(elim_set)
    print(f"\n  Resumen: {n_preg} preguntas · {n_dato} datos de contexto · {n_elim} eliminadas")

    return headers, filas, {h: r for h, r in roles.items() if r != "e"}


# ─── FASE ASISTIDA ────────────────────────────────────────────────────────────

def fase_asistida(
    headers: list[str], filas: list[list[str]],
    metricas: dict, log: list
) -> tuple[list[str], list[list[str]], dict]:
    """
    Presenta SOLO los casos detectados.
    Si no hay casos de un tipo, lo omite completamente.
    """
    decisiones = {}
    filas = [list(f) for f in filas]

    print("\n" + "═"*66)
    print("  FASE ASISTIDA")
    print("═"*66)
    print("  Solo se presentan los casos que el sistema no puede resolver solo.")
    print("  Si no hay casos de algún tipo, se omite automáticamente.\n")

    n_casos = (len(metricas["duplicados"]) + len(metricas["imposibles"]) +
               sum(1 for d in metricas["nulos"].values() if d["pct"] > 50))

    if n_casos == 0:
        print("  No se detectaron casos que requieran intervención.")
        print("  El archivo está limpio. ✓\n")
        return headers, filas, decisiones

    # ── A: Duplicados exactos ──────────────────────────────────────────────────
    dups = metricas["duplicados"]
    if dups:
        print(f"─── A. Duplicados exactos ({len(dups)} par{'es' if len(dups)>1 else ''}) ───")
        print("  Contexto: dos filas idénticas en todos los campos.")
        print("  Puede ser error de exportación o dos personas con respuestas idénticas.\n")
        eliminar = set()

        for fa, fb in dups[:5]:
            if fa < len(filas) and fb < len(filas):
                muestra = dict(list(zip(headers[:4], filas[fa][:4])))
                print(f"  Fila {fa+2} = Fila {fb+2} → {muestra}")
                r = _pedir("  [e]liminar segunda / [c]onservar ambas")
                if r == "e":
                    eliminar.add(fb)
                    decisiones[f"dup_{fb}"] = "eliminado"
                    log.append(f"[FA] Dup fila {fb+2} → eliminada")
                else:
                    decisiones[f"dup_{fb}"] = "conservado"

        if len(dups) > 5:
            r = _pedir(f"  Quedan {len(dups)-5} duplicados más. [e]liminar todos / [c]onservar")
            if r == "e":
                for _, fb in dups[5:]:
                    eliminar.add(fb); decisiones[f"dup_{fb}"] = "eliminado_masivo"

        if eliminar:
            filas = [f for i, f in enumerate(filas) if i not in eliminar]
            print(f"\n  ✓ {len(eliminar)} fila(s) eliminada(s)\n")

    # ── B: Valores imposibles ──────────────────────────────────────────────────
    imposibles = metricas["imposibles"]
    if imposibles:
        print(f"─── B. Valores imposibles/atípicos ({len(imposibles)}) ───")
        print("  Contexto: negativos inesperados u outliers extremos (±4σ).\n")

        for caso in imposibles[:10]:
            fi, col = caso["fila"], caso["col"]
            if fi >= len(filas) or col not in headers: continue
            print(f"  Fila {fi+2} | {col[:40]} = {caso['valor']}")
            print(f"  Razón: {caso['razon']}")
            print(f"  Rango del resto: {caso['rango']}")
            r = _pedir("  [c]onservar / [n]ulificar / [r]emplazar por otro valor")
            j = headers.index(col)
            if r == "n":
                filas[fi][j] = ""
                decisiones[f"imp_{fi}_{col}"] = "nulificado"
                log.append(f"[FB] Imposible fila {fi+2} {col} → nulificado")
            elif r == "r":
                nuevo = input("  Nuevo valor: ").strip()
                filas[fi][j] = nuevo
                decisiones[f"imp_{fi}_{col}"] = f"reemplazado:{nuevo}"
                log.append(f"[FB] Imposible fila {fi+2} {col} → {nuevo}")
            else:
                decisiones[f"imp_{fi}_{col}"] = "conservado"
            print()

        if len(imposibles) > 10:
            print(f"  [{len(imposibles)-10} casos adicionales en JSON de métricas]\n")

    # ── C: Columnas con >50% nulos ─────────────────────────────────────────────
    cols_nulos = [(c, d) for c, d in metricas["nulos"].items() if d["pct"] > 50 and c in headers]
    if cols_nulos:
        print(f"─── C. Columnas con >50% nulos ({len(cols_nulos)}) ───")
        print("  Puede ser pregunta opcional, condicional, o error de exportación.\n")
        for col, datos in cols_nulos:
            print(f"  {col[:50]}  →  {datos['n']} nulos ({datos['pct']}%)")
            r = _pedir("  [c]onservar / [e]liminar columna / [m]arcar como condicional")
            if r == "e":
                j = headers.index(col)
                headers = [h for i, h in enumerate(headers) if i != j]
                filas = [[v for i, v in enumerate(f) if i != j] for f in filas]
                decisiones[f"col_{col}"] = "eliminada"
                log.append(f"[FC] Columna '{col}' eliminada ({datos['pct']}% nulos)")
            elif r == "m":
                decisiones[f"col_{col}"] = "condicional"
            else:
                decisiones[f"col_{col}"] = "conservada"
            print()

    # ── D: Completitud de respondentes ────────────────────────────────────────
    n_cols = len(headers)
    if n_cols > 0:
        bajos = [(i, round((1 - sum(1 for v in f if not v.strip()) / n_cols) * 100, 1))
                 for i, f in enumerate(filas)
                 if sum(1 for v in f if not v.strip()) / n_cols > 0.5]

        if bajos:
            print(f"─── D. Respondentes con <50% completitud ({len(bajos)}) ───")
            for i, pct in bajos[:5]:
                print(f"  Fila {i+2}: {pct}% respondida")
            if len(bajos) > 5:
                print(f"  ... y {len(bajos)-5} más")
            umb_str = input("\n  ¿Excluir respondentes con menos de qué %? [30 / 0=no excluir]: ").strip()
            try: umb = float(umb_str) if umb_str else 30
            except ValueError: umb = 30
            if umb > 0:
                excluir = {i for i, pct in bajos if pct < umb}
                filas = [f for i, f in enumerate(filas) if i not in excluir]
                decisiones["respondentes_excluidos"] = len(excluir)
                log.append(f"[FD] {len(excluir)} respondentes excluidos (completitud < {umb}%)")
                print(f"  ✓ {len(excluir)} fila(s) excluida(s)\n")

    # ── E: Variantes textuales ────────────────────────────────────────────────
    tipos = metricas.get("tipos", {})
    encontradas = []
    for col in headers:
        if tipos.get(col) not in ("categorica", "binaria", "texto_libre"): continue
        try: j = headers.index(col)
        except ValueError: continue
        vals = list({f[j].strip() for f in filas if f[j].strip()})
        grupos = defaultdict(list)
        for u in vals:
            raiz = _normalizar_raiz(u)
            grupos[raiz].append(u)
        for g in grupos.values():
            if len(g) > 1: encontradas.append((col, g))

    if encontradas:
        print(f"─── E. Variantes textuales ({len(encontradas)} grupos) ───")
        print("  Valores similares que podrían ser la misma categoría.\n")
        for col, grupo in encontradas[:5]:
            print(f"  {col[:40]}: {grupo}")
            r = _pedir("  ¿[u]nificar / [c]onservar separados?")
            if r == "u":
                canon = input(f"  Forma canónica {grupo}: ").strip()
                if canon:
                    j = headers.index(col)
                    cnt = sum(1 for f in filas if f[j].strip() in grupo)
                    for f in filas:
                        if f[j].strip() in grupo: f[j] = canon
                    decisiones[f"variante_{col}"] = f"→{canon}"
                    log.append(f"[FE] {col}: {grupo} → '{canon}' ({cnt} filas)")
                    print(f"  ✓ {cnt} celdas unificadas\n")
            else:
                decisiones[f"variante_{col}"] = "conservado"

    return headers, filas, decisiones


def _normalizar_raiz(texto: str) -> str:
    """Normaliza texto para detectar variantes: sin acentos, lower, sin espacios dobles."""
    mapa = str.maketrans("áàäéèëíìïóòöúùüÁÀÄÉÈËÍÌÏÓÒÖÚÙÜ",
                         "aaaeeeiiiooouuuAAAEEEIIIOOOUUU")
    return re.sub(r"\s+", " ", texto.translate(mapa).lower().strip())


def _pedir(prompt: str) -> str:
    r = input(f"\n  {prompt}: ").strip().lower()
    return r[:1] if r else "c"


# ─── EXPORTACIÓN ──────────────────────────────────────────────────────────────

def exportar(
    ruta_base: str, ts: str,
    headers: list[str], filas: list[list[str]],
    metricas: dict, calidad: dict, decisiones: dict,
    roles_cols: dict, meta: dict, log: list
) -> tuple[str, str, str]:

    ruta_csv  = f"{ruta_base}_limpio_{ts}.csv"
    ruta_json = f"{ruta_base}_metricas_{ts}.json"
    ruta_log  = f"{ruta_base}_log_{ts}.txt"

    with open(ruta_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(headers)
        writer.writerows(filas)

    doc_json = {
        "meta_proceso": meta,
        "metricas_calidad": calidad,
        "tipos_detectados": metricas["tipos"],
        "nulos_por_columna": metricas["nulos"],
        "duplicados_detectados": [list(p) for p in metricas["duplicados"]],
        "valores_imposibles": metricas["imposibles"],
        "trazabilidad_transformaciones": metricas["trazabilidad"],
        "decisiones_investigador": decisiones,
        "roles_columnas": roles_cols,
    }
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(doc_json, f, ensure_ascii=False, indent=2, default=str)

    with open(ruta_log, "w", encoding="utf-8") as f:
        f.write("\n".join(log))

    return ruta_csv, ruta_json, ruta_log


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Uso: python3 limpieza_encuestas.py <archivo.csv|.xlsx|.xls|.ods>")
        sys.exit(1)

    ruta = sys.argv[1]
    if not os.path.exists(ruta):
        print(f"Error: no se encontró '{ruta}'"); sys.exit(1)

    base = os.path.splitext(os.path.basename(ruta))[0]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log = [f"LIMPIEZA — {ruta} — {ts}"]

    print(f"\n{'═'*66}")
    print("  LIMPIEZA DE ENCUESTAS")
    print(f"  {ruta}")
    print("═"*66)

    # 1. Carga
    print("\n[1/5] Cargando archivo...")
    headers, filas = cargar(ruta)
    log.append(f"[INGESTA] {len(filas)} filas × {len(headers)} columnas")
    print(f"  ✓ {len(filas)} respondentes × {len(headers)} columnas")

    # 2. Plataforma
    print("\n[2/5] Detectando plataforma...")
    plataforma = detectar_plataforma(headers)
    print(f"  · Detectada automáticamente: {plataforma.upper()}")
    conf = input(f"  ¿Es correcta? [s / otra: google|microsoft|limesurvey|otro]: ").strip().lower()
    if conf not in ("s", ""):
        plataforma = conf if conf in SESION_EXACTA else "otro"
        print(f"  ✓ Plataforma ajustada a: {plataforma.upper()}")
    log.append(f"[PLATAFORMA] {plataforma}")

    # 3. Fase automática
    print("\n[3/5] Fase automática...")
    headers, filas, metricas = fase_automatica(headers, filas, plataforma, log)
    calidad = calcular_calidad(metricas, headers, filas)

    print(f"\n  ┌─ Resumen de calidad ─────────────────────────────┐")
    print(f"  │  Respondentes:       {calidad['n_respondentes']}")
    print(f"  │  Columnas:           {calidad['n_columnas']}")
    print(f"  │  Completitud global: {calidad['pct_completitud']}%")
    print(f"  │  Nulos:              {calidad['pct_nulos']}%")
    print(f"  │  Duplicados:         {calidad['n_duplicados']}")
    print(f"  │  Valores imposibles: {calidad['n_imposibles']}")
    if calidad["cols_mas_nulos"]:
        print(f"  │  Cols con más nulos: {calidad['cols_mas_nulos'][:3]}")
    print(f"  └──────────────────────────────────────────────────┘")

    # 4. Revisión de columnas
    print("\n[4/5] Revisión de columnas...")
    headers, filas, roles_cols = revisar_columnas(headers, filas, log)
    metricas["roles_columnas"] = roles_cols

    # 4.5. Fase asistida
    print("\n[4.5/5] Fase asistida...")
    headers, filas, decisiones = fase_asistida(headers, filas, metricas, log)

    # 5. Exportación
    print("\n[5/5] Exportando...")
    meta = {
        "archivo": ruta,
        "plataforma": plataforma,
        "timestamp": ts,
        "n_original": metricas["n_original"],
        "n_columnas_original": metricas["n_columnas_original"],
        "n_final": len(filas),
        "n_columnas_final": len(headers),
        "n_preguntas": sum(1 for r in roles_cols.values() if r == "p"),
        "n_contexto": sum(1 for r in roles_cols.values() if r == "d"),
        "n_eliminadas": metricas["n_columnas_original"] - len(headers),
        "decisiones": len(decisiones),
    }
    calidad_final = calcular_calidad(metricas, headers, filas)
    ruta_csv, ruta_json, ruta_log = exportar(
        base, ts, headers, filas,
        metricas, calidad_final, decisiones,
        roles_cols, meta, log
    )

    print(f"\n{'═'*66}")
    print("  LIMPIEZA COMPLETADA")
    print("═"*66)
    print(f"  CSV limpio:    {ruta_csv}")
    print(f"  Métricas JSON: {ruta_json}")
    print(f"  Log:           {ruta_log}")
    print(f"\n  Respondentes: {metricas['n_original']} → {len(filas)}")
    print(f"  Columnas:     {metricas['n_columnas_original']} → {len(headers)}")
    print(f"  Preguntas confirmadas: {meta['n_preguntas']}")
    print(f"  Decisiones registradas: {len(decisiones)}")
    print(f"\n  Siguiente paso:")
    print(f"  python3 estandarizacion_encuestas.py {ruta_csv} {ruta_json}")


if __name__ == "__main__":
    main()
