
from PyQt6.QtWidgets import QMainWindow, QToolBar, QLabel
from PyQt6.QtGui import QAction , QFont , QKeySequence
from PyQt6.QtCore import Qt

from canvas.exam_canvas import ExamCanvas


class MainWindow(QMainWindow):
    """Ventana principal de la aplicación"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ExamBox")
        self.setMinimumSize(1100 , 780)

        self._build_canvas()
        self._build_toolbar()
        self._build_statusbar()



        # -- UI CONSTRUCTION --

        def _build_canvas(self):
            self.canvas = ExamCanvas(self)
            self.setCentralWidget(self.canvas)

        def _build_toolbar(self):
            tb = QToolBar("Herramientas")
            tb.setMovable(False)
            tb.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            tb.setStyleSheet("""

                QToolBar {
                    background: #2b2b2b;
                    border-bottom: 1px solid #1a1a1a;
                    padding: 4px 8px;
                    spacing: 6px;
                }
                             
                QToolButton {
                    color: #eeeeee;
                    background: transparent;
                    border: 1px solid transparent;
                    border-radius: 6px;
                    padding: 6px 10px;
                    font-size: 12px;
                }
                             
                QToolButton:hover {
                    background: #444444;
                    border-color: #666666;
                }
                QToolButton:pressed {
                    background: #555555;
                }
                             
                QtoolBar::separator {
                    background: #555555;
                    width: 1px;
                    margin: 4 6px;
                }
""")

self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tb)


# -- Añadir elementos --
add_text = QAction("Texto", self)
add_text.setStatusTip("Añadir un cuadro de texto")
add_text.triggered.connect(self.canvas.add_text_item)
tb.addAction(add_text)


add_img = QAction("Imagen", self)
add_img.setStatusTip("Añadir una imagen")
add_img.triggered.connect(self.canvas.add_image_item)
tb.addAction(add_img)

tb.addSeparator()


# -- Eliminar --
delete = QAction("Eliminar", self)
delete.setStatusTip("Eliminar el elemento seleccionado")
delete.triggered.connect(self.canvas.delete_selected)
tb.addAction(delete)

tb.addSeparator()


# -- Zoom --
zoom_in = QAction("Zoom +", self)
zoom_in.setStatusTip("Acercar")
zoom_in.triggered.connect(lambda: self.canvas.zoom_by(1.2))
tb.addAction(zoom_in)

zoom_out = QAction("Zoom -", self)
zoom_out.setStatusTip("Alejar")
zoom_out.triggered.connect(lambda: self.canvas.zoom_by(1 / 1.2))
tb.addAction(zoom_out)

zoom_reset = QAction("Reset Zoom", self)
zoom_reset.setStatusTip("Restablecer zoom")
zoom_reset.triggered.connect(self.canvas.zoom_fit)
tb.addAction(zoom_reset)


def _build_statusbar(self):
    bar = self.statusBar()
    bar.setStyleSheet("background: #2b2b2b; color: #aaaaaa; font-size: 12px;")
    bar.showMessagge(
        "Listo  * Doble clic en texto para editar    "
        "*  arrastrar para mover    "
        "*  esquina azul para redimensionar     "
        "*  Supr para eliminar"
    )