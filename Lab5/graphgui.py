import math
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

from graph_model import (
    validar_grafo_dirigido,
    construir_adyacencias,
    dijkstra,
    bellman_ford
)
from graph_drawer import offset_perpendicular, bezier_q_punto_y_tangente


class InterfazGrafo(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Práctica 4 - Grafos: Dijkstra y Bellman-Ford")
        self.geometry("1180x740")
        self.minsize(1000, 680)

        self.tamano_n = 0
        self.entradas_nombres_columnas = []
        self.entradas_nombres_filas = []
        self.entradas_matriz = []
        self.es_dirigido = tk.BooleanVar(value=False)

        self.ultimo_camino_indices = None
        self.ultima_distancia = None

        self.centro_canvas = (0, 0)

        self.ultimo_dirigido = False
        self.ultima_matriz_norm = None
        self.ultimo_nombres = []
        self.ultima_posiciones = []
        self.nodo_seleccionado = None
        self._id_resalte_nodo = None
        self._label_positions = []

        self._construir_controles_superiores()
        self._construir_zona_matriz()
        self._construir_zona_canvas()

        self.canvas_grafo.bind("<Configure>", lambda e: self._redibujar_si_es_posible())


    # =====================================================================
    #   CONTROLES SUPERIORES
    # =====================================================================

    def _construir_controles_superiores(self):
        marco_superior = ttk.Frame(self, padding=(10, 10))
        marco_superior.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(marco_superior, text="Tamaño n:").pack(side=tk.LEFT)
        self.entrada_n = ttk.Entry(marco_superior, width=5)
        self.entrada_n.pack(side=tk.LEFT, padx=(5, 10))
        self.entrada_n.insert(0, "3")
        self.entrada_n.bind("<FocusOut>", lambda e: self.crear_matriz())
        self.entrada_n.bind("<Return>", lambda e: self.crear_matriz())

        ttk.Button(marco_superior, text="Crear matriz",
                   command=self.crear_matriz).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Checkbutton(marco_superior, text="Dirigido",
                        variable=self.es_dirigido).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(marco_superior, text="Dibujar grafo",
                   command=self.dibujar_grafo).pack(side=tk.LEFT, padx=(0, 20))

        ttk.Label(marco_superior, text="Origen:").pack(side=tk.LEFT)
        self.combo_origen = ttk.Combobox(
            marco_superior, state="readonly", width=12, values=[])
        self.combo_origen.pack(side=tk.LEFT, padx=(5, 10))

        ttk.Label(marco_superior, text="Destino:").pack(side=tk.LEFT)
        self.combo_destino = ttk.Combobox(
            marco_superior, state="readonly", width=12, values=[])
        self.combo_destino.pack(side=tk.LEFT, padx=(5, 10))

        ttk.Button(marco_superior, text="Dijkstra",
                   command=self.calcular_ruta_dijkstra).pack(side=tk.LEFT, padx=(10, 5))

        ttk.Button(marco_superior, text="Bellman-Ford",
                   command=self.calcular_bellman_ford).pack(side=tk.LEFT)


        mensaje_ayuda = (
            "Instrucciones: ponga nombres de nodos en fila superior y columna izquierda.\n"
            "Ingrese pesos en la matriz (vacío o 0 = sin arista). Marque 'Dirigido' si aplica.\n"
            "Elija Origen/Destino y presione Dijkstra o Bellman-Ford."
        )
        ttk.Label(self, text=mensaje_ayuda, foreground="#555",
                  padding=(10, 4)).pack(side=tk.TOP, anchor="w")


    # =====================================================================
    #   ZONA MATRIZ
    # =====================================================================

    def _construir_zona_matriz(self):
        contenedor = ttk.Frame(self)
        contenedor.pack(side=tk.LEFT, fill=tk.BOTH, expand=False,
                        padx=(10, 5), pady=(5, 10))

        self.canvas_matriz = tk.Canvas(
            contenedor, width=540, height=540,
            highlightthickness=1, highlightbackground="#ddd")
        self.canvas_matriz.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        barra_vertical = ttk.Scrollbar(
            contenedor, orient="vertical", command=self.canvas_matriz.yview)
        barra_vertical.pack(side=tk.RIGHT, fill="y")

        barra_horizontal = ttk.Scrollbar(
            contenedor, orient="horizontal", command=self.canvas_matriz.xview)
        barra_horizontal.pack(side=tk.BOTTOM, fill="x")

        self.canvas_matriz.configure(
            yscrollcommand=barra_vertical.set,
            xscrollcommand=barra_horizontal.set
        )

        self.marco_interno_matriz = ttk.Frame(self.canvas_matriz)
        self.ventana_matriz = self.canvas_matriz.create_window(
            (0, 0), window=self.marco_interno_matriz, anchor="nw")
        self.marco_interno_matriz.bind("<Configure>", self._ajustar_scroll_matriz)


    def _ajustar_scroll_matriz(self, evento):
        self.canvas_matriz.configure(
            scrollregion=self.canvas_matriz.bbox("all")
        )
        self.canvas_matriz.itemconfig(
            self.ventana_matriz, width=max(evento.width,
                                           self.marco_interno_matriz.winfo_reqwidth()))
        self.canvas_matriz.itemconfig(
            self.ventana_matriz, height=max(evento.height,
                                            self.marco_interno_matriz.winfo_reqheight()))


    # =====================================================================
    #   CREAR MATRIZ
    # =====================================================================

    def crear_matriz(self):
        try:
            n = int(self.entrada_n.get())
            if n <= 0 or n > 50:
                raise ValueError
            self.tamano_n = n
        except ValueError:
            messagebox.showerror(
                "Error", "n debe ser un entero entre 1 y 50.")
            return

        self.entradas_nombres_columnas.clear()
        self.entradas_nombres_filas.clear()
        self.entradas_matriz.clear()
        self.ultimo_camino_indices = None
        self.ultima_distancia = None

        self.nodo_seleccionado = None
        self._id_resalte_nodo = None
        try:
            self.etiqueta_propiedades.config(
                text="Seleccione un nodo para ver sus propiedades.")
        except:
            pass

        self._set_text_expresion("")

        try:
            self.canvas_matriz.delete(self.ventana_matriz)
        except:
            pass

        for w in self.marco_interno_matriz.winfo_children():
            w.destroy()
        self.marco_interno_matriz.destroy()

        self.marco_interno_matriz = ttk.Frame(self.canvas_matriz)
        self.ventana_matriz = self.canvas_matriz.create_window(
            (0, 0), window=self.marco_interno_matriz, anchor="nw")
        self.marco_interno_matriz.bind(
            "<Configure>", self._ajustar_scroll_matriz)

        nombres_def = [f"v{i+1}" for i in range(self.tamano_n)]

        ttk.Label(self.marco_interno_matriz, text="").grid(
            row=0, column=0, padx=4, pady=4)

        for j in range(self.tamano_n):
            entrada = ttk.Entry(self.marco_interno_matriz,
                                width=12, justify="center")
            entrada.grid(row=0, column=j+1, padx=2, pady=2)
            entrada.insert(0, nombres_def[j])
            self.entradas_nombres_columnas.append(entrada)

        for i in range(self.tamano_n):
            e_fila = ttk.Entry(self.marco_interno_matriz,
                               width=12, justify="center")
            e_fila.grid(row=i+1, column=0, padx=2, pady=2)
            e_fila.insert(0, nombres_def[i])
            self.entradas_nombres_filas.append(e_fila)

            fila = []
            for j in range(self.tamano_n):
                e = ttk.Entry(self.marco_interno_matriz,
                              width=7, justify="center")
                e.grid(row=i+1, column=j+1, padx=1, pady=1)
                if i == j:
                    e.insert(0, "0")
                fila.append(e)
            self.entradas_matriz.append(fila)

        self.canvas_matriz.update_idletasks()
        reqw = self.marco_interno_matriz.winfo_reqwidth()
        reqh = self.marco_interno_matriz.winfo_reqheight()
        self.canvas_matriz.itemconfig(
            self.ventana_matriz, width=reqw, height=reqh)
        self.canvas_matriz.configure(scrollregion=self.canvas_matriz.bbox("all"))
        self.canvas_matriz.xview_moveto(0)
        self.canvas_matriz.yview_moveto(0)

        self.canvas_grafo.delete("all")
        self._actualizar_opciones_nodos()
        self.dibujar_grafo(None)


    # =====================================================================
    #   LECTURA DE NOMBRES
    # =====================================================================

    def _leer_nombres(self):
        nombres_col = [
            e.get().strip() or f"v{idx+1}"
            for idx, e in enumerate(self.entradas_nombres_columnas)
        ]
        nombres_filas = [
            e.get().strip() or f"v{idx+1}"
            for idx, e in enumerate(self.entradas_nombres_filas)
        ]
        return nombres_col, nombres_filas


    def _asegurar_nombres_iguales(self):
        cols, rows = self._leer_nombres()
        if cols == rows:
            return True

        mensaje = (
            "Los nombres de columnas y filas no coinciden.\n"
            "Sí: copiar columnas a filas.\n"
            "No: copiar filas a columnas.\n"
            "Cancelar: abortar."
        )
        resp = messagebox.askyesnocancel(
            "Nombres inconsistentes", mensaje)

        if resp is None:
            return False

        if resp is True:
            for i, val in enumerate(cols):
                self.entradas_nombres_filas[i].delete(0, tk.END)
                self.entradas_nombres_filas[i].insert(0, val)
        else:
            for i, val in enumerate(rows):
                self.entradas_nombres_columnas[i].delete(0, tk.END)
                self.entradas_nombres_columnas[i].insert(0, val)

        self._actualizar_opciones_nodos()
        return True


    # =====================================================================
    #   LECTURA DE MATRIZ
    # =====================================================================

    def _leer_matriz(self):
        matriz = [[0.0]*self.tamano_n for _ in range(self.tamano_n)]
        for i in range(self.tamano_n):
            for j in range(self.tamano_n):
                t = self.entradas_matriz[i][j].get().strip()
                if t in ("", ".", "-"):
                    valor = 0.0
                else:
                    try:
                        valor = float(t)
                    except:
                        raise ValueError(
                            f"Valor inválido en la celda ({i+1},{j+1}): '{t}'")
                matriz[i][j] = valor
        return matriz


    def _actualizar_opciones_nodos(self):
        nombres, _ = self._leer_nombres() if self.tamano_n > 0 else ([], [])
        self.combo_origen["values"] = nombres
        self.combo_destino["values"] = nombres
        if nombres:
            self.combo_origen.set(nombres[0])
            self.combo_destino.set(nombres[min(1, len(nombres)-1)])


    # =====================================================================
    #   TEXTBOX DE EXPRESIÓN
    # =====================================================================

    def _set_text_expresion(self, contenido: str):
        if not hasattr(self, "text_expresion"):
            return
        self.text_expresion.configure(state="normal")
        self.text_expresion.delete("1.0", tk.END)
        if contenido:
            self.text_expresion.insert(tk.END, contenido)
        self.text_expresion.configure(state="disabled")


    # =====================================================================
    #   ACTUALIZAR EXPRESIÓN
    # =====================================================================

    def _actualizar_expresion(self, nombres_col, matriz, dirigido: bool):
        n = len(nombres_col)

        v_str = "V = (" + ", ".join(nombres_col) + ")"

        aristas = []
        if dirigido:
            for i in range(n):
                for j in range(n):
                    w = matriz[i][j]
                    if w != 0:
                        aristas.append((nombres_col[i], nombres_col[j], w))
        else:
            for i in range(n):
                if matriz[i][i] != 0:
                    aristas.append((nombres_col[i], nombres_col[i], matriz[i][i]))
                for j in range(i+1, n):
                    w = matriz[i][j]
                    if w != 0:
                        aristas.append((nombres_col[i], nombres_col[j], w))

        a_str = "A = (" + ", ".join(f"({u},{v},{w:g})"
                                    for u, v, w in aristas) + ")"

        lineas = [v_str, a_str, "", "Salidas por vértice:"]

        for i in range(n):
            salidas = []
            for j in range(n):
                w = matriz[i][j]
                if w != 0 and (dirigido or i != j):
                    salidas.append(f"{nombres_col[j]}({w:g})")
                elif not dirigido and i == j and matriz[i][i] != 0:
                    salidas.append(f"{nombres_col[j]}({w:g})")
            lineas.append(f"  {nombres_col[i]} -> " +
                          (", ".join(salidas) if salidas else "∅"))

        self._set_text_expresion("\n".join(lineas))


    # =====================================================================
    #   DIBUJAR GRAFO
    # =====================================================================

    def dibujar_grafo(self, camino_indices=None):
        if self.tamano_n <= 0:
            return

        if not self._asegurar_nombres_iguales():
            return

        try:
            nombres_col, _ = self._leer_nombres()
            matriz = self._leer_matriz()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        if self.es_dirigido.get():
            bad = validar_grafo_dirigido(matriz)
            if bad:
                i, j = bad
                messagebox.showwarning(
                    "Arista duplicada",
                    f"El par {nombres_col[i]}->{nombres_col[j]} tiene duplicado opuesto."
                )
                return

        dirigido = self.es_dirigido.get()

        # CORRECCIÓN FINAL:
        # ---- MANTENER PESOS NEGATIVOS EN GRAFOS NO DIRIGIDOS ----
        if not dirigido:
            for i in range(self.tamano_n):
                for j in range(i+1, self.tamano_n):
                    a = matriz[i][j]
                    b = matriz[j][i]

                    if a == 0 and b == 0:
                        w = 0
                    elif a == 0:
                        w = b
                    elif b == 0:
                        w = a
                    else:
                        w = a  # ambos existen: conservar a

                    matriz[i][j] = matriz[j][i] = w
        # ------------------------------------------------------------

        self._actualizar_expresion(nombres_col, matriz, dirigido)

        self.canvas_grafo.delete("all")
        self._label_positions = []

        ancho = self.canvas_grafo.winfo_width()
        alto = self.canvas_grafo.winfo_height()
        cx, cy = ancho//2, alto//2
        self.centro_canvas = (cx, cy)
        radio = int(min(ancho, alto) * 0.35)

        posiciones = []
        for k in range(self.tamano_n):
            ang = 2*math.pi*k / self.tamano_n
            x = cx + radio*math.cos(ang)
            y = cy + radio*math.sin(ang)
            posiciones.append((x, y))

        aristas_resaltadas = set()
        if camino_indices and len(camino_indices) >= 2:
            for a, b in zip(camino_indices[:-1], camino_indices[1:]):
                aristas_resaltadas.add((a, b))
                if not dirigido:
                    aristas_resaltadas.add((b, a))

        for i in range(self.tamano_n):
            for j in range(self.tamano_n):
                peso_ij = matriz[i][j]
                if peso_ij == 0 or i == j:
                    continue
                if not dirigido and j < i:
                    continue
                es_resaltada = (i, j) in aristas_resaltadas
                hay_retorno = dirigido and matriz[j][i] != 0
                self._dibujar_arista(i, j, posiciones,
                                     peso_ij,
                                     dirigido,
                                     hay_retorno,
                                     es_resaltada)

        for i in range(self.tamano_n):
            if matriz[i][i] != 0:
                self._dibujar_bucle_variable(
                    i, posiciones[i], (cx, cy), matriz[i][i], dirigido)

        for i, (x, y) in enumerate(posiciones):
            self._dibujar_nodo(i, x, y, nombres_col[i])

        self.ultimo_dirigido = dirigido
        self.ultima_matriz_norm = matriz
        self.ultimo_nombres = nombres_col
        self.ultima_posiciones = posiciones

        if self.nodo_seleccionado is not None:
            self._resaltar_nodo(self.nodo_seleccionado)


    # =====================================================================
    #   DIBUJAR NODO
    # =====================================================================

    def _dibujar_nodo(self, indice, x, y, nombre):
        radio = 18
        self.canvas_grafo.create_oval(
            x-radio, y-radio, x+radio, y+radio,
            fill="#f5f5ff", outline="#334", width=2,
            tags=("nodo", f"nodo_{indice}")
        )
        self.canvas_grafo.create_text(
            x, y, text=nombre,
            font=("Segoe UI", 10, "bold"),
            fill="#223",
            tags=("nodo", f"nodo_{indice}")
        )

        self.canvas_grafo.tag_bind(
            f"nodo_{indice}",
            "<Button-1>",
            lambda e, idx=indice: self._on_click_nodo(idx)
        )


    # =====================================================================
    #   DIBUJAR ETIQUETA
    # =====================================================================

    def _dibujar_etiqueta(self, x, y, texto, color_texto="#333",
                           font=("Segoe UI", 9)):
        tid = self.canvas_grafo.create_text(
            x, y, text=str(texto),
            font=font, fill=color_texto
        )
        bbox = self.canvas_grafo.bbox(tid)
        if bbox:
            x1, y1, x2, y2 = bbox
            r = self.canvas_grafo.create_rectangle(
                x1-2, y1-2, x2+2, y2+2,
                fill="white", outline=""
            )
            self.canvas_grafo.tag_raise(tid, r)
        return tid


    # =====================================================================
    #   EVENTO CLICK NODO
    # =====================================================================

    def _on_click_nodo(self, indice):
        self.nodo_seleccionado = indice
        self._resaltar_nodo(indice)
        self._mostrar_propiedades_nodo(indice)


    def _resaltar_nodo(self, indice):
        if self._id_resalte_nodo is not None:
            try:
                self.canvas_grafo.delete(self._id_resalte_nodo)
            except:
                pass

        if not self.ultima_posiciones:
            return

        x, y = self.ultima_posiciones[indice]
        radio = 22
        self._id_resalte_nodo = self.canvas_grafo.create_oval(
            x-radio, y-radio, x+radio, y+radio,
            outline="#0a84ff", width=3
        )


    def _mostrar_propiedades_nodo(self, indice):
        try:
            nombres = self.ultimo_nombres
            matriz = self.ultima_matriz_norm
            dirigido = self.ultimo_dirigido
            n = len(nombres)
            if not matriz:
                return
        except:
            return

        nombre = nombres[indice]

        if dirigido:
            ady_a = [(nombres[j], matriz[indice][j])
                     for j in range(n) if matriz[indice][j] != 0 and j != indice]
            ady_de = [(nombres[i], matriz[i][indice])
                      for i in range(n) if matriz[i][indice] != 0 and i != indice]

            lista_a = ", ".join(f"{w}({p:g})" for w, p in ady_a) or "∅"
            lista_de = ", ".join(f"{u}({p:g})" for u, p in ady_de) or "∅"

            texto = (
                f"Nodo seleccionado: {nombre}\n"
                f"Adyacentes desde {nombre}: {lista_a}\n"
                f"Adyacentes hacia {nombre}: {lista_de}"
            )
        else:
            vecinos = []
            for j in range(n):
                if j == indice:
                    if matriz[indice][indice] != 0:
                        vecinos.append((nombres[j], matriz[indice][j]))
                    continue
                if matriz[indice][j] != 0 or matriz[j][indice] != 0:
                    vecinos.append((nombres[j], matriz[indice][j]))

            lista = ", ".join(f"{w}({p:g})" for w, p in vecinos) or "∅"
            texto = (
                f"Nodo seleccionado: {nombre}\n"
                f"Nodos adyacentes: {lista}"
            )

        try:
            self.etiqueta_propiedades.config(text=texto)
        except:
            pass


    # =====================================================================
    #   DIBUJAR ARISTA
    # =====================================================================

    def _offset_perpendicular(self, x1, y1, x2, y2, distancia):
        return offset_perpendicular(x1, y1, x2, y2, distancia)

    def _bezier_q_punto_y_tangente(self, p0, c, p2, t):
        return bezier_q_punto_y_tangente(p0, c, p2, t)


    def _dibujar_bucle_variable(self, indice, posicion, centro, peso, dirigido):
        x, y = posicion
        cx, cy = centro
        ang = math.atan2(y - cy, x - cx)
        radio_nodo = 18
        tang_x = -math.sin(ang)
        tang_y = math.cos(ang)
        separacion = 24
        largo = 36

        sx = x + tang_x * radio_nodo
        sy = y + tang_y * radio_nodo
        out_x = math.cos(ang)
        out_y = math.sin(ang)

        c1x = sx + tang_x * separacion + out_x * (largo * 0.6)
        c1y = sy + tang_y * separacion + out_y * (largo * 0.6)
        c2x = sx - tang_x * separacion + out_x * (largo * 0.6)
        c2y = sy - tang_y * separacion + out_y * (largo * 0.6)

        ex = x + tang_x * (radio_nodo - 1)
        ey = y + tang_y * (radio_nodo - 1)

        self.canvas_grafo.create_line(
            sx, sy, c1x, c1y, c2x, c2y, ex, ey,
            smooth=True, width=2, fill="#666"
        )

        if dirigido:
            fx1 = ex - tang_x * 8
            fy1 = ey - tang_y * 8
            fx2 = ex - tang_x * 16
            fy2 = ey - tang_y * 16

            self.canvas_grafo.create_line(
                fx1, fy1, fx2, fy2,
                width=2, fill="#666",
                arrow=tk.LAST
            )

        lx = (c1x + c2x)/2 + out_x*10
        ly = (c1y + c2y)/2 + out_y*10
        lx, ly = self._ajustar_posicion_sin_solapamiento(lx, ly)
        self._dibujar_etiqueta(lx, ly, str(peso))


    def _dibujar_arista(self, i, j, posiciones,
                         peso, dirigido, hay_retorno, es_resaltada=False):
        x1, y1 = posiciones[i]
        x2, y2 = posiciones[j]

        def desplazar_borde(xa, ya, xb, yb, margen):
            dx, dy = xb - xa, yb - ya
            d = math.hypot(dx, dy) or 1.0
            ux, uy = dx/d, dy/d
            return xa + ux*margen, ya + uy*margen

        margen = 18
        sx, sy = desplazar_borde(x1, y1, x2, y2, margen)
        ex, ey = desplazar_borde(x2, y2, x1, y1, margen)

        ancho = 3 if es_resaltada else 2
        color_linea = "#d33" if es_resaltada else "#666"
        color_texto = "#b11" if es_resaltada else "#333"

        mx, my = (sx + ex)/2, (sy + ey)/2
        dx, dy = ex - sx, ey - sy
        d = math.hypot(dx, dy) or 1.0
        px, py = -dy/d, dx/d

        if dirigido and hay_retorno:
            cx, cy = self.centro_canvas
            hacia_fuera = (mx - cx)*px + (my - cy)*py
            signo_base = 1 if hacia_fuera >= 0 else -1

            signo = signo_base if i < j else -signo_base
            curv = 40

            cx1 = mx + signo*px*curv
            cy1 = my + signo*py*curv

            self.canvas_grafo.create_line(
                sx, sy, cx1, cy1, ex, ey,
                width=ancho, fill=color_linea,
                smooth=True,
                arrow=tk.LAST, arrowshape=(12, 14, 6),
                capstyle=tk.ROUND
            )

            t = 0.5
            bx, by, tdx, tdy = self._bezier_q_punto_y_tangente(
                (sx, sy), (cx1, cy1), (ex, ey), t
            )
            tn = math.hypot(tdx, tdy) or 1.0
            nx, ny = -tdy/tn, tdx/tn
            offset_perp = 12 * signo
            offset_along = 6

            bx += nx*offset_perp + (tdx/tn)*offset_along
            by += ny*offset_perp + (tdy/tn)*offset_along

            bx, by = self._ajustar_posicion_sin_solapamiento(bx, by)
            self._dibujar_etiqueta(bx, by, str(peso),
                                   color_texto=color_texto)

        else:
            self.canvas_grafo.create_line(
                sx, sy, ex, ey,
                width=ancho, fill=color_linea,
                arrow=(tk.LAST if dirigido else None),
                arrowshape=(12, 14, 6) if dirigido else None,
                capstyle=tk.ROUND
            )

            lx, ly = self._calcular_posicion_etiqueta_linea(sx, sy, ex, ey)
            self._dibujar_etiqueta(lx, ly, str(peso),
                                   color_texto=color_texto)


    def _calcular_posicion_etiqueta_linea(self, sx, sy, ex, ey):
        mx, my = (sx + ex)/2, (sy + ey)/2
        ox, oy = self._offset_perpendicular(sx, sy, ex, ey, 14)
        lx, ly = mx + ox, my + oy

        dx, dy = ex - sx, ey - sy
        dist = math.hypot(dx, dy) or 1.0
        ux, uy = dx/dist, dy/dist
        abs_dx, abs_dy = abs(dx), abs(dy)

        ratio = 1.6
        if abs_dx < 1e-6 and abs_dy < 1e-6:
            along = 0.0
        elif abs_dx * ratio < abs_dy:
            along = 16 if sy < ey else -16
        elif abs_dy * ratio < abs_dx:
            along = 16 if sx < ex else -16
        else:
            along = 12 if (sx + sy) <= (ex + ey) else -12

        lx += ux * along
        ly += uy * along

        return self._ajustar_posicion_sin_solapamiento(lx, ly)


    def _ajustar_posicion_sin_solapamiento(self, x, y):
        posiciones = getattr(self, "_label_positions", None)
        if posiciones is None:
            self._label_positions = []
            posiciones = self._label_positions

        min_dist = 22
        max_intentos = 8
        paso = 10
        intentos = 0

        while any((x - px)**2 + (y - py)**2 < min_dist**2 for px, py in posiciones) and intentos < max_intentos:
            ang = (intentos % 4) * (math.pi / 2)
            x += math.cos(ang) * paso
            y += math.sin(ang) * paso
            intentos += 1

        posiciones.append((x, y))
        return x, y


    # =====================================================================
    #   REDIBUJAR
    # =====================================================================

    def _redibujar_si_es_posible(self):
        if self.tamano_n > 0:
            try:
                self._leer_matriz()
            except:
                return
            self.dibujar_grafo(self.ultimo_camino_indices)


    # =====================================================================
    #   Dijkstra
    # =====================================================================

    def calcular_ruta_dijkstra(self):
        if self.tamano_n <= 0:
            messagebox.showwarning("Aviso", "Primero cree la matriz.")
            return

        if not self._asegurar_nombres_iguales():
            return

        try:
            nombres_col, _ = self._leer_nombres()
            matriz = self._leer_matriz()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        dirigido = self.es_dirigido.get()
        if not dirigido:
            for i in range(self.tamano_n):
                for j in range(i+1, self.tamano_n):
                    a = matriz[i][j]
                    b = matriz[j][i]

                    if a == 0 and b == 0:
                        w = 0
                    elif a == 0:
                        w = b
                    elif b == 0:
                        w = a
                    else:
                        w = a

                    matriz[i][j] = matriz[j][i] = w

        nombre_origen = self.combo_origen.get().strip()
        nombre_destino = self.combo_destino.get().strip()

        try:
            i_origen = nombres_col.index(nombre_origen)
            i_destino = nombres_col.index(nombre_destino)
        except ValueError:
            messagebox.showerror("Error", "Nombres inválidos.")
            return

        if i_origen == i_destino:
            messagebox.showinfo("Ruta trivial",
                                "Origen y destino son iguales. Distancia = 0.")
            self.ultimo_camino_indices = [i_origen]
            self.ultima_distancia = 0
            self.etiqueta_resultado.config(
                text=f"Camino: {nombre_origen} | Distancia: 0")
            self.dibujar_grafo([i_origen])
            return

        ady = construir_adyacencias(matriz, dirigido)
        dist, camino, tiene_pesos_neg = dijkstra(ady, i_origen, i_destino)

        if tiene_pesos_neg:
            self.ultimo_camino_indices = None
            self.ultima_distancia = None
            self.etiqueta_resultado.config(
                text="Dijkstra no admite pesos negativos.")
            messagebox.showwarning(
                "Pesos negativos",
                "Dijkstra no se puede usar cuando existen aristas con peso negativo.")
            self.dibujar_grafo(None)
            return

        if dist == float("inf") or not camino:
            self.ultimo_camino_indices = None
            self.ultima_distancia = None
            self.etiqueta_resultado.config(
                text="No existe ruta entre los nodos.")
            messagebox.showinfo("Sin ruta",
                                "No existe camino entre los nodos.")
            self.dibujar_grafo(None)
            return

        self.ultimo_camino_indices = camino
        self.ultima_distancia = dist

        camino_nombres = " → ".join(nombres_col[i] for i in camino)
        self.etiqueta_resultado.config(
            text=f"[Dijkstra] Camino: {camino_nombres} | Distancia: {dist:g}"
        )

        self.dibujar_grafo(camino)


    # =====================================================================
    #   Bellman-Ford
    # =====================================================================

    def calcular_bellman_ford(self):
        if self.tamano_n <= 0:
            messagebox.showwarning("Aviso", "Primero cree la matriz.")
            return

        if not self._asegurar_nombres_iguales():
            return

        try:
            nombres_col, _ = self._leer_nombres()
            matriz = self._leer_matriz()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        dirigido = self.es_dirigido.get()
        if not dirigido:
            for i in range(self.tamano_n):
                for j in range(i+1, self.tamano_n):
                    a = matriz[i][j]
                    b = matriz[j][i]

                    if a == 0 and b == 0:
                        w = 0
                    elif a == 0:
                        w = b
                    elif b == 0:
                        w = a
                    else:
                        w = a

                    matriz[i][j] = matriz[j][i] = w

        nombre_origen = self.combo_origen.get().strip()
        nombre_destino = self.combo_destino.get().strip()

        try:
            i_origen = nombres_col.index(nombre_origen)
            i_destino = nombres_col.index(nombre_destino)
        except ValueError:
            messagebox.showerror("Error", "Nombres inválidos.")
            return

        ady = construir_adyacencias(matriz, dirigido)
        dist, prev, ciclo_neg = bellman_ford(ady, i_origen)

        if ciclo_neg:
            messagebox.showerror(
                "Error",
                "El grafo contiene ciclos negativos. No se puede aplicar Bellman-Ford."
            )
            return

        if dist[i_destino] == float("inf"):
            self.ultimo_camino_indices = None
            self.ultima_distancia = None
            self.etiqueta_resultado.config(
                text="No existe ruta (Bellman-Ford).")
            self.dibujar_grafo(None)
            return

        camino = []
        nodo = i_destino
        while nodo != -1:
            camino.append(nodo)
            nodo = prev[nodo]
        camino.reverse()

        self.ultimo_camino_indices = camino
        self.ultima_distancia = dist[i_destino]

        camino_nombres = " → ".join(nombres_col[i] for i in camino)
        self.etiqueta_resultado.config(
            text=f"[Bellman-Ford] Camino: {camino_nombres} | Distancia: {dist[i_destino]:g}"
        )

        self.dibujar_grafo(camino)


    # =====================================================================
    #   PANEL DERECHO (INFO)
    # =====================================================================

    def _construir_zona_canvas(self):
        marco_derecho = ttk.Frame(self)
        marco_derecho.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True,
                           padx=(5, 10), pady=(5, 10))

        ttk.Label(marco_derecho, text="Visualización del Grafo").pack(
            side=tk.TOP, anchor="w")

        panel_texto = ttk.Frame(marco_derecho)
        panel_texto.pack(side=tk.BOTTOM, fill=tk.X, expand=False)

        self.etiqueta_propiedades = ttk.Label(
            panel_texto,
            text="Seleccione un nodo para ver sus propiedades.",
            foreground="#224",
            justify="left",
            wraplength=900
        )
        self.etiqueta_propiedades.pack(side=tk.TOP, anchor="w")

        self.etiqueta_resultado = ttk.Label(
            panel_texto, text="", foreground="#224")
        self.etiqueta_resultado.pack(side=tk.TOP, anchor="w", pady=(6, 0))

        ttk.Label(panel_texto, text="Expresión del grafo (V, A) y salidas por vértice:").pack(
            side=tk.TOP, anchor="w", pady=(4, 2))

        self.text_expresion = ScrolledText(
            panel_texto, height=10,
            wrap="word", font=("Segoe UI", 9))
        self.text_expresion.pack(side=tk.TOP, fill=tk.X, expand=False)
        self.text_expresion.configure(state="disabled")

        self.canvas_grafo = tk.Canvas(
            marco_derecho, bg="white",
            highlightthickness=1, highlightbackground="#ddd"
        )
        self.canvas_grafo.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
