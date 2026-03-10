import os
import json
import base64

from PyQt6.QtWidgets import QGraphicsView, QFileDialog, QMessageBox, QApplication
from PyQt6.QtGui import QPainter, QPixmap, QPdfWriter, QPageSize, QFont
from PyQt6.QtCore import Qt, QRectF, QByteArray, QBuffer, QIODevice, QTimer

from canvas.exam_scene import ExamScene
from canvas.text_item import TextItem
from canvas.image_item import ImageItem
from canvas.commands import AddItemCommand, DeleteItemsCommand


class ExamCanvas(QGraphicsView):

    ZOOM_MIN = 0.2
    ZOOM_MAX = 4.0
    FILE_VERSION = 1
    OVERLAP_MARGIN = 10
    AUTOSAVE_INTERVAL_MS = 2 * 60 * 1000  # 2 minutos

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

        self._scene.item_moved.connect(self._on_item_moved)

        # Autosave
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setInterval(self.AUTOSAVE_INTERVAL_MS)
        self._autosave_timer.timeout.connect(self._autosave)
        self._autosave_timer.start()

    # ------------------------------------------------------------------ #
    #  Propiedades
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

    def scene(self):
        return self._scene

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

    def paste_from_clipboard(self):
        clipboard = QApplication.clipboard()
        pixmap = clipboard.pixmap()
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
        items = [i for i in self._scene.selectedItems() if not i.locked]
        if items:
            cmd = DeleteItemsCommand(self._scene, items)
            self._scene.undo_stack.push(cmd)

    # ------------------------------------------------------------------ #
    #  Bloquear / desbloquear
    # ------------------------------------------------------------------ #

    def toggle_lock_selected(self):
        """Bloquea los seleccionados si están desbloqueados, o desbloquea si están bloqueados."""
        items = self._scene.selectedItems()
        if not items:
            return
        # Si alguno está desbloqueado, bloquear todos; si todos bloqueados, desbloquear
        all_locked = all(getattr(i, "locked", False) for i in items)
        for item in items:
            if hasattr(item, "locked"):
                item.locked = not all_locked
        self._scene.update()

    # ------------------------------------------------------------------ #
    #  Fuente (solo para TextItem)
    # ------------------------------------------------------------------ #

    def set_font_family(self, family: str):
        for item in self._scene.selectedItems():
            if isinstance(item, TextItem):
                f = item.font()
                f.setFamily(family)
                item.setFont(f)

    def set_font_size(self, size: int):
        for item in self._scene.selectedItems():
            if isinstance(item, TextItem):
                f = item.font()
                f.setPointSize(max(6, size))
                item.setFont(f)

    def set_bold(self, bold: bool):
        for item in self._scene.selectedItems():
            if isinstance(item, TextItem):
                f = item.font()
                f.setBold(bold)
                item.setFont(f)

    def set_italic(self, italic: bool):
        for item in self._scene.selectedItems():
            if isinstance(item, TextItem):
                f = item.font()
                f.setItalic(italic)
                item.setFont(f)

    def selected_text_item(self) -> TextItem | None:
        """Devuelve el primer TextItem seleccionado, o None."""
        for item in self._scene.selectedItems():
            if isinstance(item, TextItem):
                return item
        return None

    # ------------------------------------------------------------------ #
    #  Páginas
    # ------------------------------------------------------------------ #

    def add_page(self):
        self._scene.add_page()
        new_page_top = self._scene.page_top(self._scene.num_pages - 1)
        self.ensureVisible(0, new_page_top, ExamScene.PAGE_W, ExamScene.PAGE_H, 40, 40)

    def delete_page(self, page_index: int):
        """Elimina la página indicada y sus elementos."""
        self._scene.delete_page(page_index)
        self.viewport().update()

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
    #  Guardar PDF
    # ------------------------------------------------------------------ #

    def save_pdf(self):
        self.save_pdf_as()

    def save_pdf_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar como PDF", "",
            "Archivo PDF (*.pdf);;Todos los archivos (*)",
        )
        if not path:
            return
        if not path.endswith(".pdf"):
            path += ".pdf"

        if self._render_pdf(path):
            exambox_path = path.replace(".pdf", ".exambox")
            self._write_exambox(exambox_path, silent=True)
            self._current_file = path
            self._update_window_title(path)
            # Registrar en recientes
            self.window()._recent_files.add(exambox_path)
            self.window()._rebuild_recent_menu()
            QMessageBox.information(
                self, "PDF guardado",
                f"PDF guardado en:\n{path}\n\nProyecto editable guardado en:\n{exambox_path}",
            )

    def _render_pdf(self, path: str) -> bool:
        writer = QPdfWriter(path)
        writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        writer.setResolution(150)

        painter = QPainter()
        if not painter.begin(writer):
            QMessageBox.critical(self, "Error al guardar", "No se pudo crear el archivo PDF.")
            return False

        selected = self._scene.selectedItems()
        for item in selected:
            item.setSelected(False)

        target = QRectF(0, 0, writer.width(), writer.height())
        for i in range(self._scene.num_pages):
            if i > 0:
                writer.newPage()
            self._scene.render(painter, target, self._scene.page_rect(i))

        painter.end()
        for item in selected:
            item.setSelected(True)
        return True

    # ------------------------------------------------------------------ #
    #  Imprimir
    # ------------------------------------------------------------------ #

    def print_exam(self):
        import tempfile
        import subprocess
        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", prefix="ExamBox_print_", delete=False)
        tmp_path = tmp.name
        tmp.close()
        if self._render_pdf(tmp_path):
            try:
                subprocess.Popen(["start", "", tmp_path], shell=True)
            except Exception as e:
                QMessageBox.critical(self, "Error al imprimir", f"No se pudo abrir el PDF:\n{e}")

    # ------------------------------------------------------------------ #
    #  Guardar / cargar proyecto (.exambox)
    # ------------------------------------------------------------------ #

    def save_project(self):
        if self._current_file and self._current_file.endswith(".exambox"):
            self._write_exambox(self._current_file)
        else:
            self.save_project_as()

    def save_project_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar proyecto editable", "",
            "Proyecto ExamBox (*.exambox);;Todos los archivos (*)",
        )
        if not path:
            return
        if not path.endswith(".exambox"):
            path += ".exambox"
        self._current_file = path
        self._write_exambox(path)

    def _write_exambox(self, path: str, silent: bool = False):
        data = {
            "version": self.FILE_VERSION,
            "num_pages": self._scene.num_pages,
            "items": [],
        }
        for item in self._scene.items():
            try:
                if isinstance(item, TextItem):
                    data["items"].append({
                        "type": "text",
                        "x": item.x(), "y": item.y(),
                        "width": item.textWidth(),
                        "text": item.toPlainText(),
                        "font_family": item.font().family(),
                        "font_size": item.font().pointSize(),
                        "bold": item.font().bold(),
                        "italic": item.font().italic(),
                        "locked": item.locked,
                    })
                elif isinstance(item, ImageItem):
                    data["items"].append({
                        "type": "image",
                        "x": item.x(), "y": item.y(),
                        "width": item.img_width,
                        "height": item.img_height,
                        "locked": item.locked,
                        "data": self._pixmap_to_base64(item.pixmap()),
                    })
            except Exception as e:
                QMessageBox.critical(self, "Error al serializar elemento", str(e))
                return

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            if not silent:
                self._update_window_title(path)
                # Registrar en recientes
                self.window()._recent_files.add(path)
                self.window()._rebuild_recent_menu()
                QMessageBox.information(self, "Proyecto guardado", f"Guardado correctamente en:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Error al guardar proyecto", str(e))

    def load_project(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir proyecto", "",
            "Proyecto ExamBox (*.exambox);;Todos los archivos (*)",
        )
        if not path:
            return
        self._load_from_path(path)

    def load_from_path(self, path: str):
        """Carga un proyecto desde una ruta directa (usado por archivos recientes)."""
        self._load_from_path(path)

    def _load_from_path(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error al abrir", str(e))
            return

        self._scene.clear()
        self._scene.undo_stack.clear()
        self._scene._num_pages = 1
        self._scene._update_scene_rect()

        num_pages = data.get("num_pages", 1)
        for _ in range(num_pages - 1):
            self._scene.add_page()

        for item_data in data.get("items", []):
            try:
                if item_data["type"] == "text":
                    item = TextItem()
                    item.setPlainText(item_data["text"])
                    item.setTextWidth(item_data["width"])
                    f = QFont(
                        item_data.get("font_family", "Arial"),
                        item_data.get("font_size", 12)
                    )
                    f.setBold(item_data.get("bold", False))
                    f.setItalic(item_data.get("italic", False))
                    item.setFont(f)
                    item.locked = item_data.get("locked", False)
                    item.setPos(item_data["x"], item_data["y"])
                    self._scene.addItem(item)
                elif item_data["type"] == "image":
                    pixmap = self._base64_to_pixmap(item_data["data"])
                    if not pixmap.isNull():
                        item = ImageItem(pixmap)
                        item.img_width = item_data["width"]
                        item.img_height = item_data["height"]
                        item.locked = item_data.get("locked", False)
                        item.setPos(item_data["x"], item_data["y"])
                        self._scene.addItem(item)
            except Exception as e:
                QMessageBox.warning(self, "Error al cargar elemento", str(e))

        self._current_file = path
        self._update_window_title(path)

        # Registrar en recientes
        self.window()._recent_files.add(path)
        self.window()._rebuild_recent_menu()

        self._scene.update()
        self.viewport().update()
        self.zoom_fit()

    # ------------------------------------------------------------------ #
    #  Autosave
    # ------------------------------------------------------------------ #

    def _autosave(self):
        """Guarda automáticamente en AppData cada 2 minutos."""
        import tempfile
        appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
        folder = os.path.join(appdata, "ExamBox")
        os.makedirs(folder, exist_ok=True)
        autosave_path = os.path.join(folder, "autosave.exambox")
        self._write_exambox(autosave_path, silent=True)
        # Mostrar brevemente en la barra de estado
        window = self.window()
        if hasattr(window, "statusBar"):
            window.statusBar().showMessage("✅ Autoguardado", 3000)

    # ------------------------------------------------------------------ #
    #  Sin superposición
    # ------------------------------------------------------------------ #

    def _on_item_moved(self, moved_item):
        self._resolve_overlaps(moved_item)

    def _resolve_overlaps(self, moved_item):
        if not self._no_overlap:
            return
        MAX_ITERATIONS = 40
        MARGIN = self.OVERLAP_MARGIN
        for _ in range(MAX_ITERATIONS):
            any_moved = False
            items = [i for i in self._scene.items() if isinstance(i, (TextItem, ImageItem))]
            items.sort(key=lambda i: i.sceneBoundingRect().top())
            for i, item_a in enumerate(items):
                rect_a = item_a.sceneBoundingRect()
                for item_b in items[i + 1:]:
                    # Nunca empujar un item bloqueado — en su lugar empujar item_b hacia abajo
                    rect_b = item_b.sceneBoundingRect()
                    h_overlap = rect_a.right() > rect_b.left() and rect_a.left() < rect_b.right()
                    v_overlap = rect_a.bottom() > rect_b.top()
                    if h_overlap and v_overlap:
                        push = rect_a.bottom() - rect_b.top() + MARGIN
                        if push > 0:
                            # Si item_a está bloqueado, empujar item_b hacia abajo
                            # Si item_b está bloqueado, empujar item_a hacia arriba
                            # Si ninguno está bloqueado, empujar el de abajo (item_b)
                            if getattr(item_b, "locked", False):
                                item_a.setPos(item_a.x(), item_a.y() - push)
                            else:
                                item_b.setPos(item_b.x(), item_b.y() + push)
                            any_moved = True
            if not any_moved:
                break

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
        # Encajar solo la hoja A4, no toda la escena con márgenes
        page = self._scene.page_rect(0)
        self.fitInView(page, Qt.AspectRatioMode.KeepAspectRatio)

    # ------------------------------------------------------------------ #
    #  Eventos
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
            elif event.key() == Qt.Key.Key_S:
                self.save_pdf()
        else:
            super().keyPressEvent(event)

    def wheelEvent(self, event):
        # Ctrl + rueda → zoom
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            factor = 1.15 if delta > 0 else 1 / 1.15
            self.zoom_by(factor)
        else:
            # Sin Ctrl → scroll normal
            super().wheelEvent(event)

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