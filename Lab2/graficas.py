from __future__ import annotations

import json
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


def parse_modelo_json(texto: str) -> Dict:
    """
    Espera un JSON con el esquema:
    {
      "variables": { "x": str|null, "y": str|null },
      "objective": {
        "type": "max"|"min",
        "expression": "Z = a*x + b*y",
        "coeffs": { "x": a, "y": b }
      },
      "constraints": [
        { "lhs": { "x": ax, "y": by }, "op": "<=|>=|=", "rhs": c, "label": str|null }
      ],
      "nonnegativity": true|false
    }
    Devuelve: { "sentido": "max|min", "obj": (px, py), "restr": [Restriccion] }
    """
    try:
        data = json.loads(texto)
    except Exception as exc:
        raise ValueError(f"No es JSON válido: {exc}")

    if not isinstance(data, dict):
        raise ValueError("JSON raíz debe ser un objeto.")

    obj = data.get("objective") or {}
    tipo = obj.get("type")
    if tipo not in ("max", "min"):
        raise ValueError("objective.type debe ser 'max' o 'min'.")

    coeffs = (obj.get("coeffs") or {})
    try:
        px = float(coeffs["x"])
        py = float(coeffs["y"])
    except Exception:
        raise ValueError("Coeficientes de la función objetivo inválidos o faltantes.")

    restricciones: List[Restriccion] = []
    for c in data.get("constraints") or []:
        lhs = c.get("lhs") or {}
        try:
            a = float(lhs.get("x", 0.0))
            b = float(lhs.get("y", 0.0))
            op = c.get("op")
            rhs = float(c.get("rhs", 0.0))
        except Exception:
            raise ValueError("Restricción con tipos inválidos.")

        if op not in ("<=", ">=", "="):
            raise ValueError("Operador de restricción inválido (use <=, >= o =).")
        if abs(a) < EPS and abs(b) < EPS:
            # Ignora líneas sin variables
            continue

        etiqueta = (c.get("label") or "").strip()
        restricciones.append(Restriccion(a=a, b=b, signo=op, c=rhs, etiqueta=etiqueta))

    # No negatividad
    if bool(data.get("nonnegativity", True)):
        if not any(r.a == 1 and r.b == 0 and r.signo == ">=" and abs(r.c) < EPS for r in restricciones):
            restricciones.append(Restriccion(1, 0, ">=", 0, "x ≥ 0"))
        if not any(r.a == 0 and r.b == 1 and r.signo == ">=" and abs(r.c) < EPS for r in restricciones):
            restricciones.append(Restriccion(0, 1, ">=", 0, "y ≥ 0"))

    if len(restricciones) < 2:
        raise ValueError("Se requieren al menos dos restricciones.")

    sentido = "max" if tipo == "max" else "min"
    return {"sentido": sentido, "obj": (px, py), "restr": restricciones}


# ---------- Graficador ----------
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
    det = a1 * b2 - a2 * b1
    if abs(det) < EPS:
        return None
    x = (c1 * b2 - c2 * b1) / det
    y = (a1 * c2 - a2 * c1) / det
    return (x, y)


def _deduplicar_ordenar(vertices: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    if not vertices:
        return vertices
    # Deduplicar con redondeo
    vistos, out = set(), []
    for x, y in vertices:
        k = (round(float(x), 6), round(float(y), 6))
        if k not in vistos and np.isfinite(x) and np.isfinite(y):
            vistos.add(k)
            out.append((k[0], k[1]))
    # Orden polar
    cx = sum(x for x, _ in out) / len(out)
    cy = sum(y for _, y in out) / len(out)
    out.sort(key=lambda p: np.arctan2(p[1] - cy, p[0] - cx))
    return out


def graficar(
    eje: plt.Axes,
    restricciones: List[Restriccion],
    obj: Tuple[float, float],
    sentido: str,
    titulo: str = "Región factible y solución",
):
    rectas = [(r.a, r.b, r.c) for r in restricciones]
    candidatos: List[Tuple[float, float]] = []

    for i in range(len(rectas)):
        for j in range(i + 1, len(rectas)):
            p = _interseccion(rectas[i], rectas[j])
            if p and all(_cumple_restriccion(p, r) for r in restricciones):
                candidatos.append(p)

    vertices = _deduplicar_ordenar(candidatos)
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
