from PyQt6.QtWidgets import QGraphicsTextItem, QGraphicsItem, QStyleOptionGraphicsItem, QStyle
from PyQt6.QtGui import QFont, QColor, QPen
from PyQt6.QtCore import Qt


class TextItem(QGraphicsTextItem):
    """
    Caja de texto movible y editable.

    - Clic simple: seleccionar / mover.
    - Doble clic: entrar en modo edición.
    - Clic fuera: salir del modo edición.
    """

    DEFAULT_WIDTH = 220.0
    PADDING = 6  # px de padding visual alrededor del texto

    def __init__(self, parent=None):
        super().__init__("Doble clic para editar", parent)

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemIsFocusable
        )
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.setTextWidth(self.DEFAULT_WIDTH)
        self.setFont(QFont("Arial", 12))
        self.setDefaultTextColor(QColor("#111111"))

    # ------------------------------------------------------------------ #
    #  Edición
    # ------------------------------------------------------------------ #

    def mouseDoubleClickEvent(self, event):
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        self.setFocus(Qt.FocusReason.MouseFocusReason)
        super().mouseDoubleClickEvent(event)

    def focusOutEvent(self, event):
        # Salir del modo edición al perder el foco
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        cursor = self.textCursor()
        cursor.clearSelection()
        self.setTextCursor(cursor)
        super().focusOutEvent(event)

    # ------------------------------------------------------------------ #
    #  Apariencia
    # ------------------------------------------------------------------ #

    def paint(self, painter, option, widget):
        # Suprimir el recuadro de selección nativo de Qt (lo dibujamos nosotros)
        clean_option = QStyleOptionGraphicsItem(option)
        clean_option.state &= ~QStyle.StateFlag.State_Selected

        rect = self.boundingRect()

        # Fondo amarillo pálido (aspecto de post-it / caja)
        painter.fillRect(rect, QColor(255, 253, 210, 200))

        # Borde: azul punteado si seleccionado, gris claro si no
        if self.isSelected():
            pen = QPen(QColor("#4A90D9"), 1.5, Qt.PenStyle.DashLine)
        else:
            pen = QPen(QColor("#CCCCCC"), 1.0, Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect.adjusted(0.5, 0.5, -0.5, -0.5))

        # Dibujar el texto por encima
        super().paint(painter, clean_option, widget)