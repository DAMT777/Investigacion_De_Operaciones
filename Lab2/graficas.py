from __future__ import annotations
import re, math
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
import numpy as np
import matplotlib.pyplot as plt

@dataclass

class Restriccion:
    a: float
    b: float
    signo: str   # '<=', '>=', '='
    c: float
    etiqueta: str = ""

EPS = 1e-9

def _dedup(pts: List[Tuple[float, float]], nd=6):
    out, seen = [], set()
    for x, y in pts:
        k = (round(x, nd), round(y, nd))
        if k not in seen and np.isfinite(x) and np.isfinite(y):
            seen.add(k); out.append((float(k[0]), float(k[1])))
    return out

def _ordenar(pts: List[Tuple[float, float]]):
    if not pts: return pts
    cx = sum(x for x,_ in pts)/len(pts)
    cy = sum(y for _,y in pts)/len(pts)
    return sorted(pts, key=lambda p: math.atan2(p[1]-cy, p[0]-cx))

def _cumple(p: Tuple[float,float], R: Restriccion) -> bool:
    x,y = p; v = R.a*x + R.b*y
    if R.signo == "<=": return v <= R.c + 1e-7
    if R.signo == ">=": return v >= R.c - 1e-7
    return abs(v - R.c) <= 1e-7

def _inter(r1: Tuple[float,float,float], r2: Tuple[float,float,float]):
    a1,b1,c1 = r1; a2,b2,c2 = r2
    if abs(a1) < EPS and abs(b1) < EPS: return None
    if abs(a2) < EPS and abs(b2) < EPS: return None
    det = a1*b2 - a2*b1
    if abs(det) < EPS: return None
    x = (c1*b2 - c2*b1) / det
    y = (a1*c2 - a2*c1) / det
    return (x, y)

def _parse_line_to_restr(line: str) -> Optional[Restriccion]:
    """
    Convierte líneas tipo:
      - "40x + 30y <= 600  → peso"
      - "x >= 3            → mínimo de grandes"
      - "y >= 2x           → relación"
      - "- y >= 4x"  (guion + espacio = viñeta; se quita)
      - "-y >= 4x"   (signo negativo real)
      - "x = 3 + y", "5 >= x - 2y"
    a Restriccion, soportando variables a ambos lados y evitando
    confundir el número de '4x' como constante.
    """
    if not line:
        return None

    s = line.strip()

    m_bullet = re.match(r"^\s*([-–—•·*])\s+(.*)$", s)
    if m_bullet:
        s = m_bullet.group(2)

  
    s = (s.replace("≤","<=").replace("⩽","<=")
           .replace("≥",">=").replace("⩾",">=")
           .replace("−","-"))


    s_for_parse = re.split(r"→|\[", s)[0].strip()
    etiqueta    = s_for_parse 


    m = re.search(r"(<=|>=|=)", s_for_parse)
    if not m:
        return None
    op = m.group(1)
    left  = s_for_parse[:m.start()]
    right = s_for_parse[m.end():]

    term_pat = re.compile(r"([+-]?\s*\d*(?:[\.,]\d*)?)\s*\*?\s*([xy])", re.I)

    def _parse_expr(expr: str):
        """Devuelve (ax, ay, c) para una expresión con x, y y constantes."""
        ax = ay = c = 0.0
        spans = []
        for t in term_pat.finditer(expr):
            coef_s = (t.group(1) or "").replace(" ", "")
            var    = t.group(2).lower()
            if coef_s in ("", "+", "+.", "+,"):
                coef = 1.0
            elif coef_s in ("-", "-.", "-,"):
                coef = -1.0
            else:
                coef = float(coef_s.replace(",", "."))
            if var == "x":
                ax += coef
            else:
                ay += coef
            spans.append(t.span())

        s_no_vars = []
        idx = 0
        for a, b in spans:
            s_no_vars.append(expr[idx:a])
            idx = b
        s_no_vars.append(expr[idx:])
        s_no_vars = "".join(s_no_vars)

        for t in re.finditer(r"([+-]?\d+(?:[\.,]\d+)?)", s_no_vars):
            c += float(t.group(1).replace(",", "."))

        return ax, ay, c

    Lx, Ly, Lc = _parse_expr(left)
    Rx, Ry, Rc = _parse_expr(right)

    ax = Lx - Rx
    by = Ly - Ry
    rhs = Rc - Lc

    if abs(ax) < EPS and abs(by) < EPS:
        return None

    return Restriccion(ax, by, op, rhs, etiqueta)

