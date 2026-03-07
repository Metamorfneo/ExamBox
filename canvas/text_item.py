from PyQt6.QtWidgets import QGraphicsTextItem, QGraphicsItem, QStyleOptionGraphicsItem, QStyle
from PyQt6.QtGui import QFont, QColor, QPen
from PyQt6.QtCore import Qt, QPointF


class TextItem(QGraphicsTextItem):
    """
    Caja de texto movible y editable.

    - Clic simple: seleccionar / mover.
    - Doble clic: entrar en modo edición.
    - Clic fuera: salir del modo edición.
    """

    DEFAULT_WIDTH = 220.0

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

        self._drag_start: QPointF | None = None
        self._editing = False

    # ------------------------------------------------------------------ #
    #  Edición
    # ------------------------------------------------------------------ #

    def mouseDoubleClickEvent(self, event):
        self._editing = True
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        self.setFocus(Qt.FocusReason.MouseFocusReason)
        super().mouseDoubleClickEvent(event)

    def focusOutEvent(self, event):
        self._editing = False
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        cursor = self.textCursor()
        cursor.clearSelection()
        self.setTextCursor(cursor)
        super().focusOutEvent(event)

    # ------------------------------------------------------------------ #
    #  Movimiento con tracking para Undo
    # ------------------------------------------------------------------ #

    def mousePressEvent(self, event):
        if not self._editing:
            self._drag_start = self.pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if not self._editing and self._drag_start is not None:
            new_pos = self.pos()
            if new_pos != self._drag_start and self.scene():
                from canvas.commands import MoveItemCommand
                cmd = MoveItemCommand(self, self._drag_start, new_pos)
                self.scene().undo_stack.push(cmd)
                self.scene().item_moved.emit(self)
        self._drag_start = None

    # ------------------------------------------------------------------ #
    #  Apariencia
    # ------------------------------------------------------------------ #

    def paint(self, painter, option, widget):
        clean_option = QStyleOptionGraphicsItem(option)
        clean_option.state &= ~QStyle.StateFlag.State_Selected

        rect = self.boundingRect()

        # Fondo amarillo pálido
        painter.fillRect(rect, QColor(255, 253, 210, 200))

        # Borde: azul punteado si seleccionado, gris claro si no
        if self.isSelected():
            pen = QPen(QColor("#4A90D9"), 1.5, Qt.PenStyle.DashLine)
        else:
            pen = QPen(QColor("#CCCCCC"), 1.0, Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect.adjusted(0.5, 0.5, -0.5, -0.5))

        super().paint(painter, clean_option, widget)