import sys
from PySide6.QtWidgets import QApplication
from interfaz import VentanaMetodoGrafico

def main():
    app = QApplication(sys.argv)
    w = VentanaMetodoGrafico()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
