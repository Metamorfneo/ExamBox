from PyQt6.QtWidgets import (
    QMainWindow, QToolBar, QFontComboBox, QSpinBox,
    QWidgetAction, QLabel, QMenu, QToolButton
)
from PyQt6.QtGui import QAction, QKeySequence, QFont
from PyQt6.QtCore import Qt

from canvas.exam_canvas import ExamCanvas
from canvas.text_item import TextItem
from UI.thumbnail_panel import ThumbnailPanel
from UI.recent_files import RecentFiles

TOOLBAR_STYLE = """
    QToolBar {
        background: #2b2b2b;
        border-bottom: 1px solid #1a1a1a;
        padding: 4px 8px;
        spacing: 4px;
    }
    QToolButton {
        color: #eeeeee;
        background: transparent;
        border: 1px solid transparent;
        border-radius: 6px;
        padding: 5px 8px;
        font-size: 12px;
    }
    QToolButton:hover { background: #444444; border-color: #666666; }
    QToolButton:pressed { background: #555555; }
    QToolButton:checked { background: #1a5fa8; border-color: #4A90D9; color: #ffffff; }
    QToolBar::separator { background: #555555; width: 1px; margin: 4px 6px; }
    QFontComboBox, QSpinBox {
        background: #3a3a3a; color: #eeeeee;
        border: 1px solid #555555; border-radius: 4px;
        padding: 2px 4px; font-size: 12px;
    }
    QLabel { color: #aaaaaa; font-size: 11px; padding: 0 4px; }
"""


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ExamBox — Nuevo examen")
        self.setMinimumSize(1200, 780)

        self._recent_files = RecentFiles()

        self._build_canvas()
        self._build_main_toolbar()
        self._build_font_toolbar()
        self._build_thumbnail_panel()
        self._build_statusbar()

        # Actualizar controles de fuente cuando cambia la selección
        self.canvas.scene().selectionChanged.connect(self._on_selection_changed)

    # ------------------------------------------------------------------ #
    #  UI Construction
    # ------------------------------------------------------------------ #

    def _build_canvas(self):
        self.canvas = ExamCanvas(self)
        self.setCentralWidget(self.canvas)

    def _build_main_toolbar(self):
        tb = QToolBar("Herramientas")
        tb.setMovable(False)
        tb.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        tb.setStyleSheet(TOOLBAR_STYLE)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tb)
        self._main_toolbar = tb  # guardar referencia para la barra de fuente

        # -- Archivo --
        new_exam = QAction("🆕  Nuevo", self)
        new_exam.setShortcut(QKeySequence("Ctrl+N"))
        new_exam.setStatusTip("Nuevo examen (Ctrl+N)")
        new_exam.triggered.connect(self.canvas.new_exam)
        tb.addAction(new_exam)

        # Botón Abrir con menú desplegable de recientes
        open_btn = QAction("📂  Abrir", self)
        open_btn.setShortcut(QKeySequence("Ctrl+O"))
        open_btn.setStatusTip("Abrir proyecto (Ctrl+O) — mantén pulsado para ver recientes")
        open_btn.triggered.connect(self.canvas.load_project)
        tb.addAction(open_btn)

        self._recent_menu_action = QAction("🕐  Recientes", self)
        self._recent_menu = QMenu(self)
        self._recent_menu_action.setMenu(self._recent_menu)
        tb.addAction(self._recent_menu_action)
        self._rebuild_recent_menu()

        save_project = QAction("🗂️  Guardar proyecto", self)
        save_project.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_project.setStatusTip("Guardar proyecto editable .exambox (Ctrl+Shift+S)")
        save_project.triggered.connect(self.canvas.save_project)
        tb.addAction(save_project)

        save_pdf = QAction("📄  Guardar PDF", self)
        save_pdf.setShortcut(QKeySequence("Ctrl+S"))
        save_pdf.setStatusTip("Guardar el examen como PDF (Ctrl+S)")
        save_pdf.triggered.connect(self.canvas.save_pdf)
        tb.addAction(save_pdf)

        print_exam = QAction("🖨️  Imprimir", self)
        print_exam.setShortcut(QKeySequence("Ctrl+P"))
        print_exam.setStatusTip("Imprimir el examen (Ctrl+P)")
        print_exam.triggered.connect(self.canvas.print_exam)
        tb.addAction(print_exam)

        tb.addSeparator()

        # -- Deshacer / Rehacer --
        undo_action = QAction("↩  Deshacer", self)
        undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        undo_action.triggered.connect(self.canvas.undo)
        tb.addAction(undo_action)

        redo_action = QAction("↪  Rehacer", self)
        redo_action.setShortcut(QKeySequence("Ctrl+Y"))
        redo_action.triggered.connect(self.canvas.redo)
        tb.addAction(redo_action)

        tb.addSeparator()

        # -- Añadir elementos --
        add_text = QAction("📝  Texto", self)
        add_text.triggered.connect(self.canvas.add_text_item)
        tb.addAction(add_text)

        add_img = QAction("🖼️  Imagen", self)
        add_img.triggered.connect(self.canvas.add_image_item)
        tb.addAction(add_img)

        tb.addSeparator()

        # -- Acciones sobre selección --
        delete = QAction("🗑️  Eliminar", self)
        delete.setStatusTip("Eliminar seleccionado (Supr)")
        delete.triggered.connect(self.canvas.delete_selected)
        tb.addAction(delete)

        lock_action = QAction("🔒  Bloquear", self)
        lock_action.setCheckable(False)
        lock_action.setStatusTip("Bloquear/desbloquear el elemento seleccionado")
        lock_action.triggered.connect(self.canvas.toggle_lock_selected)
        tb.addAction(lock_action)

        tb.addSeparator()

        # -- Opciones de vista --
        grid_action = QAction("⊞  Cuadrícula", self)
        grid_action.setCheckable(True)
        grid_action.toggled.connect(lambda v: setattr(self.canvas, "show_grid", v))
        tb.addAction(grid_action)

        overlap_action = QAction("⬜  Sin superposición", self)
        overlap_action.setCheckable(True)
        overlap_action.toggled.connect(lambda v: setattr(self.canvas, "no_overlap", v))
        tb.addAction(overlap_action)

        tb.addSeparator()

        # -- Páginas --
        add_page = QAction("📄+  Nueva hoja", self)
        add_page.setShortcut(QKeySequence("Ctrl+M"))
        add_page.triggered.connect(self.canvas.add_page)
        tb.addAction(add_page)

        tb.addSeparator()

        # -- Zoom --
        zoom_in = QAction("🔍+", self)
        zoom_in.triggered.connect(lambda: self.canvas.zoom_by(1.2))
        tb.addAction(zoom_in)

        zoom_out = QAction("🔍−", self)
        zoom_out.triggered.connect(lambda: self.canvas.zoom_by(1 / 1.2))
        tb.addAction(zoom_out)

    def _build_font_toolbar(self):
        """
        Barra de fuente colapsable: un botón 'Aa ▾' en la toolbar principal
        que despliega un menú flotante con los controles de fuente.
        """
        # Añadimos el botón al final de la toolbar principal
        main_tb = self._main_toolbar

        # Separador antes del botón de fuente
        main_tb.addSeparator()

        # Botón desplegable estilo QToolButton con menú
        self._font_btn = QToolButton(self)
        self._font_btn.setText("  Aa  ▾")
        self._font_btn.setToolTip("Opciones de fuente para el texto seleccionado")
        self._font_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._font_btn.setStyleSheet("""
            QToolButton {
                color: #eeeeee;
                background: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 6px;
                padding: 5px 10px;
                font-size: 13px;
                font-weight: bold;
            }
            QToolButton:hover { background: #4a4a4a; border-color: #4A90D9; }
            QToolButton:disabled { color: #666666; background: #2b2b2b; border-color: #444; }
            QToolButton::menu-indicator { image: none; }
        """)

        # Menú del botón
        font_menu = QMenu(self)
        font_menu.setStyleSheet("""
            QMenu {
                background: #2b2b2b;
                border: 1px solid #555555;
                border-radius: 6px;
                padding: 8px;
            }
            QLabel { color: #aaaaaa; font-size: 11px; padding: 2px 4px; }
            QFontComboBox, QSpinBox {
                background: #3a3a3a; color: #eeeeee;
                border: 1px solid #555555; border-radius: 4px;
                padding: 3px 6px; font-size: 12px; min-width: 160px;
            }
            QToolButton {
                color: #eeeeee; background: #3a3a3a;
                border: 1px solid #555555; border-radius: 4px;
                padding: 4px 14px; font-size: 12px;
            }
            QToolButton:hover { background: #4a90d9; }
            QToolButton:checked { background: #1a5fa8; border-color: #4A90D9; }
        """)

        # -- Familia --
        lbl_family = QLabel("  Fuente")
        lbl_family_action = QWidgetAction(self)
        lbl_family_action.setDefaultWidget(lbl_family)
        font_menu.addAction(lbl_family_action)

        self._font_combo = QFontComboBox()
        self._font_combo.setCurrentFont(QFont("Arial"))
        self._font_combo.setFixedWidth(200)
        self._font_combo.currentFontChanged.connect(
            lambda f: self.canvas.set_font_family(f.family())
        )
        combo_action = QWidgetAction(self)
        combo_action.setDefaultWidget(self._font_combo)
        font_menu.addAction(combo_action)

        font_menu.addSeparator()

        # -- Tamaño --
        lbl_size = QLabel("  Tamaño")
        lbl_size_action = QWidgetAction(self)
        lbl_size_action.setDefaultWidget(lbl_size)
        font_menu.addAction(lbl_size_action)

        self._font_size = QSpinBox()
        self._font_size.setRange(6, 96)
        self._font_size.setValue(12)
        self._font_size.setFixedWidth(80)
        self._font_size.valueChanged.connect(self.canvas.set_font_size)
        size_action = QWidgetAction(self)
        size_action.setDefaultWidget(self._font_size)
        font_menu.addAction(size_action)

        font_menu.addSeparator()

        # -- Negrita e Italica en una fila --
        self._bold_action = QAction("  N  Negrita", self)
        self._bold_action.setCheckable(True)
        self._bold_action.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self._bold_action.toggled.connect(self.canvas.set_bold)
        font_menu.addAction(self._bold_action)

        self._italic_action = QAction("  K  Cursiva", self)
        self._italic_action.setCheckable(True)
        f_italic = QFont("Arial", 11)
        f_italic.setItalic(True)
        self._italic_action.setFont(f_italic)
        self._italic_action.toggled.connect(self.canvas.set_italic)
        font_menu.addAction(self._italic_action)

        self._font_btn.setMenu(font_menu)

        font_btn_action = QWidgetAction(self)
        font_btn_action.setDefaultWidget(self._font_btn)
        main_tb.addAction(font_btn_action)

        # Guardar referencia para enable/disable
        self._font_toolbar = font_menu
        self._set_font_toolbar_enabled(False)

    def _build_thumbnail_panel(self):
        self._thumb_panel = ThumbnailPanel(self.canvas, self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._thumb_panel)
        self._thumb_panel.refresh()

    def _build_statusbar(self):
        bar = self.statusBar()
        bar.setStyleSheet("background: #2b2b2b; color: #aaaaaa; font-size: 12px;")
        bar.showMessage(
            "Listo  ·  📝 Doble clic para editar  ·  🔒 Bloquear fija el elemento  "
            "·  🕐 Autoguardado cada 2 min  ·  Ctrl+S guardar PDF  ·  Supr eliminar"
        )

    # ------------------------------------------------------------------ #
    #  Archivos recientes
    # ------------------------------------------------------------------ #

    def _rebuild_recent_menu(self):
        self._recent_menu.clear()
        files = self._recent_files.get_all()
        if not files:
            no_recent = QAction("(sin archivos recientes)", self)
            no_recent.setEnabled(False)
            self._recent_menu.addAction(no_recent)
        else:
            for path in files:
                action = QAction(f"  {path}", self)
                action.triggered.connect(lambda checked, p=path: self.canvas.load_from_path(p))
                self._recent_menu.addAction(action)
            self._recent_menu.addSeparator()
            clear_action = QAction("🗑️  Limpiar recientes", self)
            clear_action.triggered.connect(self._clear_recents)
            self._recent_menu.addAction(clear_action)

    def _clear_recents(self):
        self._recent_files.clear()
        self._rebuild_recent_menu()

    # ------------------------------------------------------------------ #
    #  Controles de fuente
    # ------------------------------------------------------------------ #

    def _on_selection_changed(self):
        text_item = self.canvas.selected_text_item()
        self._set_font_toolbar_enabled(text_item is not None)
        if text_item:
            f = text_item.font()
            # Bloquear señales para no disparar cambios mientras actualizamos
            self._font_combo.blockSignals(True)
            self._font_size.blockSignals(True)
            self._bold_action.blockSignals(True)
            self._italic_action.blockSignals(True)

            self._font_combo.setCurrentFont(f)
            self._font_size.setValue(f.pointSize())
            self._bold_action.setChecked(f.bold())
            self._italic_action.setChecked(f.italic())

            self._font_combo.blockSignals(False)
            self._font_size.blockSignals(False)
            self._bold_action.blockSignals(False)
            self._italic_action.blockSignals(False)

    def _set_font_toolbar_enabled(self, enabled: bool):
        self._font_btn.setEnabled(enabled)
        if not enabled:
            self._font_btn.setToolTip("Selecciona una caja de texto para cambiar la fuente")