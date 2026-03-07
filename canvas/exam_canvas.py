import os
import json
import base64

from PyQt6.QtWidgets import QGraphicsView, QFileDialog, QMessageBox, QApplication
from PyQt6.QtGui import QPainter, QPixmap
from PyQt6.QtCore import Qt, QRectF, QByteArray, QBuffer, QIODevice
from PyQt6.QtPrintSupport import QPrinter

from canvas.exam_scene import ExamScene
from canvas.text_item import TextItem
from canvas.image_item import ImageItem
from canvas.commands import AddItemCommand, DeleteItemsCommand


class ExamCanvas(QGraphicsView):
    """
    Vista principal del examen.
    Gestiona zoom, adición, eliminación, guardado, carga, undo/redo
    y el modo sin superposición.
    """

    ZOOM_MIN = 0.2
    ZOOM_MAX = 4.0
    FILE_VERSION = 1
    OVERLAP_MARGIN = 10  # px de espacio mínimo entre elementos en modo sin superposición

    def __init__(self, parent=None):
        super().__init__(parent)

        self._scene = ExamScene(self)
        self.setScene(self._scene)

        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setStyleSheet("background: #D0D0D0; border: none;")

        self._zoom_level = 1.0
        self._current_file: str | None = None
        self._no_overlap = False

        # Escuchar cuando un item se mueve para resolver superposiciones
        self._scene.item_moved.connect(self._on_item_moved)

    # ------------------------------------------------------------------ #
    #  Propiedades de modo
    # ------------------------------------------------------------------ #

    @property
    def no_overlap(self) -> bool:
        return self._no_overlap

    @no_overlap.setter
    def no_overlap(self, value: bool):
        self._no_overlap = value

    @property
    def show_grid(self) -> bool:
        return self._scene.show_grid

    @show_grid.setter
    def show_grid(self, value: bool):
        self._scene.show_grid = value
        self._scene.update()

    # ------------------------------------------------------------------ #
    #  Undo / Redo
    # ------------------------------------------------------------------ #

    def undo(self):
        self._scene.undo_stack.undo()

    def redo(self):
        self._scene.undo_stack.redo()

    # ------------------------------------------------------------------ #
    #  Añadir elementos
    # ------------------------------------------------------------------ #

    def add_text_item(self):
        item = TextItem()
        pos = self._center_in_scene()
        item.setPos(pos.x() - item.textWidth() / 2, pos.y() - 20)
        cmd = AddItemCommand(self._scene, item)
        self._scene.undo_stack.push(cmd)
        self._scene.clearSelection()
        item.setSelected(True)
        self._resolve_overlaps(item)

    def add_image_item(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar imagen", "",
            "Imágenes (*.png *.jpg *.jpeg *.bmp *.gif *.webp)",
        )
        if not path:
            return
        pixmap = QPixmap(path)
        if pixmap.isNull():
            return

        max_w = ExamScene.PAGE_W * 0.6
        if pixmap.width() > max_w:
            pixmap = pixmap.scaledToWidth(int(max_w), Qt.TransformationMode.SmoothTransformation)

        item = ImageItem(pixmap)
        pos = self._center_in_scene()
        item.setPos(pos.x() - item.img_width / 2, pos.y() - item.img_height / 2)
        cmd = AddItemCommand(self._scene, item)
        self._scene.undo_stack.push(cmd)
        self._scene.clearSelection()
        item.setSelected(True)
        self._resolve_overlaps(item)

    # ------------------------------------------------------------------ #
    #  Eliminar
    # ------------------------------------------------------------------ #

    def delete_selected(self):
        items = self._scene.selectedItems()
        if items:
            cmd = DeleteItemsCommand(self._scene, items)
            self._scene.undo_stack.push(cmd)

    # ------------------------------------------------------------------ #
    #  Páginas
    # ------------------------------------------------------------------ #

    def add_page(self):
        """Añade una nueva hoja en blanco debajo de las existentes."""
        self._scene.add_page()
        new_page_top = self._scene.page_top(self._scene.num_pages - 1)
        self.ensureVisible(0, new_page_top, ExamScene.PAGE_W, ExamScene.PAGE_H, 40, 40)

    # ------------------------------------------------------------------ #
    #  Guardar
    # ------------------------------------------------------------------ #

    def save(self):
        if self._current_file:
            self._write_file(self._current_file)
        else:
            self.save_as()

    def save_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar examen", "",
            "Examen ExamBox (*.exambox);;Todos los archivos (*)",
        )
        if not path:
            return
        if not path.endswith(".exambox"):
            path += ".exambox"
        self._current_file = path
        self._write_file(path)

    def _write_file(self, path: str):
        data = {
            "version": self.FILE_VERSION,
            "num_pages": self._scene.num_pages,
            "items": [],
        }

        for item in self._scene.items():
            if isinstance(item, TextItem):
                data["items"].append({
                    "type": "text",
                    "x": item.x(), "y": item.y(),
                    "width": item.textWidth(),
                    "text": item.toPlainText(),
                    "font_size": item.font().pointSize(),
                })
            elif isinstance(item, ImageItem):
                data["items"].append({
                    "type": "image",
                    "x": item.x(), "y": item.y(),
                    "width": item.img_width,
                    "height": item.img_height,
                    "data": self._pixmap_to_base64(item.pixmap()),
                })

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._update_window_title(path)
        except Exception as e:
            QMessageBox.critical(self, "Error al guardar", str(e))

    # ------------------------------------------------------------------ #
    #  Cargar
    # ------------------------------------------------------------------ #

    def load(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir examen", "",
            "Examen ExamBox (*.exambox);;Todos los archivos (*)",
        )
        if not path:
            return
        self._read_file(path)

    def _read_file(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error al abrir", str(e))
            return

        self._scene.clear()
        self._scene.undo_stack.clear()

        # Restaurar número de páginas
        num_pages = data.get("num_pages", 1)
        for _ in range(num_pages - 1):
            self._scene.add_page()

        for item_data in data.get("items", []):
            if item_data["type"] == "text":
                item = TextItem()
                item.setPlainText(item_data["text"])
                item.setTextWidth(item_data["width"])
                font = item.font()
                font.setPointSize(item_data.get("font_size", 12))
                item.setFont(font)
                item.setPos(item_data["x"], item_data["y"])
                self._scene.addItem(item)
            elif item_data["type"] == "image":
                pixmap = self._base64_to_pixmap(item_data["data"])
                if not pixmap.isNull():
                    item = ImageItem(pixmap)
                    item.img_width = item_data["width"]
                    item.img_height = item_data["height"]
                    item.setPos(item_data["x"], item_data["y"])
                    self._scene.addItem(item)

        self._current_file = path
        self._update_window_title(path)

    # ------------------------------------------------------------------ #
    #  Nuevo examen
    # ------------------------------------------------------------------ #

    def new_exam(self):
        reply = QMessageBox.question(
            self, "Nuevo examen",
            "¿Seguro que quieres empezar un examen nuevo?\nSe perderán los cambios no guardados.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._scene.clear()
            self._scene.undo_stack.clear()
            self._scene._num_pages = 1
            self._scene._update_scene_rect()
            self._scene.update()
            self._current_file = None
            self._update_window_title(None)

    # ------------------------------------------------------------------ #
    #  Exportar PDF
    # ------------------------------------------------------------------ #

    def export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar como PDF", "",
            "Archivo PDF (*.pdf);;Todos los archivos (*)",
        )
        if not path:
            return
        if not path.endswith(".pdf"):
            path += ".pdf"

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(path)
        printer.setPageSize(QPrinter.PageSize.A4)
        printer.setFullPage(True)

        painter = QPainter()
        if not painter.begin(printer):
            QMessageBox.critical(self, "Error al exportar", "No se pudo crear el archivo PDF.")
            return

        # Ocultar selección para que no aparezca en el PDF
        selected = self._scene.selectedItems()
        for item in selected:
            item.setSelected(False)

        target = QRectF(printer.pageRect(QPrinter.Unit.DevicePixel))

        for i in range(self._scene.num_pages):
            if i > 0:
                printer.newPage()
            source = self._scene.page_rect(i)
            self._scene.render(painter, target, source)

        painter.end()

        for item in selected:
            item.setSelected(True)

        QMessageBox.information(
            self, "PDF exportado",
            f"El examen se ha guardado correctamente en:\n{path}",
        )

    # ------------------------------------------------------------------ #
    #  Sin superposición
    # ------------------------------------------------------------------ #

    def _on_item_moved(self, moved_item):
        """Llamado automáticamente cuando un item termina de moverse."""
        self._resolve_overlaps(moved_item)

    def _resolve_overlaps(self, moved_item):
        """
        Si el modo sin superposición está activo, empuja los elementos
        hacia abajo para que no se superpongan con moved_item ni entre sí.
        """
        if not self._no_overlap:
            return

        MAX_ITERATIONS = 40
        MARGIN = self.OVERLAP_MARGIN

        for _ in range(MAX_ITERATIONS):
            any_moved = False

            # Ordenar todos los items de arriba a abajo
            items = [
                i for i in self._scene.items()
                if isinstance(i, (TextItem, ImageItem))
            ]
            items.sort(key=lambda i: i.sceneBoundingRect().top())

            for i, item_a in enumerate(items):
                rect_a = item_a.sceneBoundingRect()

                for item_b in items[i + 1:]:
                    rect_b = item_b.sceneBoundingRect()

                    # Solo empujar si hay solapamiento horizontal también
                    h_overlap = rect_a.right() > rect_b.left() and rect_a.left() < rect_b.right()
                    v_overlap = rect_a.bottom() > rect_b.top()

                    if h_overlap and v_overlap:
                        push = rect_a.bottom() - rect_b.top() + MARGIN
                        if push > 0:
                            item_b.setPos(item_b.x(), item_b.y() + push)
                            any_moved = True

            if not any_moved:
                break

    def paste_from_clipboard(self):
        """Pega una imagen del portapapeles como ImageItem."""
        clipboard = QApplication.clipboard()
        pixmap = clipboard.pixmap()

        if pixmap.isNull():
            return

        # Reducir si es demasiado grande para la hoja
        max_w = ExamScene.PAGE_W * 0.6
        if pixmap.width() > max_w:
            pixmap = pixmap.scaledToWidth(int(max_w), Qt.TransformationMode.SmoothTransformation)

        item = ImageItem(pixmap)
        pos = self._center_in_scene()
        item.setPos(pos.x() - item.img_width / 2, pos.y() - item.img_height / 2)
        cmd = AddItemCommand(self._scene, item)
        self._scene.undo_stack.push(cmd)
        self._scene.clearSelection()
        item.setSelected(True)
        self._resolve_overlaps(item)

    # ------------------------------------------------------------------ #
    #  Zoom
    # ------------------------------------------------------------------ #

    def zoom_by(self, factor: float):
        new_zoom = self._zoom_level * factor
        if not (self.ZOOM_MIN <= new_zoom <= self.ZOOM_MAX):
            return
        self._zoom_level = new_zoom
        self.scale(factor, factor)

    def zoom_fit(self):
        self.resetTransform()
        self._zoom_level = 1.0
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    # ------------------------------------------------------------------ #
    #  Eventos de teclado
    # ------------------------------------------------------------------ #

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            self.delete_selected()
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_Z:
                self.undo()
            elif event.key() == Qt.Key.Key_Y:
                self.redo()
            elif event.key() == Qt.Key.Key_V:
                self.paste_from_clipboard()
        else:
            super().keyPressEvent(event)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        factor = 1.15 if delta > 0 else 1 / 1.15
        self.zoom_by(factor)

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #

    def _center_in_scene(self):
        return self.mapToScene(self.viewport().rect().center())

    def _update_window_title(self, path: str | None):
        window = self.window()
        if path:
            window.setWindowTitle(f"ExamBox — {os.path.basename(path)}")
        else:
            window.setWindowTitle("ExamBox — Nuevo examen")

    @staticmethod
    def _pixmap_to_base64(pixmap: QPixmap) -> str:
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        pixmap.save(buffer, "PNG")
        return base64.b64encode(bytes(byte_array)).decode("utf-8")

    @staticmethod
    def _base64_to_pixmap(data: str) -> QPixmap:
        pixmap = QPixmap()
        pixmap.loadFromData(base64.b64decode(data))
        return pixmap