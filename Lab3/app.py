import tkinter as tk
from tkinter import messagebox
import pandas as pd

from simplex import Simplex
from display import problem_summary, build_iteration_views, dataframe_to_text, label_tableau
from parser_ai import parse_problem


def solve():
    try:
        c = list(map(float, entry_c.get().split(",")))
        A, b = [], []
        for restriccion in text_A.get("1.0", tk.END).strip().split("\n"):
            if not restriccion.strip():
                continue
            partes = restriccion.split("<=")
            coef = list(map(float, partes[0].split(",")))
            rhs = float(partes[1])
            A.append(coef)
            b.append(rhs)
        steps, solution = Simplex(c, A, b)
        mostrar_resultados(steps, solution, c, A, b, sense="max")
    except Exception as e:
        messagebox.showerror("Error", f"Ocurrio un problema en modo manual: {e}")


def solve_ia():
    try:
        problema = text_natural.get("1.0", tk.END).strip()
        c, A, b = parse_problem(problema)
        steps, solution = Simplex(c, A, b)
        mostrar_resultados(steps, solution, c, A, b, sense="max")
    except Exception as e:
        messagebox.showerror("Error", f"Ocurrio un problema en modo IA: {e}")


def mostrar_resultados(steps, solution, c, A, b, sense="max"):
    text_output.delete("1.0", tk.END)

    # Encabezado del problema
    text_output.insert(tk.END, "Modelo del problema\n", ("title",))
    text_output.insert(tk.END, problem_summary(c, A, b, sense) + "\n\n")

    # Vista de iteraciones: antes y despues del pivote
    views = build_iteration_views(steps, c, A, b, sense)
    if not views:
        n_vars, n_cons = len(c), len(b)
        df_final = label_tableau(steps[-1], n_vars, n_cons)
        text_output.insert(tk.END, "Tabla final (optima)\n", ("subtitle",))
        text_output.insert(tk.END, dataframe_to_text(df_final) + "\n\n")
    else:
        for view in views:
            idx = view["index"]
            text_output.insert(tk.END, f"Iteracion {idx} — Antes del pivote\n", ("subtitle",))
            if view.get("entering") and view.get("leaving"):
                text_output.insert(
                    tk.END,
                    f"Entra {view['entering']}  |  Sale {view['leaving']}\n",
                    ("emphasis",),
                )
            text_output.insert(tk.END, dataframe_to_text(view["before_df"]) + "\n\n")

            text_output.insert(tk.END, "Resultado (despues del pivote)\n", ("subtitle",))
            text_output.insert(tk.END, dataframe_to_text(view["after_df"]) + "\n\n")

    # Resultado final
    text_output.insert(tk.END, "Solucion optima\n", ("title",))
    n_vars = len(c)
    vars_sorted = [f"x{i+1}" for i in range(n_vars)]
    lines = []
    for k in vars_sorted:
        val = solution.get(k, 0)
        lines.append(f"{k} = {val}")
    lines.append(f"Z = {solution.get('Z', 0)}")
    text_output.insert(tk.END, "; ".join(lines) + "\n")


root = tk.Tk()
root.title("Metodo Simplex")

frame_left = tk.Frame(root, padx=10, pady=10)
frame_left.pack(side="left", fill="y")

frame_right = tk.Frame(root, padx=10, pady=10)
frame_right.pack(side="right", fill="both", expand=True)


frame_modelo = tk.LabelFrame(frame_left, text="Modelo Matematico", padx=10, pady=10)
frame_modelo.pack(fill="x", pady=5)

tk.Label(frame_modelo, text="Coeficientes de la funcion objetivo (ej: 3,5):").pack(anchor="w")
entry_c = tk.Entry(frame_modelo, width=40)
entry_c.pack()

tk.Label(frame_modelo, text="Restricciones (ej: 1,2 <= 6)").pack(anchor="w")
text_A = tk.Text(frame_modelo, width=40, height=5)
text_A.pack()

btn_manual = tk.Button(frame_modelo, text="Resolver (Modo Manual)", command=solve)
btn_manual.pack(pady=5)

# --- Bloque IA ---
frame_ia = tk.LabelFrame(frame_left, text="Problema en Lenguaje Natural", padx=10, pady=10)
frame_ia.pack(fill="x", pady=5)

text_natural = tk.Text(frame_ia, width=40, height=5)
text_natural.pack()

btn_ia = tk.Button(frame_ia, text="Resolver con IA", command=solve_ia)
btn_ia.pack(pady=5)


tk.Label(frame_right, text="Resultados").pack(anchor="w")
text_output = tk.Text(frame_right, width=80, height=30)
text_output.pack(fill="both", expand=True)

# Estilos basicos para mejorar la lectura
try:
    text_output.tag_configure("title", font=("Segoe UI", 11, "bold"))
    text_output.tag_configure("subtitle", font=("Segoe UI", 10, "bold"))
    text_output.tag_configure("emphasis", foreground="#0A84FF")
except Exception:
    pass

root.mainloop()

