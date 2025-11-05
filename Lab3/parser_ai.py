import os
import json
import re
import logging
from groq import Groq

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("parser_ai")

# Cargar variables desde .env si existe (opcionalmente con python-dotenv)
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if not s or s.startswith("#") or "=" not in s:
                        continue
                    k, v = s.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k and k not in os.environ:
                        os.environ[k] = v
        except Exception:
            pass

client = None
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

if GROQ_API_KEY:
    try:
        client = Groq(api_key=GROQ_API_KEY)
        logger.info("Groq client inicializado.")
    except Exception as e:
        logger.warning(f"No se pudo inicializar Groq: {e}")
        client = None
else:
    logger.info("No se encontró GROQ_API_KEY; se usará parser local (dummy).")


def _normalize_A_rows(A, n_vars):
    normalized = []
    for row in A:
        row = list(map(float, row))
        if len(row) < n_vars:
            row = row + [0.0] * (n_vars - len(row))
        elif len(row) > n_vars:
            row = row[:n_vars]
        normalized.append(row)
    return normalized


def _try_parse_json_from_raw(raw):
    raw = raw.strip()
    if not raw:
        raise ValueError("Respuesta vacía.")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{(?:.|\n)*\}", raw)
        if m:
            return json.loads(m.group(0))
        raise ValueError("No se pudo extraer JSON válido.")


def _dummy_parse(texto):
    texto = texto.replace("×", "*")
    c = []
    m_obj = re.search(r"(maximizar|maximo|max)\s*[:\-]?\s*(.+?)(?:sujeto|restricciones|$)", texto, flags=re.I | re.S)
    if m_obj:
        expr = m_obj.group(2)
        pairs = re.findall(r"([+-]?\d+(?:\.\d+)?)\s*\*?\s*x\s*([0-9]+)", expr, flags=re.I)
        if pairs:
            pairs_sorted = sorted(((int(idx), float(val)) for val, idx in pairs), key=lambda x: x[0])
            c = [v for _, v in pairs_sorted]
    if not c:
        pairs = re.findall(r"([+-]?\d+(?:\.\d+)?)\s*\*?\s*x\s*([0-9]+)", texto, flags=re.I)
        if pairs:
            pairs_sorted = sorted(((int(idx), float(val)) for val, idx in pairs), key=lambda x: x[0])
            c = [v for _, v in pairs_sorted]
    constraints = re.findall(r"([0-9xX\+\-\s\*,\.]*)\s*(<=|>=|=)\s*([+-]?\d+(?:\.\d+)?)", texto)
    A = []
    b = []
    for lhs, sign, rhs in constraints:
        pairs = re.findall(r"([+-]?\d+(?:\.\d+)?)\s*\*?\s*x\s*([0-9]+)", lhs, flags=re.I)
        if pairs:
            pairs_sorted = sorted(((int(idx), float(val)) for val, idx in pairs), key=lambda x: x[0])
            row = [v for _, v in pairs_sorted]
        else:
            nums = re.findall(r"([+-]?\d+(?:\.\d+)?)", lhs)
            row = [float(n) for n in nums] if nums else []
        A.append(row)
        b.append(float(rhs))
    if not c and A:
        n_vars = max((len(r) for r in A), default=0)
        c = [0.0] * n_vars
    if not c or not A or not b:
        raise ValueError("No se pudieron extraer c, A o b.")
    A = _normalize_A_rows(A, len(c))
    return c, A, b


def parse_problem(texto, use_ai=True, model="llama-3.1-8b-instant"):
    if use_ai and client:
        prompt = f"""
Convierte el siguiente problema de programación lineal escrito en lenguaje natural a un modelo matemático en JSON estricto; los arreglos pueden tener n variables (no necesariamente dos).

Reglas:
- La salida debe ser ÚNICAMENTE un objeto JSON válido, sin texto adicional.
- El objeto JSON debe tener exactamente tres claves: "c", "A" y "b".
- "c" es la lista de coeficientes de la función objetivo (ejemplo: [40, 55]).
- "A" es una matriz rectangular (lista de listas), donde cada fila corresponde a los coeficientes de una restricción.
- "b" es una lista con los valores del lado derecho de cada restricción.
- Todas las filas de "A" deben tener la misma cantidad de coeficientes que "c".
- Usa solo números (enteros o decimales).

Ejemplo de salida válida:
{{"c": [3, 5], "A": [[1, 2], [3, 2]], "b": [6, 12]}}

Problema: {texto}
"""
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            raw = ""
            try:
                raw = response.choices[0].message.content
            except Exception:
                raw = str(response)
            raw = (raw or "").strip()
            logger.info("Respuesta cruda: %s", raw[:500])
            data = _try_parse_json_from_raw(raw)
            if not isinstance(data, dict) or not all(k in data for k in ("c", "A", "b")):
                return _dummy_parse(texto)

            def _flatten_to_floats(x):
                if x is None:
                    return []
                if isinstance(x, (int, float)):
                    return [float(x)]
                if isinstance(x, str):
                    try:
                        return [float(x)]
                    except Exception:
                        return []
                out = []
                try:
                    for item in x:
                        if isinstance(item, (list, tuple)):
                            out.extend(_flatten_to_floats(item))
                        else:
                            if item is None:
                                continue
                            out.append(float(item))
                except TypeError:
                    try:
                        return [float(x)]
                    except Exception:
                        return []
                return out

            c = _flatten_to_floats(data.get("c", []))
            A_raw = data.get("A", [])
            b = _flatten_to_floats(data.get("b", []))

            A = []
            for row in A_raw:
                A.append(_flatten_to_floats(row))

            if not c and A:
                n_vars = max((len(r) for r in A), default=0)
                c = [0.0] * n_vars

            if A:
                rows = len(A)
                cols = max((len(r) for r in A))
                if len(c) != cols and len(c) == rows and b and len(A[0]) == len(b):
                    A = [list(col) for col in zip(*A)]

            A = _normalize_A_rows(A, len(c))

            if len(b) != len(A):
                if len(b) == 0:
                    b = [0.0] * len(A)
                elif len(b) == len(c) and len(A) == len(c):
                    pass
                else:
                    raise ValueError(
                        f"Dimensiones inconsistentes tras parseo: len(c)={len(c)}, len(A)={(len(A), len(A[0]) if A else 0)}, len(b)={len(b)}"
                    )

            logger.info("Parsed shapes: c=%d, A=%dx%d, b=%d", len(c), len(A), len(A[0]) if A else 0, len(b))
            return c, A, b

        except Exception as e:
            logger.warning("Error en Groq: %s", e)
            return _dummy_parse(texto)
    else:
        return _dummy_parse(texto)