def parse_salida_modelo(texto: str) -> Dict:
    """
    Extrae solo lo de la sección 'Restricciones:' y la FO.
    Evita capturar 'Coeficientes: x = ..., y = ...' como restricción.
    """
    if not texto or not texto.strip():
        raise ValueError("Texto del modelo vacío.")


    sentido = "max"
    m_tipo = re.search(r"Tipo\s*:\s*(Maximizar|Minimizar)", texto, re.I)
    if m_tipo:
        sentido = "max" if m_tipo.group(1).lower().startswith("max") else "min"

    px = py = None
    m_exp = re.search(r"Expresi[oó]n\s*:\s*Z\s*=\s*([^\n\r]+)", texto, re.I)
    if m_exp:
        expr = m_exp.group(1)
        mx = re.search(r"([+-]?\d+(?:[\.,]\d+)?)(?=\s*\*?\s*x)", expr, re.I)
        my = re.search(r"([+-]?\d+(?:[\.,]\d+)?)(?=\s*\*?\s*y)", expr, re.I)
        if mx: px = float(mx.group(1).replace(",", "."))
        if my: py = float(my.group(1).replace(",", "."))
    if px is None or py is None:
        m_cx = re.search(r"Coeficientes[^:\n]*:\s*.*?x\s*=\s*([+-]?\d+(?:[\.,]\d+)?)", texto, re.I)
        m_cy = re.search(r"Coeficientes[^:\n]*:\s*.*?y\s*=\s*([+-]?\d+(?:[\.,]\d+)?)", texto, re.I)
        if m_cx: px = float(m_cx.group(1).replace(",", "."))
        if m_cy: py = float(m_cy.group(1).replace(",", "."))
    if px is None or py is None:
        raise ValueError("No se pudieron leer los coeficientes de la función objetivo.")


    ini = re.search(r"(📐\s*)?Restricciones\s*:", texto, re.I)
    if not ini:
        raise ValueError("No se encontró la sección 'Restricciones:' en la salida.")
    start = ini.end()
    fin = len(texto)
    m_fin = re.search(r"\n\s*(📌|🎯|🚫|──|—|\-\-|\_\_)", texto[start:], re.I)
    if m_fin:
        fin = start + m_fin.start()
    bloque = texto[start:fin]

    restricciones: List[Restriccion] = []
    for raw in bloque.splitlines():
        r = _parse_line_to_restr(raw)
        if r: restricciones.append(r)

    if not any(r.a==1 and r.b==0 and r.signo==">=" and abs(r.c)<EPS for r in restricciones):
        restricciones.append(Restriccion(1,0,">=",0,"x ≥ 0"))
    if not any(r.a==0 and r.b==1 and r.signo==">=" and abs(r.c)<EPS for r in restricciones):
        restricciones.append(Restriccion(0,1,">=",0,"y ≥ 0"))

    if len(restricciones) < 2:
        raise ValueError("No se detectaron suficientes restricciones en la sección correspondiente.")

    return {"sentido": sentido, "obj": (px, py), "restr": restricciones}

def pretty_debug_restricciones(restr: List[Restriccion]) -> str:
    lines = ["[Restricciones detectadas]"]
    for r in restr:
        lines.append(f"  {r.a:.3f}*x + {r.b:.3f}*y {r.signo} {r.c:.3f}   ({r.etiqueta})")
    return "\n".join(lines)

def resolver(restricciones: List[Restriccion], obj: Tuple[float, float], sentido: str):
    rectas = [(r.a,r.b,r.c) for r in restricciones]
    cand = []
    for i in range(len(rectas)):
        for j in range(i+1, len(rectas)):
            p = _inter(rectas[i], rectas[j])
            if p and all(_cumple(p, R) for R in restricciones):
                cand.append(p)
    verts = _ordenar(_dedup(cand))
    if not verts:
        raise ValueError("Región factible vacía o no acotada (no hay vértices).")
    px,py = obj
    vals = [px*x + py*y for x,y in verts]
    idx = int(np.argmax(vals) if sentido.lower().startswith("max") else np.argmin(vals))
    return verts, verts[idx], vals[idx]

def graficar(ax: plt.Axes,
             restricciones: List[Restriccion],
             obj: Tuple[float, float],
             sentido: str,
             titulo: str = "Región factible y solución") -> Optional[Dict]:
    rectas = [(r.a,r.b,r.c) for r in restricciones]
    cand = []
    for i in range(len(rectas)):
        for j in range(i+1, len(rectas)):
            p = _inter(rectas[i], rectas[j])
            if p and all(_cumple(p, R) for R in restricciones):
                cand.append(p)
    verts = _ordenar(_dedup(cand))
    if not verts:
        ax.clear()
        ax.text(0.5, 0.5, "Región factible vacía", ha="center", va="center")
        ax.set_axis_off()
        return None

    xs = [x for x,_ in verts]; ys = [y for _,y in verts]
    xmin, xmax = min(0,min(xs))-5, max(xs)+5
    ymin, ymax = min(0,min(ys))-5, max(ys)+5
    X = np.linspace(xmin, xmax, 400)

    ax.clear()
    for R in restricciones:
        a,b,c = R.a,R.b,R.c
        lab = R.etiqueta or f"{a}x + {b}y {R.signo} {c}"
        if abs(a) < EPS and abs(b) < EPS:
            continue
        if abs(b) < EPS:
            if abs(a) < EPS:
                continue
            x0 = c/a
            ax.plot([x0,x0],[ymin,ymax],'--',label=lab)
        else:
            Y = (c - a*X)/b
            ax.plot(X,Y,'--',label=lab)

    poly = verts + [verts[0]]
    ax.fill([p[0] for p in poly],[p[1] for p in poly], alpha=.25, label="Espacio de soluciones")
    ax.scatter([x for x,_ in verts], [y for _,y in verts], s=40, label="Vértices")

    px,py = obj
    vals = [px*x + py*y for x,y in verts]
    idx = int(np.argmax(vals) if sentido.lower().startswith("max") else np.argmin(vals))
    opt = verts[idx]
    ax.scatter([opt[0]],[opt[1]], s=120, edgecolor="black", facecolor="orange", zorder=5, label="Solución óptima")

    ax.set_title(titulo)
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.grid(True, ls=":", alpha=.6)
    ax.set_xlabel("x")
    ax.set_ylabel("y")

    ax.figure.subplots_adjust(right=0.78)
    ax.legend(
        loc="center left",
        bbox_to_anchor=(1.005, 0.5),
        borderaxespad=0.0,
        frameon=False,
        fontsize=9,
        handlelength=2.0
    )

    return {"vertices": verts, "optimo": {"punto": opt, "valor": vals[idx]}}
