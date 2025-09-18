import sys
from typing import Optional

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QCloseEvent
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
)

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from graficas import parse_salida_modelo, graficar
from groq_worker import GroqWorker


APP_MARGIN = 16
GAP_LG = 16
GAP_MD = 12
BOTON_ANCHO = 170
BOTON_ALTO = 48
LOGO_TAM = QSize(180, 180)
TEXTO_MIN_ALTO = 150
SALIDA_MIN_ALTO = 280


class VentanaMetodoGrafico(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Método Gráfico")
        self.resize(1200, 760)

        self.trabajador_ia: Optional[GroqWorker] = None

        self._construir_interfaz()
        self._pintar_placeholder_grafica()

    # ---------- Construcción UI ----------
    def _construir_interfaz(self) -> None:
        contenedor = QHBoxLayout(self)
        contenedor.setContentsMargins(APP_MARGIN, APP_MARGIN, APP_MARGIN, APP_MARGIN)
        contenedor.setSpacing(GAP_LG)

        columna_izq = self._construir_columna_izquierda()
        columna_der = self._construir_columna_derecha()

        contenedor.addLayout(columna_izq, stretch=3)
        contenedor.addLayout(columna_der, stretch=2)

        self._aplicar_estilos()

    def _construir_columna_izquierda(self) -> QVBoxLayout:
        columna = QVBoxLayout()
        columna.setSpacing(GAP_MD)

        titulo = QLabel("Optimización")
        titulo.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        titulo.setObjectName("tituloPrincipal")
        columna.addWidget(titulo)

        self.entrada_enunciado = QTextEdit()
        self.entrada_enunciado.setPlaceholderText("Escribe aquí el enunciado del problema…")
        self.entrada_enunciado.setMinimumHeight(TEXTO_MIN_ALTO)
        columna.addWidget(self.entrada_enunciado)

        self.marco_grafica = QFrame()
        self.marco_grafica.setFrameShape(QFrame.Box)
        self.marco_grafica.setLineWidth(2)
        self.marco_grafica.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout_grafica = QVBoxLayout(self.marco_grafica)
        layout_grafica.setContentsMargins(8, 8, 8, 8)

        self.figura = Figure(figsize=(6, 4))
        self.canvas = FigureCanvas(self.figura)
        layout_grafica.addWidget(self.canvas)
        columna.addWidget(self.marco_grafica, stretch=1)

        return columna

    def _construir_columna_derecha(self) -> QVBoxLayout:
        columna = QVBoxLayout()
        columna.setSpacing(GAP_LG)

        self.boton_resolver = QPushButton("Solucionar")
        self.boton_resolver.setFixedSize(BOTON_ANCHO, BOTON_ALTO)
        self.boton_resolver.clicked.connect(self._on_click_resolver)
        columna.addWidget(self.boton_resolver, alignment=Qt.AlignRight)

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

        return columna

    def _aplicar_estilos(self) -> None:
        self.setStyleSheet(
            """
            #tituloPrincipal { font-size: 22px; font-weight: 800; }
            #subtitulo { font-weight: 700; }
            QTextEdit {
                font-size: 14px;
                border-radius: 8px;
                padding: 8px;
            }
            QFrame {
                border-radius: 8px;
            }
            QPushButton {
                font-weight: 700;
                border-radius: 10px;
                padding: 8px 14px;
            }
            QPushButton:disabled {
                opacity: 0.6;
            }
            """
        )

    def _cargar_logo(self, ruta: str) -> None:
        pixmap = QPixmap(ruta)
        if pixmap.isNull():
            self.lbl_logo.setText("Logo")
            return
        ajustado = pixmap.scaled(
            self.marco_logo.size() - QSize(16, 16),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.lbl_logo.setPixmap(ajustado)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        # Reescalar logo si existe
        if self.lbl_logo.pixmap():
            self._cargar_logo("logo.png")

    # ---------- Interacciones ----------
    def _pintar_placeholder_grafica(self) -> None:
        eje = self.figura.add_subplot(111)
        eje.text(
            0.5,
            0.5,
            "Aquí se mostrará el gráfico\ncuando el modelo sea válido.",
            ha="center",
            va="center",
        )
        eje.set_axis_off()
        self.canvas.draw()

    def _on_click_resolver(self) -> None:
        enunciado = self.entrada_enunciado.toPlainText().strip()
        if not enunciado:
            QMessageBox.information(self, "Atención", "Escribe un enunciado del problema.")
            return

        self._bloquear_ui_en_proceso(True)
        self.salida_texto.clear()

        self.trabajador_ia = GroqWorker(problem_text=enunciado)
        self.trabajador_ia.finished.connect(self._al_terminar_exitoso)
        self.trabajador_ia.failed.connect(self._al_fallar)
        self.trabajador_ia.start()

    def _bloquear_ui_en_proceso(self, ocupado: bool) -> None:
        self.boton_resolver.setEnabled(not ocupado)
        self.boton_resolver.setText("Procesando…" if ocupado else "Solucionar")
        QApplication.setOverrideCursor(Qt.WaitCursor if ocupado else Qt.ArrowCursor)
        self.entrada_enunciado.setEnabled(not ocupado)

    # ---------- Callbacks del worker ----------
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
            self.canvas.draw()

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
        self.figura.clear()
        eje = self.figura.add_subplot(111)
        eje.text(0.5, 0.5, mensaje, ha="center", va="center")
        eje.set_axis_off()
        self.canvas.draw()

    # ---------- Ciclo de vida ----------
    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if self.trabajador_ia and self.trabajador_ia.isRunning():
            self.trabajador_ia.terminate()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = VentanaMetodoGrafico()
    w.show()
    sys.exit(app.exec())