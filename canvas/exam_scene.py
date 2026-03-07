from PyQt6.QtWidgets import QGraphicsScene
from PyQt6.QtGui import QColor, QPen, QBrush
from PyQt6.QtCore import Qt, QRectF


class ExamScene(QGraphicsScene):
    """
    Escena que representa una hoja A4 en blanco sobre un fondo gris.
    Dimensiones A4 a 96 dpi: 794 x 1123 px.
    """

    PAGE_W = 794
    PAGE_H = 1123
    MARGIN = 80  # espacio gris alrededor de la página

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(
            -self.MARGIN,
            -self.MARGIN,
            self.PAGE_W + self.MARGIN * 2,
            self.PAGE_H + self.MARGIN * 2,
        )
        self.setBackgroundBrush(QBrush(QColor("#D0D0D0")))

    def drawBackground(self, painter, rect):
        """Dibuja el fondo gris, la sombra y la hoja blanca."""
        super().drawBackground(painter, rect)

        page = QRectF(0, 0, self.PAGE_W, self.PAGE_H)

        # Sombra
        shadow = page.translated(6, 6)
        painter.fillRect(shadow, QColor(0, 0, 0, 50))

        # Hoja blanca
        painter.fillRect(page, Qt.GlobalColor.white)

        # Borde sutil de la hoja
        painter.setPen(QPen(QColor("#BBBBBB"), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(page)