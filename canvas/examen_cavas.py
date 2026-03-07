from PyQt6.QtWidgets import QGraphicsView , QFileDialog
from PyQt6.QtGui import QPainter , QPixmap
from PyQt6.QtCore import Qt

from canvas.exam_scene import ExamScene
from canvas.text_item import TextItem
from canvas.image_item import ImageItem

class ExamCanvas(QGraphicsView):

    """ Vista principal del examens , gestiona zoom , adicion y eliminacion de elementos"""

    ZOOM_MIN = 0.2
    ZOOM_MAX = 4.0

    def __init__(self, parent=None):
        super().__init__(parent)

        self._scene = ExamenScene(self)
        self.setScene(self._scene)


        # Calidad del renderizado
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)


        # Comportamiento de la vista
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.styleSheet("background: #D0D0D0; border: none;")

        self._zoom_level = 1.0


        # -- LLamadas publicas desde la toolbar --

        def add_text_item(self):
            """Crea una nueva caja de texto en el centro de la hoja"""
            item = TextItem()
            pos = self._center_in_scene()
            item.setPos(pos.x() - item.text_width() / 2, pos.y() -20)
            self._scene.addItem(item)
            self._scene.clearSelection()
            item.setSelected(True)

        def add_image_item(self):
            """Abre un dialogo para elegir la imagen y la añade al centro de la hoja"""
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Seleccionar imagen",
                "",
                "Imagenes (*.png *jpg *.jpeg *.bmp *.gif);;Todos los archivos (*)",
            )
            if not path:
                return
            
            pixmap = QPixmap(path)
            if pixmap.isNull():
                return
            
            # Redimensionar la imagen si es demasiado grande*
            max_w = ExamScene.PAGE_W * 0.6
            if pixmap.width() > max_w:
                pixmap = pixmap.scaledToWidth(
                    int(max_w), Qt.TransformationMode.SmoothTransformation
                )


            item = ImageItem(pixmap)
            pos = self._center_in_scene()
            item.setPos(pos.x() - item.img_width / 2, pos.y() - item.img_height / 2)
            self._scene.addItem(item)
            self._scene.clearSelection()
            item.setSelected(True)

        def delete_selected(self):
            """Elimina el elemento seleccionado"""
            for item in self._scene.selectedItems():
                self._scene.removeItem(item)

        def zoom_by(self, factor: float):
            """Aplica un zoom relativo al nivel actual"""
            new_zoom = self._zoom_level * factor
            if not (self.ZOOM_MIN <= new_zoom <= self.ZOOM_MAX):
                return
            self._zoom_level = new_zoom
            self.scale(factor, factor)

        def zoom_fit(self):
            """ Ajusta el zoom para que la hoja quema en la ventana"""
            self.resetTransform()
            self._zoom_level = 1.0
            self.fitInView(
                self._scene.sceneRect(),
                Qt.AspectRatioMode.KeepAspectRatio,
            )



# -- Eventos --

        def KeyPressEvent(self , event):
            if event.key() == Qt.Key.Key_Delete:
                self.delete_selected()
            else:
                super().keyPressEvent(event)

        def wheelEvent(self , event):
            "Zoom con la rueda del raton"
            delta = event.angleDelta().y()
            factor = 1.15 if delta > 0 else 1 / 1.15
            self.zoom_by(factor)


# --Auxiliares --


        def _center_in_scene(self):
            """Devuelve el punto central de la vista"""
            return self.mapToScene(self.viewport().rect().center())