from PyQt6.QtWidgets import (
    QDockWidget, QListWidget, QListWidgetItem,
    QLabel, QVBoxLayout, QWidget, QMenu, QMessageBox
)
from PyQt6.QtGui import QPixmap, QPainter, QColor, QIcon
from PyQt6.QtCore import Qt, QTimer, QRectF, QSize


class ThumbnailPanel(QDockWidget):
    """
    Panel lateral con miniaturas de cada página.
    - Clic izquierdo: navegar a la página.
    - Clic derecho: menú contextual con opción de borrar página.
    """

    THUMB_W = 120
    THUMB_H = 170

    def __init__(self, canvas, parent=None):
        super().__init__("Páginas", parent)
        self._canvas = canvas
        self.setMinimumWidth(150)
        self.setMaximumWidth(180)
        self.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self._list = QListWidget()
        self._list.setIconSize(QSize(self.THUMB_W, self.THUMB_H))
        self._list.setSpacing(6)
        self._list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._list.customContextMenuRequested.connect(self._on_context_menu)
        self._list.setStyleSheet("""
            QListWidget {
                background: #3a3a3a;
                border: none;
            }
            QListWidget::item {
                color: #cccccc;
                padding: 4px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background: #1a5fa8;
                color: white;
            }
            QListWidget::item:hover {
                background: #505050;
            }
        """)
        self._list.itemClicked.connect(self._on_thumbnail_clicked)
        layout.addWidget(self._list)
        self.setWidget(container)

        # Timer para no redibujar en cada cambio mínimo
        self._refresh_timer = QTimer()
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.setInterval(400)
        self._refresh_timer.timeout.connect(self.refresh)

        canvas.scene().changed.connect(self._schedule_refresh)

    def _schedule_refresh(self, _=None):
        self._refresh_timer.start()

    def refresh(self):
        scene = self._canvas.scene()
        num_pages = scene.num_pages
        current_row = self._list.currentRow()

        selected = scene.selectedItems()
        for item in selected:
            item.setSelected(False)

        self._list.clear()

        for i in range(num_pages):
            pixmap = QPixmap(self.THUMB_W, self.THUMB_H)
            pixmap.fill(QColor("#ffffff"))

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            source = scene.page_rect(i)
            target = QRectF(0, 0, self.THUMB_W, self.THUMB_H)
            scene.render(painter, target, source)
            painter.end()

            item = QListWidgetItem(f"  Pág. {i + 1}")
            item.setIcon(QIcon(pixmap))
            item.setData(Qt.ItemDataRole.UserRole, i)
            self._list.addItem(item)

        for item in selected:
            item.setSelected(True)

        if 0 <= current_row < self._list.count():
            self._list.setCurrentRow(current_row)

    def _on_thumbnail_clicked(self, item: QListWidgetItem):
        page_index = item.data(Qt.ItemDataRole.UserRole)
        from canvas.exam_scene import ExamScene
        y = self._canvas.scene().page_top(page_index)
        self._canvas.ensureVisible(0, y, ExamScene.PAGE_W, ExamScene.PAGE_H, 40, 40)

    def _on_context_menu(self, pos):
        """Muestra menú contextual al hacer clic derecho sobre una miniatura."""
        item = self._list.itemAt(pos)
        if item is None:
            return

        page_index = item.data(Qt.ItemDataRole.UserRole)
        num_pages = self._canvas.scene().num_pages

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: #2b2b2b;
                color: #eeeeee;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px;
            }
            QMenu::item { padding: 6px 20px; border-radius: 3px; }
            QMenu::item:selected { background: #1a5fa8; }
            QMenu::item:disabled { color: #666666; }
        """)

        # Navegar a la página
        nav_action = menu.addAction(f"📄  Ir a página {page_index + 1}")
        nav_action.triggered.connect(lambda: self._on_thumbnail_clicked(item))

        menu.addSeparator()

        # Borrar página — desactivado si solo hay una
        delete_action = menu.addAction(f"🗑️  Borrar página {page_index + 1}")
        if num_pages <= 1:
            delete_action.setEnabled(False)
            delete_action.setToolTip("No se puede borrar la única página")
        else:
            delete_action.triggered.connect(lambda: self._confirm_delete_page(page_index))

        menu.exec(self._list.viewport().mapToGlobal(pos))

    def _confirm_delete_page(self, page_index: int):
        """Pide confirmación antes de borrar la página."""
        reply = QMessageBox.question(
            self,
            "Borrar página",
            f"¿Seguro que quieres borrar la página {page_index + 1}?\n"
            "Se eliminarán todos los elementos que contiene.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._canvas.delete_page(page_index)
            self.refresh()

    def highlight_page(self, page_index: int):
        if 0 <= page_index < self._list.count():
            self._list.setCurrentRow(page_index)