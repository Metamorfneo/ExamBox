from PyQt6.QtWidgets import QGraphicsTextItem , QGraphicsItem , QStyleOptionGraphicsItem , QStyle
from PyQt6.QtGui import QFont , QColor , QPen
from PyQt6.QtCore import Qt


class TextItem(QGraphicsTextItem):
    """Caja de texto movible y editable"""


    DEFAULT_WIDTH = 220.0
    PADDING = 6

    def __init__(self, parent=None):
        super().__init__("Doble click para editar", parent)

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemIsFocusable
        )

        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.setTextWidth(self.DEFAULT_WIDTH)
        self.setFont(Qfont("Arial" , 12))
        self.setDefaultTextColor(QColor("#111111"))



# -- Edicion --

def mouseDoubleClickEvent(self, event):
    self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
    self.setFocus(Qt.FocusReason.MouseFocusReason)
    super().mouseDoubleClickEvent(event)

def focusOutEvent(self, event):
    # Salimos del modo de edición al perder el foco
    self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
    cursor = self.textCursor()
    cursor.clearSelection()
    self.setTextCursor(cursor)
    super().focusOutEvent(event)



    # -- Apariencia --

    def paint(self , painter , option , widget):
        # Suprimir el recuadro de seleccion nativo de Qt
        clean_option = QStyleOptionGraphicsItem(option)
        clean_option.state &= ~QStyle.StateFlag.State_Selected

        rect = self.boundingRect()

        #Fondo amarillo palido
        painter.fillRect(rect, QColor("255 , 253 , 210 , 200"))


        #Borde: Azul punteado si seleccionado , gris solido si no

        if self.isSelected():
            pen = Qpen(Qcolor("#4A30D9"), 1.5, Qt.PenStyle.DashLine)
        else:
            pen = QPen(QColor("#CCCCCC"), 1.0, Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect.adjusted(0.5, 0.5, -0.5, -0.5))


        # -- dibuja el texto por encima

        super().paint(painter, clean_option, widget)