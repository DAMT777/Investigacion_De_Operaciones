from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np


EPS = 1e-9


@dataclass
class Restriccion:
    a: float
    b: float
    signo: str  # '<=', '>=', '='
    c: float
    etiqueta: str = ""


def _deduplicar_puntos(puntos: List[Tuple[float, float]], nd: int = 6) -> List[Tuple[float, float]]:
    salida, vistos = [], set()
    for x, y in puntos:
        clave = (round(x, nd), round(y, nd))
        if clave not in vistos and np.isfinite(x) and np.isfinite(y):
            vistos.add(clave)
            salida.append((float(clave[0]), float(clave[1])))
    return salida


def _ordenar_puntos(puntos: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    if not puntos:
        return puntos
    cx = sum(x for x, _ in puntos) / len(puntos)
    cy = sum(y for _, y in puntos) / len(puntos)
    return sorted(puntos, key=lambda p: math.atan2(p[1] - cy, p[0] - cx))


def _cumple_restriccion(p: Tuple[float, float], r: Restriccion) -> bool:
    x, y = p
    v = r.a * x + r.b * y
    if r.signo == "<=":
        return v <= r.c + 1e-7
    if r.signo == ">=":
        return v >= r.c - 1e-7
    return abs(v - r.c) <= 1e-7


def _interseccion(r1: Tuple[float, float, float], r2: Tuple[float, float, float]) -> Optional[Tuple[float, float]]:
    a1, b1, c1 = r1
    a2, b2, c2 = r2
    if abs(a1) < EPS and abs(b1) < EPS:
        return None
    if abs(a2) < EPS and abs(b2) < EPS:
        return None
    det = a1 * b2 - a2 * b1
    if abs(det) < EPS:
        return None
    x = (c1 * b2 - c2 * b1) / det
    y = (a1 * c2 - a2 * c1) / det
    return (x, y)


def _parsear_linea_a_restriccion(linea: str) -> Optional[Restriccion]:
    if not linea:
        return None

    s = linea.strip()

    viñeta = re.match(r"^\s*([-–—•·*])\s+(.*)$", s)
    if viñeta:
        s = viñeta.group(2)

    s = (
        s.replace("≤", "<=")
        .replace("⩽", "<=")
        .replace("≥", ">=")
        .replace("⩾", ">=")
        .replace("−", "-")
    )

    s_sin_comentario = re.split(r"→|\[", s)[0].strip()
    etiqueta = s_sin_comentario

    m = re.search(r"(<=|>=|=)", s_sin_comentario)
    if not m:
        return None

    op = m.group(1)
    izquierda = s_sin_comentario[: m.start()]
    derecha = s_sin_comentario[m.end() :]

    patron_termino = re.compile(r"([+-]?\s*\d*(?:[\.,]\d*)?)\s*\*?\s*([xy])", re.I)

    def descomponer(expr: str) -> Tuple[float, float, float]:
        ax = ay = c = 0.0
        spans = []
        for t in patron_termino.finditer(expr):
            s_coef = (t.group(1) or "").replace(" ", "")
            var = t.group(2).lower()

            if s_coef in ("", "+", "+.", "+,"):
                coef = 1.0
            elif s_coef in ("-", "-.", "-,"):
                coef = -1.0
            else:
                coef = float(s_coef.replace(",", "."))

            if var == "x":
                ax += coef
            else:
                ay += coef
            spans.append(t.span())

        sin_vars = []
        idx = 0
        for a, b in spans:
            sin_vars.append(expr[idx:a])
            idx = b
        sin_vars.append(expr[idx:])
        resto = "".join(sin_vars)

        for t in re.finditer(r"([+-]?\d+(?:[\.,]\d+)?)", resto):
            c += float(t.group(1).replace(",", "."))

        return ax, ay, c

    lx, ly, lc = descomponer(izquierda)
    rx, ry, rc = descomponer(derecha)

    a = lx - rx
    b = ly - ry
    c = rc - lc

    if abs(a) < EPS and abs(b) < EPS:
        return None

    return Restriccion(a=a, b=b, signo=op, c=c, etiqueta=etiqueta)


def parse_salida_modelo(texto: str) -> Dict:
    if not texto or not texto.strip():
        raise ValueError("Texto del modelo vacío.")

    sentido = "max"
    m_tipo = re.search(r"Tipo\s*:\s*(Maximizar|Minimizar)", texto, re.I)
    if m_tipo:
        sentido = "max" if m_tipo.group(1).lower().startswith("max") else "min"

    coef_x = coef_y = None
    m_exp = re.search(r"Expresi[oó]n\s*:\s*Z\s*=\s*([^\n\r]+)", texto, re.I)
    if m_exp:
        expr = m_exp.group(1)
        mx = re.search(r"([+-]?\d+(?:[\.,]\d+)?)(?=\s*\*?\s*x)", expr, re.I)
        my = re.search(r"([+-]?\d+(?:[\.,]\d+)?)(?=\s*\*?\s*y)", expr, re.I)
        if mx:
            coef_x = float(mx.group(1).replace(",", "."))
        if my:
            coef_y = float(my.group(1).replace(",", "."))
    if coef_x is None or coef_y is None:
        m_cx = re.search(r"Coeficientes[^:\n]*:\s*.*?x\s*=\s*([+-]?\d+(?:[\.,]\d+)?)", texto, re.I)
        m_cy = re.search(r"Coeficientes[^:\n]*:\s*.*?y\s*=\s*([+-]?\d+(?:[\.,]\d+)?)", texto, re.I)
        if m_cx:
            coef_x = float(m_cx.group(1).replace(",", "."))
        if m_cy:
            coef_y = float(m_cy.group(1).replace(",", "."))

    if coef_x is None or coef_y is None:
        raise ValueError("No se pudieron leer los coeficientes de la función objetivo.")

    m_ini = re.search(r"(📐\s*)?Restricciones\s*:", texto, re.I)
    if not m_ini:
        raise ValueError("No se encontró la sección 'Restricciones:' en la salida.")
    inicio = m_ini.end()

    fin = len(texto)
    m_fin = re.search(r"\n\s*(📌|🎯|🚫|──|—|\-\-|\_\_)", texto[inicio:], re.I)
    if m_fin:
        fin = inicio + m_fin.start()

    bloque = texto[inicio:fin]

    restricciones: List[Restriccion] = []
    for cruda in bloque.splitlines():
        r = _parsear_linea_a_restriccion(cruda)
        if r:
            restricciones.append(r)

    # No negatividad por defecto si no viene explícita
    if not any(r.a == 1 and r.b == 0 and r.signo == ">=" and abs(r.c) < EPS for r in restricciones):
        restricciones.append(Restriccion(1, 0, ">=", 0, "x ≥ 0"))
    if not any(r.a == 0 and r.b == 1 and r.signo == ">=" and abs(r.c) < EPS for r in restricciones):
        restricciones.append(Restriccion(0, 1, ">=", 0, "y ≥ 0"))

    if len(restricciones) < 2:
        raise ValueError("No se detectaron suficientes restricciones en la sección correspondiente.")

    return {"sentido": sentido, "obj": (coef_x, coef_y), "restr": restricciones}


def graficar(
    eje: plt.Axes,
    restricciones: List[Restriccion],
    obj: Tuple[float, float],
    sentido: str,
    titulo: str = "Región factible y solución",
) -> Optional[Dict]:
    rectas = [(r.a, r.b, r.c) for r in restricciones]
    candidatos: List[Tuple[float, float]] = []

    for i in range(len(rectas)):
        for j in range(i + 1, len(rectas)):
            p = _interseccion(rectas[i], rectas[j])
            if p and all(_cumple_restriccion(p, r) for r in restricciones):
                candidatos.append(p)

    vertices = _ordenar_puntos(_deduplicar_puntos(candidatos))
    if not vertices:
        eje.clear()
        eje.text(0.5, 0.5, "Región factible vacía", ha="center", va="center")
        eje.set_axis_off()
        return None

    xs = [x for x, _ in vertices]
    ys = [y for _, y in vertices]
    xmin, xmax = min(0, min(xs)) - 5, max(xs) + 5
    ymin, ymax = min(0, min(ys)) - 5, max(ys) + 5
    X = np.linspace(xmin, xmax, 400)

    eje.clear()
    for r in restricciones:
        a, b, c = r.a, r.b, r.c
        etiqueta = r.etiqueta or f"{a}x + {b}y {r.signo} {c}"
        if abs(a) < EPS and abs(b) < EPS:
            continue
        if abs(b) < EPS:
            if abs(a) < EPS:
                continue
            x0 = c / a
            eje.plot([x0, x0], [ymin, ymax], "--", label=etiqueta)
        else:
            Y = (c - a * X) / b
            eje.plot(X, Y, "--", label=etiqueta)

    poligono = vertices + [vertices[0]]
    eje.fill([p[0] for p in poligono], [p[1] for p in poligono], alpha=0.25, label="Espacio de soluciones")
    eje.scatter([x for x, _ in vertices], [y for _, y in vertices], s=40, label="Vértices")

    px, py = obj
    valores = [px * x + py * y for x, y in vertices]
    idx_opt = int(np.argmax(valores) if sentido.lower().startswith("max") else np.argmin(valores))
    punto_opt = vertices[idx_opt]

    eje.scatter([punto_opt[0]], [punto_opt[1]], s=120, edgecolor="black", facecolor="orange", zorder=5, label="Solución óptima")

    eje.set_title(titulo)
    eje.set_xlim(xmin, xmax)
    eje.set_ylim(ymin, ymax)
    eje.grid(True, ls=":", alpha=0.6)
    eje.set_xlabel("x")
    eje.set_ylabel("y")

    eje.figure.subplots_adjust(right=0.78)
    eje.legend(
        loc="center left",
        bbox_to_anchor=(1.005, 0.5),
        borderaxespad=0.0,
        frameon=False,
        fontsize=9,
        handlelength=2.0,
    )

    return {"vertices": vertices, "optimo": {"punto": punto_opt, "valor": valores[idx_opt]}}