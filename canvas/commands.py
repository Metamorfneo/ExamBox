from PyQt6.QtGui import QUndoCommand
from PyQt6.QtCore import QPointF


class MoveItemCommand(QUndoCommand):
    """Registra el movimiento de un elemento para poder deshacerlo."""

    def __init__(self, item, old_pos: QPointF, new_pos: QPointF):
        super().__init__("Mover elemento")
        self._item = item
        self._old_pos = QPointF(old_pos)
        self._new_pos = QPointF(new_pos)

    def undo(self):
        self._item.setPos(self._old_pos)

    def redo(self):
        self._item.setPos(self._new_pos)


class AddItemCommand(QUndoCommand):
    """Registra la adición de un elemento al canvas."""

    def __init__(self, scene, item):
        super().__init__("Añadir elemento")
        self._scene = scene
        self._item = item

    def undo(self):
        self._scene.removeItem(self._item)

    def redo(self):
        if self._item.scene() is None:
            self._scene.addItem(self._item)


class DeleteItemsCommand(QUndoCommand):
    """Registra el borrado de uno o varios elementos."""

    def __init__(self, scene, items):
        super().__init__("Eliminar elemento(s)")
        self._scene = scene
        self._items = list(items)

    def undo(self):
        for item in self._items:
            if item.scene() is None:
                self._scene.addItem(item)

    def redo(self):
        for item in self._items:
            if item.scene() is not None:
                self._scene.removeItem(item)


class ResizeImageCommand(QUndoCommand):
    """Registra el redimensionado de una imagen."""

    def __init__(self, item, old_w: float, old_h: float, new_w: float, new_h: float):
        super().__init__("Redimensionar imagen")
        self._item = item
        self._old_w = old_w
        self._old_h = old_h
        self._new_w = new_w
        self._new_h = new_h

    def undo(self):
        self._item.prepareGeometryChange()
        self._item.img_width = self._old_w
        self._item.img_height = self._old_h
        self._item.update()

    def redo(self):
        self._item.prepareGeometryChange()
        self._item.img_width = self._new_w
        self._item.img_height = self._new_h
        self._item.update()