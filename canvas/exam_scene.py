from PyQt6.QtWidgets import QGraphicsScene
from PyQt6.QtGui import QColor, QPen, QBrush, QUndoStack
from PyQt6.QtCore import Qt, QRectF, pyqtSignal


class ExamScene(QGraphicsScene):
    """
    Escena que representa una o varias hojas A4 apiladas verticalmente.
    Dimensiones A4 a 96 dpi: 794 x 1123 px.
    """

    PAGE_W  = 794
    PAGE_H  = 1123
    PAGE_GAP = 40   # espacio entre páginas
    MARGIN  = 80    # espacio gris alrededor del conjunto

    item_moved = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._num_pages = 1
        self.show_grid  = False
        self.undo_stack = QUndoStack(self)

        self._update_scene_rect()
        self.setBackgroundBrush(QBrush(QColor("#D0D0D0")))

    # ------------------------------------------------------------------ #
    #  Páginas
    # ------------------------------------------------------------------ #

    @property
    def num_pages(self) -> int:
        return self._num_pages

    def add_page(self):
        self._num_pages += 1
        self._update_scene_rect()
        self.update()

    def page_top(self, page_index: int) -> float:
        """Coordenada Y superior de la página indicada (base 0)."""
        return page_index * (self.PAGE_H + self.PAGE_GAP)

    def page_rect(self, page_index: int) -> QRectF:
        return QRectF(0, self.page_top(page_index), self.PAGE_W, self.PAGE_H)

    def total_height(self) -> float:
        return self._num_pages * self.PAGE_H + (self._num_pages - 1) * self.PAGE_GAP

    def _update_scene_rect(self):
        self.setSceneRect(
            -self.MARGIN,
            -self.MARGIN,
            self.PAGE_W  + self.MARGIN * 2,
            self.total_height() + self.MARGIN * 2,
        )

    # ------------------------------------------------------------------ #
    #  Dibujo de fondo
    # ------------------------------------------------------------------ #

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)

        for i in range(self._num_pages):
            page = self.page_rect(i)

            # Sombra
            painter.fillRect(page.translated(6, 6), QColor(0, 0, 0, 50))

            # Hoja blanca
            painter.fillRect(page, Qt.GlobalColor.white)

            # Borde sutil
            painter.setPen(QPen(QColor("#BBBBBB"), 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(page)

            # Número de página (esquina inferior derecha, fuera de la hoja)
            if self._num_pages > 1:
                painter.setPen(QPen(QColor("#999999"), 1))
                label_rect = QRectF(page.right() - 60, page.bottom() + 6, 60, 20)
                painter.drawText(label_rect, Qt.AlignmentFlag.AlignRight, f"Pág. {i + 1}")

            # Cuadrícula opcional
            if self.show_grid:
                self._draw_grid(painter, page)

    def _draw_grid(self, painter, page: QRectF):
        GRID = 20
        pen = QPen(QColor(160, 190, 220, 140), 0.6, Qt.PenStyle.DotLine)
        painter.setPen(pen)

        x = page.left()
        while x <= page.right():
            painter.drawLine(int(x), int(page.top()), int(x), int(page.bottom()))
            x += GRID

        y = page.top()
        while y <= page.bottom():
            painter.drawLine(int(page.left()), int(y), int(page.right()), int(y))
            y += GRID