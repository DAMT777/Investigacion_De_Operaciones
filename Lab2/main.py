import sys
from PySide6.QtWidgets import QApplication
from interfaz import VentanaMetodoGrafico


def ejecutar_aplicacion() -> None:
    app = QApplication(sys.argv)
    ventana = VentanaMetodoGrafico()
    ventana.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    ejecutar_aplicacion()
