import sys
import os

# Asegura que Python busca módulos desde la carpeta del proyecto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from UI.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ExamBox")
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()