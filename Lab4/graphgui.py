import math
import tkinter as tk
from tkinter import ttk, messagebox

from graph_model import validar_grafo_dirigido, construir_adyacencias, dijkstra
from graph_drawer import offset_perpendicular, bezier_q_punto_y_tangente

class InterfazGrafo(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Práctica 4 - Grafos y Dijkstra")
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

        self._construir_controles_superiores()
        self._construir_zona_matriz()
        self._construir_zona_canvas()

        self.canvas_grafo.bind("<Configure>", lambda e: self._redibujar_si_es_posible())

    def _construir_controles_superiores(self):
        marco_superior = ttk.Frame(self, padding=(10, 10))
        marco_superior.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(marco_superior, text="Tamaño n:").pack(side=tk.LEFT)
        self.entrada_n = ttk.Entry(marco_superior, width=5)
        self.entrada_n.pack(side=tk.LEFT, padx=(5, 10))
        self.entrada_n.insert(0, "4")
        self.entrada_n.bind("<FocusOut>", lambda e: self.crear_matriz())
        self.entrada_n.bind("<Return>", lambda e: self.crear_matriz())

        ttk.Button(marco_superior, text="Crear matriz", command=self.crear_matriz).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Checkbutton(marco_superior, text="Dirigido", variable=self.es_dirigido).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(marco_superior, text="Dibujar grafo", command=self.dibujar_grafo).pack(side=tk.LEFT, padx=(0, 20))

        ttk.Label(marco_superior, text="Origen:").pack(side=tk.LEFT)
        self.combo_origen = ttk.Combobox(marco_superior, state="readonly", width=12, values=[])
        self.combo_origen.pack(side=tk.LEFT, padx=(5, 10))

        ttk.Label(marco_superior, text="Destino:").pack(side=tk.LEFT)
        self.combo_destino = ttk.Combobox(marco_superior, state="readonly", width=12, values=[])
        self.combo_destino.pack(side=tk.LEFT, padx=(5, 10))

        ttk.Button(marco_superior, text="Calcular ruta (Dijkstra)", command=self.calcular_ruta_dijkstra).pack(side=tk.LEFT)

        mensaje_ayuda = (
            "Instrucciones: ponga nombres de nodos en la fila superior y columna izquierda.\n"
            "Ingrese pesos en la matriz (vacío o 0 = sin arista). Marque 'Dirigido' si aplica.\n"
            "Luego elija Origen/Destino y presione 'Calcular ruta (Dijkstra)'."
        )
        ttk.Label(self, text=mensaje_ayuda, foreground="#555", padding=(10, 4)).pack(side=tk.TOP, anchor="w")

    def _construir_zona_matriz(self):
        contenedor = ttk.Frame(self)
        contenedor.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(10, 5), pady=(5, 10))

        self.canvas_matriz = tk.Canvas(contenedor, width=540, height=540, highlightthickness=1, highlightbackground="#ddd")
        self.canvas_matriz.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        barra_vertical = ttk.Scrollbar(contenedor, orient="vertical", command=self.canvas_matriz.yview)
        barra_vertical.pack(side=tk.RIGHT, fill="y")

        barra_horizontal = ttk.Scrollbar(contenedor, orient="horizontal", command=self.canvas_matriz.xview)
        barra_horizontal.pack(side=tk.BOTTOM, fill="x")

        self.canvas_matriz.configure(yscrollcommand=barra_vertical.set, xscrollcommand=barra_horizontal.set)

        self.marco_interno_matriz = ttk.Frame(self.canvas_matriz)
        self.ventana_matriz = self.canvas_matriz.create_window((0, 0), window=self.marco_interno_matriz, anchor="nw")
        self.marco_interno_matriz.bind("<Configure>", self._ajustar_scroll_matriz)

    def _construir_zona_canvas(self):
        marco_derecho = ttk.Frame(self)
        marco_derecho.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 10), pady=(5, 10))

        ttk.Label(marco_derecho, text="Visualización del Grafo").pack(side=tk.TOP, anchor="w")

        self.canvas_grafo = tk.Canvas(marco_derecho, bg="white", highlightthickness=1, highlightbackground="#ddd")
        self.canvas_grafo.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.etiqueta_resultado = ttk.Label(marco_derecho, text="", foreground="#224")
        self.etiqueta_resultado.pack(side=tk.TOP, anchor="w", pady=(6, 0))

    def _ajustar_scroll_matriz(self, evento):
        self.canvas_matriz.configure(scrollregion=self.canvas_matriz.bbox("all"))
        self.canvas_matriz.itemconfig(self.ventana_matriz, width=max(evento.width, self.marco_interno_matriz.winfo_reqwidth()))
        self.canvas_matriz.itemconfig(self.ventana_matriz, height=max(evento.height, self.marco_interno_matriz.winfo_reqheight()))

    def crear_matriz(self):
        try:
            n = int(self.entrada_n.get())
            if n <= 0 or n > 50:
                raise ValueError
            self.tamano_n = n
        except ValueError:
            messagebox.showerror("Error", "n debe ser un entero entre 1 y 50.")
            return

        self.entradas_nombres_columnas.clear()
        self.entradas_nombres_filas.clear()
        self.entradas_matriz.clear()
        self.ultimo_camino_indices = None
        self.ultima_distancia = None
        self.etiqueta_resultado.config(text="")

        try:
            self.canvas_matriz.delete(self.ventana_matriz)
        except Exception:
            pass
        for w in self.marco_interno_matriz.winfo_children():
            w.destroy()
        self.marco_interno_matriz.destroy()

        self.marco_interno_matriz = ttk.Frame(self.canvas_matriz)
        self.ventana_matriz = self.canvas_matriz.create_window((0, 0), window=self.marco_interno_matriz, anchor="nw")
        self.marco_interno_matriz.bind("<Configure>", self._ajustar_scroll_matriz)

        nombres_por_defecto = [f"v{i+1}" for i in range(self.tamano_n)]

        ttk.Label(self.marco_interno_matriz, text="").grid(row=0, column=0, padx=4, pady=4)

        for j in range(self.tamano_n):
            entrada = ttk.Entry(self.marco_interno_matriz, width=12, justify="center")
            entrada.grid(row=0, column=j+1, padx=2, pady=2)
            entrada.insert(0, nombres_por_defecto[j])
            self.entradas_nombres_columnas.append(entrada)

        for i in range(self.tamano_n):
            entrada_fila = ttk.Entry(self.marco_interno_matriz, width=12, justify="center")
            entrada_fila.grid(row=i+1, column=0, padx=2, pady=2)
            entrada_fila.insert(0, nombres_por_defecto[i])
            self.entradas_nombres_filas.append(entrada_fila)

            fila_celdas = []
            for j in range(self.tamano_n):
                entrada_peso = ttk.Entry(self.marco_interno_matriz, width=7, justify="center")
                entrada_peso.grid(row=i+1, column=j+1, padx=1, pady=1)
                if i == j:
                    entrada_peso.insert(0, "0")
                fila_celdas.append(entrada_peso)
            self.entradas_matriz.append(fila_celdas)

        self.canvas_matriz.update_idletasks()
        reqw = self.marco_interno_matriz.winfo_reqwidth()
        reqh = self.marco_interno_matriz.winfo_reqheight()
        self.canvas_matriz.itemconfig(self.ventana_matriz, width=reqw, height=reqh)
        self.canvas_matriz.configure(scrollregion=self.canvas_matriz.bbox("all"))
        self.canvas_matriz.xview_moveto(0)
        self.canvas_matriz.yview_moveto(0)

        self.canvas_grafo.delete("all")
        self._actualizar_opciones_nodos()
        self.dibujar_grafo(None)

    def _leer_nombres(self):
        nombres_columnas = [e.get().strip() or f"v{idx+1}" for idx, e in enumerate(self.entradas_nombres_columnas)]
        nombres_filas = [e.get().strip() or f"v{idx+1}" for idx, e in enumerate(self.entradas_nombres_filas)]
        return nombres_columnas, nombres_filas

    def _asegurar_nombres_iguales(self):
        """Verifica que los nombres de columnas y filas sean iguales en orden.
        Si no lo son, pregunta al usuario si quiere:
         - copiar columnas -> filas
         - copiar filas -> columnas
         - cancelar la operación
        Retorna True si se asegura la igualdad (o ya eran iguales), False si el usuario canceló.
        """
        cols, rows = self._leer_nombres()
        if cols == rows:
            return True

        # Construir mensaje y opciones
        mensaje = (
            "Los nombres de las columnas y filas no coinciden.\n"
            "¿Desea sincronizarlos?\n\n"
            "Sí: copiar nombres de columnas a filas.\n"
            "No: copiar nombres de filas a columnas.\n"
            "Cancelar: abortar la operación."
        )
        resp = messagebox.askyesnocancel("Nombres inconsistentes", mensaje)
        if resp is None:
            return False
        if resp is True:
            # copiar columnas a filas
            for idx, val in enumerate(cols):
                if idx < len(self.entradas_nombres_filas):
                    self.entradas_nombres_filas[idx].delete(0, tk.END)
                    self.entradas_nombres_filas[idx].insert(0, val)
        else:
            # copiar filas a columnas
            for idx, val in enumerate(rows):
                if idx < len(self.entradas_nombres_columnas):
                    self.entradas_nombres_columnas[idx].delete(0, tk.END)
                    self.entradas_nombres_columnas[idx].insert(0, val)

        # Actualizar combos y devolver éxito
        self._actualizar_opciones_nodos()
        return True

    def _leer_matriz(self):
        matriz = [[0.0]*self.tamano_n for _ in range(self.tamano_n)]
        for i in range(self.tamano_n):
            for j in range(self.tamano_n):
                texto = self.entradas_matriz[i][j].get().strip()
                if texto in ("", ".", "-"):
                    valor = 0.0
                else:
                    try:
                        valor = float(texto)
                    except ValueError:
                        raise ValueError(f"Peso inválido en ({i+1},{j+1}): '{texto}'")
                matriz[i][j] = valor
        return matriz

    def _actualizar_opciones_nodos(self):
        nombres, _ = self._leer_nombres() if self.tamano_n > 0 else ([], [])
        self.combo_origen["values"] = nombres
        self.combo_destino["values"] = nombres
        if nombres:
            self.combo_origen.set(nombres[0])
            self.combo_destino.set(nombres[min(1, len(nombres)-1)])

 
    def dibujar_grafo(self, camino_indices=None):
        if self.tamano_n <= 0:
            messagebox.showwarning("Aviso", "Primero cree la matriz (ingrese n y presione 'Crear matriz').")
            return

        # Asegurar que nombres de columnas y filas coincidan o permitir sincronizarlos
        if not self._asegurar_nombres_iguales():
            return

        try:
            nombres_col, _ = self._leer_nombres()
            matriz = self._leer_matriz()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

 
        if self.es_dirigido.get():
            bad_pair = self._validar_grafo_dirigido(matriz)
            if bad_pair is not None:
                i, j = bad_pair
                nombres, _ = self._leer_nombres()
                messagebox.showwarning(
                    "Arista duplicada en dirigido",
                    f"En grafo dirigido no se permite que <{nombres[i]},{nombres[j]}> sea igual a <{nombres[j]},{nombres[i]}>.\n"
                    "Corrija uno de los dos valores."
                )
                return

        dirigido = self.es_dirigido.get()
        if not dirigido:
            for i in range(self.tamano_n):
                for j in range(i+1, self.tamano_n):
                    w = max(matriz[i][j], matriz[j][i])
                    matriz[i][j] = matriz[j][i] = w


        if dirigido:
            bad_pair = self._validar_grafo_dirigido(matriz)
            if bad_pair is not None:
                i, j = bad_pair
                nombres, _ = self._leer_nombres()
                messagebox.showwarning(
                    "Arista duplicada en dirigido",
                    f"En grafo dirigido no se permite que <{nombres[i]},{nombres[j]}> sea igual a <{nombres[j]},{nombres[i]}>.\n"
                    "Corrija uno de los dos valores."
                )
                return

        self.canvas_grafo.delete("all")

        ancho = self.canvas_grafo.winfo_width()
        alto = self.canvas_grafo.winfo_height()
        cx, cy = ancho // 2, alto // 2
        self.centro_canvas = (cx, cy)
        radio = int(min(ancho, alto) * 0.35)

        posiciones = []
        for k in range(self.tamano_n):
            angulo = 2 * math.pi * k / self.tamano_n
            x = cx + radio * math.cos(angulo)
            y = cy + radio * math.sin(angulo)
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
                self._dibujar_arista(i, j, posiciones, peso_ij, dirigido, hay_retorno, es_resaltada)

        for i in range(self.tamano_n):
            if matriz[i][i] != 0:
                self._dibujar_bucle_variable(i, posiciones[i], (cx, cy), matriz[i][i], dirigido)

        for i, (x, y) in enumerate(posiciones):
            self._dibujar_nodo(x, y, nombres_col[i])

    def _dibujar_nodo(self, x, y, nombre):
        radio = 18
        self.canvas_grafo.create_oval(x - radio, y - radio, x + radio, y + radio,
                                      fill="#f5f5ff", outline="#334", width=2)
        self.canvas_grafo.create_text(x, y, text=nombre, font=("Segoe UI", 10, "bold"), fill="#223")

    def _dibujar_etiqueta(self, x, y, texto, color_texto="#333", font=("Segoe UI", 9)):
        """Dibuja una etiqueta con pequeño fondo blanco para mejorar contraste.
        Crea primero el texto para conocer su bbox, luego un rectángulo debajo.
        """
        tid = self.canvas_grafo.create_text(x, y, text=str(texto), font=font, fill=color_texto)
        bbox = self.canvas_grafo.bbox(tid)
        if bbox:
            x1, y1, x2, y2 = bbox
            pad = 2
            rid = self.canvas_grafo.create_rectangle(x1 - pad, y1 - pad, x2 + pad, y2 + pad,
                                                     fill="white", outline="", width=0)
            # Asegurar orden: rectángulo debajo del texto.
            self.canvas_grafo.tag_raise(tid, rid)
        return tid

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
        tang_y =  math.cos(ang)
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
        self.canvas_grafo.create_line(sx, sy, c1x, c1y, c2x, c2y, ex, ey,
                                      smooth=True, width=2, fill="#666")
        if dirigido:
            fx1 = ex - tang_x * 8; fy1 = ey - tang_y * 8
            fx2 = ex - tang_x * 16; fy2 = ey - tang_y * 16
            self.canvas_grafo.create_line(fx1, fy1, fx2, fy2, width=2, fill="#666", arrow=tk.LAST)
        lx = (c1x + c2x) / 2 + out_x * 10
        ly = (c1y + c2y) / 2 + out_y * 10
        self._dibujar_etiqueta(lx, ly, str(peso), color_texto="#333")

    def _dibujar_arista(self, i, j, posiciones, peso, dirigido, hay_retorno, es_resaltada=False):
        x1, y1 = posiciones[i]
        x2, y2 = posiciones[j]

        def desplazar_borde(xa, ya, xb, yb, margen):
            dx, dy = xb - xa, yb - ya
            d = math.hypot(dx, dy) or 1.0
            ux, uy = dx / d, dy / d
            return xa + ux * margen, ya + uy * margen

        margen = 18
        sx, sy = desplazar_borde(x1, y1, x2, y2, margen)
        ex, ey = desplazar_borde(x2, y2, x1, y1, margen)

        ancho_linea = 3 if es_resaltada else 2
        color_linea = "#d33" if es_resaltada else "#666"
        color_texto = "#b11" if es_resaltada else "#333"

        
        mx, my = (sx + ex) / 2, (sy + ey) / 2
        dx, dy = ex - sx, ey - sy
        d = math.hypot(dx, dy) or 1.0
        px, py = -dy / d, dx / d 

        if dirigido and hay_retorno:

            # Definir lado de curvatura respecto al centro para evitar solapamientos
            cx, cy = self.centro_canvas
            hacia_fuera = (mx - cx) * px + (my - cy) * py
            signo_base = 1 if hacia_fuera >= 0 else -1

            # Poner aristas opuestas en lados opuestos: i<j a un lado, j<i al otro
            signo = signo_base if i < j else -signo_base
            curvatura = 40  # magnitud de desplazamiento del punto de control

            cx1 = mx + signo * px * curvatura
            cy1 = my + signo * py * curvatura

            self.canvas_grafo.create_line(
                sx, sy, cx1, cy1, ex, ey,
                width=ancho_linea, fill=color_linea, smooth=True,
                arrow=tk.LAST, arrowshape=(12, 14, 6), capstyle=tk.ROUND
            )

            # Etiqueta: a mitad de la curva, con desplazamiento siguiendo el mismo lado
            t = 0.5
            bx, by, tdx, tdy = self._bezier_q_punto_y_tangente((sx, sy), (cx1, cy1), (ex, ey), t)
            tn = math.hypot(tdx, tdy) or 1.0
            nx, ny = -tdy / tn, tdx / tn
            offset_perp = 12 * signo  # mismo lado que la curvatura
            offset_along = 6
            bx += nx * offset_perp + (tdx / tn) * offset_along
            by += ny * offset_perp + (tdy / tn) * offset_along
            self._dibujar_etiqueta(bx, by, str(peso), color_texto=color_texto)

        else:
            self.canvas_grafo.create_line(sx, sy, ex, ey,
                                          width=ancho_linea, fill=color_linea,
                                          arrow=tk.LAST if dirigido else None,
                                          arrowshape=(12, 14, 6) if dirigido else None,
                                          capstyle=tk.ROUND)
            ox, oy = self._offset_perpendicular(sx, sy, ex, ey, 10)
            self._dibujar_etiqueta(mx + ox, my + oy, str(peso), color_texto=color_texto)

    def _redibujar_si_es_posible(self):
        if self.tamano_n > 0:
            try:
                _ = self._leer_matriz()
            except Exception:
                return
            self.dibujar_grafo(self.ultimo_camino_indices)

    def _validar_grafo_dirigido(self, matriz):
        return validar_grafo_dirigido(matriz)

    @staticmethod
    def _construir_adyacencias(matriz, dirigido):
        return construir_adyacencias(matriz, dirigido)

    @staticmethod
    def _dijkstra(adyacencias, indice_origen, indice_destino):
        return dijkstra(adyacencias, indice_origen, indice_destino)

    def calcular_ruta_dijkstra(self):
        if self.tamano_n <= 0:
            messagebox.showwarning("Aviso", "Primero cree la matriz (ingrese n y presione 'Crear matriz').")
            return

        # Validar/sincronizar nombres antes de leer la matriz
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
                    w = max(matriz[i][j], matriz[j][i])
                    matriz[i][j] = matriz[j][i] = w

        nombre_origen = self.combo_origen.get().strip()
        nombre_destino = self.combo_destino.get().strip()
        if not nombre_origen or not nombre_destino:
            messagebox.showwarning("Aviso", "Seleccione nodos de Origen y Destino.")
            return

        try:
            indice_origen = nombres_col.index(nombre_origen)
            indice_destino = nombres_col.index(nombre_destino)
        except ValueError:
            messagebox.showerror("Error", "Los nombres seleccionados no existen en la matriz.")
            return

        if indice_origen == indice_destino:
            messagebox.showinfo("Ruta trivial", "Origen y destino son el mismo nodo. Distancia = 0.")
            self.ultimo_camino_indices = [indice_origen]
            self.ultima_distancia = 0.0
            self.etiqueta_resultado.config(text=f"Camino: {nombre_origen}  |  Distancia: 0")
            self.dibujar_grafo(self.ultimo_camino_indices)
            return

        adyacencias = self._construir_adyacencias(matriz, dirigido)
        distancia, camino_indices = self._dijkstra(adyacencias, indice_origen, indice_destino)

        if distancia == float("inf") or not camino_indices:
            self.ultimo_camino_indices = None
            self.ultima_distancia = None
            self.etiqueta_resultado.config(text="No existe camino entre los nodos seleccionados.")
            messagebox.showinfo("Sin ruta", "No existe camino entre los nodos seleccionados.")
            self.dibujar_grafo(None)
            return

        self.ultimo_camino_indices = camino_indices
        self.ultima_distancia = distancia
        camino_nombres = " → ".join(nombres_col[i] for i in camino_indices)
        self.etiqueta_resultado.config(text=f"Camino: {camino_nombres}  |  Distancia total: {distancia:g}")
        self.dibujar_grafo(self.ultimo_camino_indices)

