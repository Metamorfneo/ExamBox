from PyQt6.QtWidgets import QGraphicsItem
from PyQt6.QtGui import QPen, QBrush, QColor, QPixmap, QPainterPath
from PyQt6.QtCore import Qt, QRectF, QPointF

HANDLE_SIZE = 14
MIN_SIZE = 40.0


class ImageItem(QGraphicsItem):
    """
    Caja de imagen movible y redimensionable.

    - Clic y arrastra: mover.
    - Seleccionar → arrastra el triángulo azul (esquina inf-der): redimensionar.
    """

    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)

        self._pixmap = pixmap
        self.img_width = float(pixmap.width())
        self.img_height = float(pixmap.height())
        self._aspect = self.img_width / self.img_height

        self._resizing = False
        self._resize_start: QPointF | None = None
        self._orig_w = self.img_width
        self._orig_h = self.img_height

        self._drag_start: QPointF | None = None

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)

    # ------------------------------------------------------------------ #
    #  Acceso al pixmap (necesario para guardar en JSON)
    # ------------------------------------------------------------------ #

    def pixmap(self) -> QPixmap:
        return self._pixmap

    # ------------------------------------------------------------------ #
    #  Geometría
    # ------------------------------------------------------------------ #

    def boundingRect(self) -> QRectF:
        return QRectF(-1, -1, self.img_width + HANDLE_SIZE + 1, self.img_height + HANDLE_SIZE + 1)

    def _image_rect(self) -> QRectF:
        return QRectF(0, 0, self.img_width, self.img_height)

    def _handle_path(self) -> QPainterPath:
        x = self.img_width
        y = self.img_height
        path = QPainterPath()
        path.moveTo(x, y + HANDLE_SIZE)
        path.lineTo(x + HANDLE_SIZE, y)
        path.lineTo(x + HANDLE_SIZE, y + HANDLE_SIZE)
        path.closeSubpath()
        return path

    def _on_handle(self, pos: QPointF) -> bool:
        return self._handle_path().contains(pos)

    # ------------------------------------------------------------------ #
    #  Pintura
    # ------------------------------------------------------------------ #

    def paint(self, painter, option, widget):
        img_rect = self._image_rect()
        painter.drawPixmap(img_rect.toRect(), self._pixmap)

        if self.isSelected():
            pen = QPen(QColor("#4A90D9"), 1.5, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(img_rect)
            painter.setPen(QPen(QColor("#2070C0"), 1))
            painter.setBrush(QBrush(QColor("#4A90D9")))
            painter.drawPath(self._handle_path())
        else:
            painter.setPen(QPen(QColor("#AAAAAA"), 0.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(img_rect)

    # ------------------------------------------------------------------ #
    #  Cursor
    # ------------------------------------------------------------------ #

    def hoverMoveEvent(self, event):
        if self.isSelected() and self._on_handle(event.pos()):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        else:
            self.setCursor(Qt.CursorShape.SizeAllCursor)
        super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event):
        self.unsetCursor()
        super().hoverLeaveEvent(event)

    # ------------------------------------------------------------------ #
    #  Ratón — mover y redimensionar con Undo
    # ------------------------------------------------------------------ #

    def mousePressEvent(self, event):
        if self.isSelected() and self._on_handle(event.pos()):
            # Iniciar redimensión
            self._resizing = True
            self._resize_start = event.pos()
            self._orig_w = self.img_width
            self._orig_h = self.img_height
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            event.accept()
        else:
            # Iniciar movimiento
            self._resizing = False
            self._drag_start = self.pos()
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._resizing and self._resize_start is not None:
            delta = event.pos() - self._resize_start
            new_w = max(MIN_SIZE, self._orig_w + delta.x())
            new_h = new_w / self._aspect
            self.prepareGeometryChange()
            self.img_width = new_w
            self.img_height = new_h
            self.update()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._resizing:
            # Guardar el resize en el undo stack si cambió el tamaño
            if self.scene() and (self.img_width != self._orig_w or self.img_height != self._orig_h):
                from canvas.commands import ResizeImageCommand
                cmd = ResizeImageCommand(
                    self, self._orig_w, self._orig_h,
                    self.img_width, self.img_height
                )
                self.scene().undo_stack.push(cmd)
                self.scene().item_moved.emit(self)
            self._resizing = False
            self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
            event.accept()
        else:
            super().mouseReleaseEvent(event)
            # Guardar el movimiento en el undo stack si cambió la posición
            if self._drag_start is not None and self.scene():
                new_pos = self.pos()
                if new_pos != self._drag_start:
                    from canvas.commands import MoveItemCommand
                    cmd = MoveItemCommand(self, self._drag_start, new_pos)
                    self.scene().undo_stack.push(cmd)
                    self.scene().item_moved.emit(self)
            self._drag_start = None