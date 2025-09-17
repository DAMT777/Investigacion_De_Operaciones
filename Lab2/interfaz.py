import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QTextEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from graficas import parse_salida_modelo, graficar
from groq_worker import GroqWorker


class VentanaMetodoGrafico(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Método Gráfico")
        self.resize(1200, 760)

        self.worker: GroqWorker | None = None

        root = QHBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)


        col_izq = QVBoxLayout()
        col_izq.setSpacing(12)

        lbl_titulo = QLabel("Optimización")
        lbl_titulo.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        lbl_titulo.setStyleSheet("font-size: 22px; font-weight: 800;")
        col_izq.addWidget(lbl_titulo)


        self.txt_problema = QTextEdit()
        self.txt_problema.setPlaceholderText("Escribe aquí el enunciado del problema…")
        self.txt_problema.setMinimumHeight(150)
        col_izq.addWidget(self.txt_problema)

        self.canvas_frame = QFrame()
        self.canvas_frame.setFrameShape(QFrame.Box)
        self.canvas_frame.setLineWidth(2)
        self.canvas_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        canvas_layout = QVBoxLayout(self.canvas_frame)
        canvas_layout.setContentsMargins(8, 8, 8, 8)

        self.figure = Figure(figsize=(6, 4))
        self.canvas = FigureCanvas(self.figure)
        canvas_layout.addWidget(self.canvas)

        col_izq.addWidget(self.canvas_frame, stretch=1)

        col_der = QVBoxLayout()
        col_der.setSpacing(16)

        self.btn_solucionar = QPushButton("Solucionar")
        self.btn_solucionar.setFixedSize(170, 48)
        self.btn_solucionar.clicked.connect(self.on_solucionar)
        col_der.addWidget(self.btn_solucionar, alignment=Qt.AlignRight)

        logo_frame = QFrame()
        logo_frame.setFrameShape(QFrame.Box)
        logo_frame.setLineWidth(2)
        logo_frame.setFixedSize(180, 180)

        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setContentsMargins(8, 8, 8, 8)

        lbl_logo = QLabel()
        lbl_logo.setAlignment(Qt.AlignCenter)

        pixmap = QPixmap("logo.png")
        if not pixmap.isNull():
            pm = pixmap.scaled(
                logo_frame.size() - QSize(16, 16),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            lbl_logo.setPixmap(pm)
        else:
            lbl_logo.setText("Logo")

        logo_layout.addWidget(lbl_logo, alignment=Qt.AlignCenter)
        col_der.addWidget(logo_frame, alignment=Qt.AlignRight)

        lbl_modelo = QLabel("Modelo extraído (IA)")
        lbl_modelo.setStyleSheet("font-weight: bold;")
        col_der.addWidget(lbl_modelo)

        self.txt_salida = QTextEdit()
        self.txt_salida.setReadOnly(True)
        self.txt_salida.setMinimumHeight(280)
        self.txt_salida.setPlaceholderText(
            "Aquí verás la salida con Variables, FO, Restricciones y No negatividad…"
        )
        col_der.addWidget(self.txt_salida, stretch=1)


        root.addLayout(col_izq, stretch=3)
        root.addLayout(col_der, stretch=2)

        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, "Aquí se mostrará el gráfico\ncuando el modelo sea válido.",
                ha="center", va="center")
        ax.set_axis_off()
        self.canvas.draw()

    def on_solucionar(self):
        if not self.txt_problema.toPlainText().strip():
            QMessageBox.information(
                self,
                "Atención",
                "Escribe un enunciado del problema."
            )
            return

        self.txt_salida.clear()
        self.btn_solucionar.setEnabled(False)
        self.btn_solucionar.setText("Procesando…")

        self.worker = GroqWorker(
            problem_text=self.txt_problema.toPlainText().strip()
        )
        self.worker.finished.connect(self.on_ok)
        self.worker.failed.connect(self.on_fail)
        self.worker.start()


    def on_ok(self, texto: str):
        self.txt_salida.setPlainText(texto)
        self.btn_solucionar.setEnabled(True)
        self.btn_solucionar.setText("Solucionar")
        self.worker = None

        if ("Función Objetivo" not in texto) or ("Restricciones" not in texto):
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.text(
                0.5, 0.5,
                "No se detectó un modelo válido para graficar.\n"
                "Asegúrate de que existan las secciones:\n"
                "‘Función Objetivo’ y ‘Restricciones’.",
                ha="center", va="center"
            )
            ax.set_axis_off()
            self.canvas.draw()
            return

        try:
            data = parse_salida_modelo(texto)

            self.figure.clear()
            ax = self.figure.add_subplot(111)
            res = graficar(
                ax,
                data["restr"],
                data["obj"],
                data["sentido"],
                titulo="Región factible y solución"
            )
            self.canvas.draw()

            if res:
                verts = res["vertices"]
                opt_pt = res["optimo"]["punto"]
                opt_val = res["optimo"]["valor"]
                px, py = data["obj"]

                verts_fmt = ", ".join([f"({x:.2f}, {y:.2f})" for x, y in verts])

                analisis = [
                    "\n📊 Análisis de la solución (calculado por la app):",
                    f"- Vértices factibles: {verts_fmt}",
                    f"- Solución óptima: x* = {opt_pt[0]:.2f}, y* = {opt_pt[1]:.2f}",
                    f"- Valor óptimo Z* = {opt_val:.2f}   (Z = {px}*x + {py}*y)"
                ]
                self.txt_salida.append("\n".join(analisis))
            else:
                self.txt_salida.append(
                    "\n📊 Análisis de la solución (calculado por la app):\n- Región factible vacía o no acotada."
                )

        except Exception as e:
            print("[DEBUG] Error en parseo/graficación:", e)
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, "Ocurrió un error al graficar.", ha="center", va="center")
            ax.set_axis_off()
            self.canvas.draw()
            self.txt_salida.append(f"\n[Error] No se pudo calcular el análisis:\n{e}")

    def on_fail(self, error: str):
        self.txt_salida.setPlainText(f"Error al llamar a Groq:\n{error}")
        self.btn_solucionar.setEnabled(True)
        self.btn_solucionar.setText("Solucionar")
        self.worker = None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = VentanaMetodoGrafico()
    w.show()
    sys.exit(app.exec())
