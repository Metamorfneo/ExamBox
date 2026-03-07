from PyQt6.QtWidgets import QMainWindow, QToolBar
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtCore import Qt

from canvas.exam_canvas import ExamCanvas

TOOLBAR_STYLE = """
    QToolBar {
        background: #2b2b2b;
        border-bottom: 1px solid #1a1a1a;
        padding: 4px 8px;
        spacing: 6px;
    }
    QToolButton {
        color: #eeeeee;
        background: transparent;
        border: 1px solid transparent;
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 12px;
    }
    QToolButton:hover {
        background: #444444;
        border-color: #666666;
    }
    QToolButton:pressed {
        background: #555555;
    }
    QToolButton:checked {
        background: #1a5fa8;
        border-color: #4A90D9;
        color: #ffffff;
    }
    QToolBar::separator {
        background: #555555;
        width: 1px;
        margin: 4px 6px;
    }
"""


class MainWindow(QMainWindow):
    """Ventana principal de ExamBox."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ExamBox — Nuevo examen")
        self.setMinimumSize(1100, 780)

        self._build_canvas()
        self._build_toolbar()
        self._build_statusbar()

    # ------------------------------------------------------------------ #
    #  UI Construction
    # ------------------------------------------------------------------ #

    def _build_canvas(self):
        self.canvas = ExamCanvas(self)
        self.setCentralWidget(self.canvas)

    def _build_toolbar(self):
        tb = QToolBar("Herramientas")
        tb.setMovable(False)
        tb.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        tb.setStyleSheet(TOOLBAR_STYLE)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tb)

        # -- Archivo --
        new_exam = QAction("🆕  Nuevo", self)
        new_exam.setShortcut(QKeySequence("Ctrl+N"))
        new_exam.setStatusTip("Nuevo examen (Ctrl+N)")
        new_exam.triggered.connect(self.canvas.new_exam)
        tb.addAction(new_exam)

        open_exam = QAction("📂  Abrir", self)
        open_exam.setShortcut(QKeySequence("Ctrl+O"))
        open_exam.setStatusTip("Abrir examen guardado (Ctrl+O)")
        open_exam.triggered.connect(self.canvas.load)
        tb.addAction(open_exam)

        save_exam = QAction("💾  Guardar", self)
        save_exam.setShortcut(QKeySequence("Ctrl+S"))
        save_exam.setStatusTip("Guardar examen (Ctrl+S)")
        save_exam.triggered.connect(self.canvas.save)
        tb.addAction(save_exam)

        save_as_exam = QAction("💾  Guardar como", self)
        save_as_exam.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_exam.setStatusTip("Guardar examen como... (Ctrl+Shift+S)")
        save_as_exam.triggered.connect(self.canvas.save_as)
        tb.addAction(save_as_exam)

        export_pdf = QAction("📄  Exportar PDF", self)
        export_pdf.setShortcut(QKeySequence("Ctrl+E"))
        export_pdf.setStatusTip("Exportar el examen como PDF (Ctrl+E)")
        export_pdf.triggered.connect(self.canvas.export_pdf)
        tb.addAction(export_pdf)

        tb.addSeparator()

        # -- Deshacer / Rehacer --
        undo_action = QAction("↩  Deshacer", self)
        undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        undo_action.setStatusTip("Deshacer última acción (Ctrl+Z)")
        undo_action.triggered.connect(self.canvas.undo)
        tb.addAction(undo_action)

        redo_action = QAction("↪  Rehacer", self)
        redo_action.setShortcut(QKeySequence("Ctrl+Y"))
        redo_action.setStatusTip("Rehacer acción (Ctrl+Y)")
        redo_action.triggered.connect(self.canvas.redo)
        tb.addAction(redo_action)

        tb.addSeparator()

        # -- Añadir elementos --
        add_text = QAction("📝  Texto", self)
        add_text.setStatusTip("Añadir una caja de texto al examen")
        add_text.triggered.connect(self.canvas.add_text_item)
        tb.addAction(add_text)

        add_img = QAction("🖼️  Imagen", self)
        add_img.setStatusTip("Añadir una imagen desde archivo")
        add_img.triggered.connect(self.canvas.add_image_item)
        tb.addAction(add_img)

        tb.addSeparator()

        # -- Eliminar --
        delete = QAction("🗑️  Eliminar", self)
        delete.setStatusTip("Eliminar el elemento seleccionado (Supr)")
        delete.triggered.connect(self.canvas.delete_selected)
        tb.addAction(delete)

        tb.addSeparator()

        # -- Opciones de vista / layout (botones tipo toggle) --
        grid_action = QAction("⊞  Cuadrícula", self)
        grid_action.setCheckable(True)
        grid_action.setChecked(False)
        grid_action.setStatusTip("Mostrar/ocultar cuadrícula de ayuda")
        grid_action.toggled.connect(lambda checked: setattr(self.canvas, "show_grid", checked))
        tb.addAction(grid_action)

        overlap_action = QAction("⬜  Sin superposición", self)
        overlap_action.setCheckable(True)
        overlap_action.setChecked(False)
        overlap_action.setStatusTip(
            "Activado: los elementos se empujan hacia abajo al solaparse. "
            "Desactivado: pueden superponerse libremente."
        )
        overlap_action.toggled.connect(lambda checked: setattr(self.canvas, "no_overlap", checked))
        tb.addAction(overlap_action)

        tb.addSeparator()

        # -- Páginas --
        add_page = QAction("📄+  Nueva hoja", self)
        add_page.setShortcut(QKeySequence("Ctrl+M"))
        add_page.setStatusTip("Añadir una nueva hoja A4 debajo (Ctrl+M)")
        add_page.triggered.connect(self.canvas.add_page)
        tb.addAction(add_page)

        tb.addSeparator()

        # -- Zoom --
        zoom_in = QAction("🔍+  Zoom +", self)
        zoom_in.setStatusTip("Acercar (rueda del ratón)")
        zoom_in.triggered.connect(lambda: self.canvas.zoom_by(1.2))
        tb.addAction(zoom_in)

        zoom_out = QAction("🔍−  Zoom −", self)
        zoom_out.setStatusTip("Alejar (rueda del ratón)")
        zoom_out.triggered.connect(lambda: self.canvas.zoom_by(1 / 1.2))
        tb.addAction(zoom_out)

        zoom_reset = QAction("⊙  Encajar", self)
        zoom_reset.setStatusTip("Ajustar la hoja en pantalla")
        zoom_reset.triggered.connect(self.canvas.zoom_fit)
        tb.addAction(zoom_reset)

    def _build_statusbar(self):
        bar = self.statusBar()
        bar.setStyleSheet("background: #2b2b2b; color: #aaaaaa; font-size: 12px;")
        bar.showMessage(
            "Listo  ·  📝 Doble clic para editar texto  "
            "·  ↩↪ Ctrl+Z / Ctrl+Y para deshacer/rehacer  "
            "·  ⬜ Sin superposición empuja elementos al moverlos  "
            "·  Supr para eliminar  ·  Ctrl+S guardar  ·  Ctrl+E PDF"
        )