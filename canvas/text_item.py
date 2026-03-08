from PyQt6.QtWidgets import QGraphicsTextItem, QGraphicsItem, QStyleOptionGraphicsItem, QStyle
from PyQt6.QtGui import QFont, QColor, QPen, QFontMetrics
from PyQt6.QtCore import Qt, QPointF


class TextItem(QGraphicsTextItem):
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
        self._locked = False

    # ------------------------------------------------------------------ #
    #  Bloqueo
    # ------------------------------------------------------------------ #

    @property
    def locked(self) -> bool:
        return self._locked

    @locked.setter
    def locked(self, value: bool):
        self._locked = value
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, not value)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, not value)
        self.update()

    # ------------------------------------------------------------------ #
    #  Edición
    # ------------------------------------------------------------------ #

    def mouseDoubleClickEvent(self, event):
        if self._locked:
            return
        self._editing = True
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        self.setFocus(Qt.FocusReason.MouseFocusReason)
        self.update()
        super().mouseDoubleClickEvent(event)

    def focusOutEvent(self, event):
        self._editing = False
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        cursor = self.textCursor()
        cursor.clearSelection()
        self.setTextCursor(cursor)
        self.update()
        super().focusOutEvent(event)

    # ------------------------------------------------------------------ #
    #  Movimiento con Undo
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

        if self._locked:
            # Fondo rayado muy sutil para indicar que está bloqueado
            painter.fillRect(rect, QColor(255, 200, 100, 30))
            pen = QPen(QColor("#E0A000"), 1.0, Qt.PenStyle.DotLine)
        elif self._editing:
            painter.fillRect(rect, QColor(210, 230, 255, 180))
            pen = QPen(QColor("#4A90D9"), 1.5, Qt.PenStyle.SolidLine)
        elif self.isSelected():
            painter.fillRect(rect, QColor(0, 0, 0, 10))
            pen = QPen(QColor("#4A90D9"), 1.5, Qt.PenStyle.DashLine)
        else:
            pen = QPen(QColor(0, 0, 0, 0))

        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect.adjusted(0.5, 0.5, -0.5, -0.5))

        # Icono de candado si está bloqueado
        if self._locked:
            painter.setPen(QPen(QColor("#E0A000"), 1))
            painter.setFont(QFont("Arial", 8))
            painter.drawText(rect.adjusted(2, 2, -2, -2), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight, "🔒")

        super().paint(painter, clean_option, widget)