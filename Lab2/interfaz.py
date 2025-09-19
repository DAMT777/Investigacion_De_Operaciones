from __future__ import annotations

import os
from typing import Optional

from PySide6.QtCore import Qt, QSize, QTimer, QEvent
from PySide6.QtGui import QPixmap, QCloseEvent, QAction
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QTextEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QSizePolicy,
    QMessageBox,
    QFileDialog,
    QSplitter,
    QToolBar,
    QStackedLayout,
)

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from graficas import parse_salida_modelo, graficar
from groq_worker import GroqWorker
from ocr_worker import OCRWorker
from config import APP_DARK_MODE

APP_MARGIN = 16
GAP_LG = 16
GAP_MD = 12
BOTON_ANCHO = 180
BOTON_ALTO = 44
LOGO_TAM = QSize(180, 180)
TEXTO_MIN_ALTO = 150
SALIDA_MIN_ALTO = 280

ASPECTO_GRAFICA = 2.4
CANVAS_ANCHO_MAX = 1100
GRAFICA_ALTO_MAX = 360


class VentanaMetodoGrafico(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Método Gráfico")
        self.resize(1220, 780)

        self.trabajador_ia: Optional[GroqWorker] = None
        self.trabajador_ocr: Optional[OCRWorker] = None
        self._preview_original: Optional[QPixmap] = None  # para escalar preview en resize

        self._construir_interfaz()
        self._pintar_placeholder_grafica()

        if APP_DARK_MODE:
            self._activar_modo_oscuro()

    # ---------- Construcción UI ----------
    def _construir_interfaz(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(APP_MARGIN, APP_MARGIN, APP_MARGIN, APP_MARGIN)
        root.setSpacing(GAP_LG)

        # Toolbar
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(18, 18))

        act_ocr = QAction("📷 Leer imagen…", self)
        act_ocr.triggered.connect(self._on_click_ocr)
        toolbar.addAction(act_ocr)

        act_limpiar = QAction("🧹 Limpiar", self)
        act_limpiar.triggered.connect(self._limpiar_todo)
        toolbar.addAction(act_limpiar)

        root.addWidget(toolbar)

        # Split principal 2|3
        splitter = QSplitter(Qt.Horizontal)

        cont_izq = QWidget()
        cont_der = QWidget()

        lay_izq = QVBoxLayout(cont_izq)
        lay_izq.setContentsMargins(0, 0, 0, 0)
        lay_izq.addLayout(self._construir_panel_izquierdo())

        lay_der = QVBoxLayout(cont_der)
        lay_der.setContentsMargins(0, 0, 0, 0)
        lay_der.addLayout(self._construir_panel_derecho())

        splitter.addWidget(cont_izq)
        splitter.addWidget(cont_der)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)

        root.addWidget(splitter, stretch=1)

        self._aplicar_estilos()

    def _construir_panel_izquierdo(self) -> QVBoxLayout:
        columna = QVBoxLayout()
        columna.setSpacing(GAP_MD)

        cab = QHBoxLayout()
        titulo = QLabel("Optimización — Método gráfico (2 variables)")
        titulo.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        titulo.setObjectName("tituloPrincipal")

        self.btn_resolver = QPushButton("▶ Solucionar")
        self.btn_resolver.setFixedSize(BOTON_ANCHO, BOTON_ALTO)
        self.btn_resolver.clicked.connect(self._on_click_resolver)

        cab.addWidget(titulo, stretch=1)
        cab.addWidget(self.btn_resolver, alignment=Qt.AlignRight)
        columna.addLayout(cab)

        self.entrada_enunciado = QTextEdit()
        self.entrada_enunciado.setPlaceholderText("Escribe aquí el enunciado del problema…")
        self.entrada_enunciado.setMinimumHeight(TEXTO_MIN_ALTO)
        self.entrada_enunciado.installEventFilter(self)  # para Ctrl+Enter
        columna.addWidget(self.entrada_enunciado)

        # === Bloque unificado: Preview OCR y Gráfica ===
        self.marco_grafica = QFrame()
        self.marco_grafica.setFrameShape(QFrame.Box)
        self.marco_grafica.setLineWidth(2)
        self.marco_grafica.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.marco_grafica.setMaximumHeight(GRAFICA_ALTO_MAX)

        lay_graf = QVBoxLayout(self.marco_grafica)
        lay_graf.setContentsMargins(8, 8, 8, 8)

        self.figura = Figure(figsize=(6, 4), constrained_layout=True)
        self.canvas = FigureCanvas(self.figura)

        self.lbl_preview = QLabel("Sin imagen")
        self.lbl_preview.setAlignment(Qt.AlignCenter)
        self.lbl_preview.setObjectName("previewBox")
        self.lbl_preview.setMinimumSize(200, 160)

        self.stack_grafica = QStackedLayout()
        self.stack_grafica.addWidget(self.lbl_preview)  # idx 0
        self.stack_grafica.addWidget(self.canvas)       # idx 1
        self.stack_grafica.setCurrentWidget(self.canvas)

        lay_graf.addLayout(self.stack_grafica)
        columna.addWidget(self.marco_grafica)

        return columna

    def _construir_panel_derecho(self) -> QVBoxLayout:
        columna = QVBoxLayout()
        columna.setSpacing(GAP_LG)

        # Marco del logo
        self.marco_logo = QFrame()
        self.marco_logo.setFrameShape(QFrame.Box)
        self.marco_logo.setLineWidth(2)
        self.marco_logo.setFixedSize(LOGO_TAM)

        layout_logo = QVBoxLayout(self.marco_logo)
        layout_logo.setContentsMargins(8, 8, 8, 8)

        self.lbl_logo = QLabel()
        self.lbl_logo.setAlignment(Qt.AlignCenter)
        layout_logo.addWidget(self.lbl_logo, alignment=Qt.AlignCenter)

        self._cargar_logo("logo.png")

        columna.addWidget(self.marco_logo, alignment=Qt.AlignRight)

        etiqueta_modelo = QLabel("Modelo extraído (IA)")
        etiqueta_modelo.setObjectName("subtitulo")
        columna.addWidget(etiqueta_modelo)

        self.salida_texto = QTextEdit()
        self.salida_texto.setReadOnly(True)
        self.salida_texto.setMinimumHeight(SALIDA_MIN_ALTO)
        self.salida_texto.setPlaceholderText(
            "Aquí verás la salida con Variables, FO, Restricciones y No negatividad…"
        )
        columna.addWidget(self.salida_texto, stretch=1)

        self.lbl_estado = QLabel("Listo.")
        self.lbl_estado.setObjectName("status")
        columna.addWidget(self.lbl_estado)

        return columna

    def _aplicar_estilos(self) -> None:
        self.setStyleSheet(
            """
            QWidget { font-size: 14px; }
            #tituloPrincipal { font-size: 20px; font-weight: 800; }
            #subtitulo { font-weight: 700; }
            #status { color: #6b7280; font-size: 12px; }
            #previewBox { border: 1px dashed #9ca3af; border-radius: 8px; padding: 6px; }

            QTextEdit {
                border: 1px solid #d1d5db;
                border-radius: 10px;
                padding: 10px;
                background: #ffffff;
            }
            QFrame {
                border-radius: 10px;
            }
            QPushButton {
                font-weight: 700;
                border-radius: 12px;
                padding: 8px 14px;
                background: #111827; color: #fff;
            }
            QPushButton:disabled { opacity: 0.75; }
            QToolBar { border: 0; }
            """
        )

    def _activar_modo_oscuro(self) -> None:
        self.setStyleSheet(self.styleSheet() + """
            QWidget { background: #0b0f14; color: #e5e7eb; }
            QTextEdit { background: #0f172a; color: #e5e7eb; border-color: #334155; }
            QFrame { border: 1px solid #334155; }
            QPushButton { background: #2563eb; }
            #status { color: #9ca3af; }
            #previewBox { border-color: #475569; }
        """)

    # ---------- Logo ----------
    def _cargar_logo(self, ruta_relativa: str) -> None:
        """
        Carga un logo opcional desde ruta relativa a este archivo .py.
        Si el archivo no existe o no se puede leer, deja el texto 'Logo'.
        """
        try:
            base = os.path.dirname(os.path.abspath(__file__))
            ruta_absoluta = os.path.join(base, ruta_relativa)

            pm = QPixmap(ruta_absoluta)
            if pm.isNull():
                self.lbl_logo.setText("Logo")
                self.lbl_logo.setPixmap(QPixmap())
                return

            size_disp = self.marco_logo.size() - QSize(16, 16)
            ajustado = pm.scaled(
                size_disp,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.lbl_logo.setPixmap(ajustado)
            self.lbl_logo.setText("")
        except Exception:
            self.lbl_logo.setText("Logo")
            self.lbl_logo.setPixmap(QPixmap())

    # ---------- Helpers de layout/preview ----------
    def _ajustar_aspecto_grafica(self) -> None:
        if not self.canvas or not self.marco_grafica:
            return
        alto = max(1, min(self.marco_grafica.height() - 16, GRAFICA_ALTO_MAX - 16))
        ancho_deseado = int(min(self.marco_grafica.width() - 16, alto * ASPECTO_GRAFICA, CANVAS_ANCHO_MAX))
        self.canvas.setFixedWidth(max(360, ancho_deseado))
        if self.stack_grafica.currentWidget() is self.lbl_preview and self._preview_original:
            self._colocar_preview_escalado()

    def _colocar_preview_escalado(self) -> None:
        if not self._preview_original:
            return
        area = self.marco_grafica.size() - QSize(24, 24)
        esc = self._preview_original.scaled(
            max(100, area.width()),
            max(100, area.height()),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.lbl_preview.setPixmap(esc)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)

        if getattr(self, "lbl_logo", None) is not None:
            self._cargar_logo("logo.png")
        self._ajustar_aspecto_grafica()

    # ---------- Interacciones ----------
    def _pintar_placeholder_grafica(self) -> None:
        self.stack_grafica.setCurrentWidget(self.canvas)
        self.figura.clear()
        eje = self.figura.add_subplot(111)
        eje.text(
            0.5, 0.5,
            "Aquí se mostrará el gráfico\ncuando el modelo sea válido.",
            ha="center", va="center", transform=eje.transAxes
        )
        eje.set_axis_off()
        self.canvas.draw_idle()
        self._ajustar_aspecto_grafica()

    def _flash_estado(self, mensaje: str, ms: int = 2300) -> None:
        self.lbl_estado.setText(mensaje)
        QTimer.singleShot(ms, lambda: self.lbl_estado.setText("Listo."))

    def eventFilter(self, obj, event) -> bool:
        if obj is self.entrada_enunciado and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Enter, Qt.Key_Return) and event.modifiers() & Qt.ControlModifier:
                self._on_click_resolver()
                return True
        return super().eventFilter(obj, event)

    def _on_click_resolver(self) -> None:
        enunciado = self.entrada_enunciado.toPlainText().strip()
        if not enunciado:
            QMessageBox.information(self, "Atención", "Escribe un enunciado del problema.")
            return

        # Si estaba visible la preview, volvemos al canvas
        if self.stack_grafica.currentWidget() is self.lbl_preview:
            self.lbl_preview.clear()
            self.stack_grafica.setCurrentWidget(self.canvas)


        if self.trabajador_ia and self.trabajador_ia.isRunning():
            self._flash_estado("Ya hay un proceso en ejecución…")
            return

        self._bloquear_ui_en_proceso(True)
        self.salida_texto.clear()

        self.trabajador_ia = GroqWorker(problem_text=enunciado)
        self.trabajador_ia.finished.connect(self._al_terminar_exitoso)
        self.trabajador_ia.failed.connect(self._al_fallar)
        self.trabajador_ia.start()

    def _bloquear_ui_en_proceso(self, ocupado: bool) -> None:
        self.btn_resolver.setEnabled(not ocupado)
        self.btn_resolver.setText("⏳ Procesando…" if ocupado else "▶ Solucionar")
        if ocupado:
            QApplication.setOverrideCursor(Qt.WaitCursor)
        else:
            QApplication.restoreOverrideCursor()
        self.entrada_enunciado.setEnabled(not ocupado)

    # ---------- OCR ----------
    def _on_click_ocr(self) -> None:
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Selecciona una imagen", "",
            "Imágenes (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)"
        )
        if not ruta:
            return
        self._mostrar_preview(ruta)
        self._correr_ocr(ruta)

    def _mostrar_preview(self, ruta: str) -> None:
        pm = QPixmap(ruta)
        if pm.isNull():
            self._flash_estado("No se pudo cargar la imagen.")
            return
        self._preview_original = pm
        self._colocar_preview_escalado()
        self.stack_grafica.setCurrentWidget(self.lbl_preview)

    def _correr_ocr(self, ruta: str) -> None:
        if self.trabajador_ocr and self.trabajador_ocr.isRunning():
            self._flash_estado("OCR en curso…")
            return
        self._flash_estado("Leyendo imagen con OCR…")
        self.trabajador_ocr = OCRWorker(ruta)
        self.trabajador_ocr.finished_ok.connect(self._ocr_ok)
        self.trabajador_ocr.finished_error.connect(self._ocr_error)
        self.trabajador_ocr.start()

    def _ocr_ok(self, texto: str) -> None:
        actual = self.entrada_enunciado.toPlainText().strip()
        nuevo = (actual + "\n\n" if actual else "") + texto.strip()
        self.entrada_enunciado.setPlainText(nuevo)
        self._flash_estado("OCR completado.")

    def _ocr_error(self, msg: str) -> None:
        QMessageBox.warning(self, "OCR", f"No se pudo leer la imagen:\n{msg}")
        self._flash_estado("Falló el OCR.")

    # ---------- Callbacks del worker IA ----------
    def _al_terminar_exitoso(self, texto_modelo: str) -> None:
        self.salida_texto.setPlainText(texto_modelo)
        self._bloquear_ui_en_proceso(False)
        self.trabajador_ia = None

        if ("Función Objetivo" not in texto_modelo) or ("Restricciones" not in texto_modelo):
            self._mostrar_mensaje_grafica(
                "No se detectó un modelo válido para graficar.\n"
                "Asegúrate de que existan las secciones:\n"
                "‘Función Objetivo’ y ‘Restricciones’."
            )
            return

        try:
            datos = parse_salida_modelo(texto_modelo)

            self.figura.clear()
            eje = self.figura.add_subplot(111)
            resultado = graficar(
                eje,
                datos["restr"],
                datos["obj"],
                datos["sentido"],
                titulo="Región factible y solución",
            )
            self.canvas.draw_idle()
            self._ajustar_aspecto_grafica()

            if resultado:
                vertices = resultado["vertices"]
                punto_optimo = resultado["optimo"]["punto"]
                valor_optimo = resultado["optimo"]["valor"]
                coef_x, coef_y = datos["obj"]

                vertices_fmt = ", ".join(f"({x:.2f}, {y:.2f})" for x, y in vertices)
                analisis = [
                    "\n📊 Análisis de la solución (calculado por la app):",
                    f"- Vértices factibles: {vertices_fmt}",
                    f"- Solución óptima: x* = {punto_optimo[0]:.2f}, y* = {punto_optimo[1]:.2f}",
                    f"- Valor óptimo Z* = {valor_optimo:.2f}   (Z = {coef_x}*x + {coef_y}*y)",
                ]
                self.salida_texto.append("\n".join(analisis))
            else:
                self.salida_texto.append(
                    "\n📊 Análisis de la solución (calculado por la app):\n"
                    "- Región factible vacía o no acotada."
                )

        except Exception as exc:  # noqa: BLE001
            self._mostrar_mensaje_grafica("Ocurrió un error al graficar.")
            self.salida_texto.append(f"\n[Error] No se pudo calcular el análisis:\n{exc}")

    def _al_fallar(self, mensaje_error: str) -> None:
        self.salida_texto.setPlainText(f"Error al llamar a Groq:\n{mensaje_error}")
        self._bloquear_ui_en_proceso(False)
        self.trabajador_ia = None

    def _mostrar_mensaje_grafica(self, mensaje: str) -> None:
        self.stack_grafica.setCurrentWidget(self.canvas)
        self.figura.clear()
        eje = self.figura.add_subplot(111)
        eje.text(0.5, 0.5, mensaje, ha="center", va="center", transform=eje.transAxes)
        eje.set_axis_off()
        self.canvas.draw_idle()
        self._ajustar_aspecto_grafica()

    def _limpiar_todo(self) -> None:
        self.entrada_enunciado.clear()
        self.salida_texto.clear()
        self._preview_original = None
        self.lbl_preview.clear()
        self._pintar_placeholder_grafica()
        self._flash_estado("Limpio.")

    # ---------- Ciclo de vida ----------
    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if self.trabajador_ia and self.trabajador_ia.isRunning():
            self.trabajador_ia.terminate()
        if self.trabajador_ocr and self.trabajador_ocr.isRunning():
            self.trabajador_ocr.terminate()
        super().closeEvent(event)
