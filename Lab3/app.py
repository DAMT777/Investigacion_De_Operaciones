import tkinter as tk
from tkinter import messagebox
import pandas as pd

from simplex import Simplex
from display import ShowTable
from parser_ai import parse_problem

def solve():
    try:
        c = list(map(float, entry_c.get().split(",")))
        A, b = [], []
        for restriccion in text_A.get("1.0", tk.END).strip().split("\n"):
            partes = restriccion.split("<=")
            coef = list(map(float, partes[0].split(",")))
            rhs = float(partes[1])
            A.append(coef)
            b.append(rhs)
        steps, solution = Simplex(c, A, b)
        mostrar_resultados(steps, solution)
    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un problema en modo manual: {e}")

def solve_ia():
    try:
        problema = text_natural.get("1.0", tk.END).strip()
        c, A, b = parse_problem(problema)
        steps, solution = Simplex(c, A, b)
        mostrar_resultados(steps, solution)
    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un problema en modo IA: {e}")

def mostrar_resultados(steps, solution):
    text_output.delete("1.0", tk.END)
    for i, step in enumerate(steps):
        if not isinstance(step, pd.DataFrame):
            df = pd.DataFrame(step)
        else:
            df = step
        text_output.insert(tk.END, f"Iteración {i}:\n")
        text_output.insert(tk.END, df.to_string(index=False))
        text_output.insert(tk.END, "\n\n")
    text_output.insert(tk.END, f"Solución óptima:\n{solution}\n")

root = tk.Tk()
root.title("Método Simplex")

frame_left = tk.Frame(root, padx=10, pady=10)
frame_left.pack(side="left", fill="y")

frame_right = tk.Frame(root, padx=10, pady=10)
frame_right.pack(side="right", fill="both", expand=True)


frame_modelo = tk.LabelFrame(frame_left, text="Modelo Matemático", padx=10, pady=10)
frame_modelo.pack(fill="x", pady=5)

tk.Label(frame_modelo, text="Coeficientes de la función objetivo (ej: 3,5):").pack(anchor="w")
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

root.mainloop()
