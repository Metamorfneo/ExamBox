Aplicación de escritorio para confeccionar exámenes con cajas de texto e imágenes arrastrables.
Requisitos

Python 3.10+
PyQt6

Instalación
bashpip install -r requirements.txt
Ejecutar
bashpython main.py
Controles
AcciónCómoMover elementoClic y arrastraEditar textoDoble clic sobre la cajaRedimensionar imagenSelecciona → arrastra el triángulo azul (esquina inferior derecha)Eliminar elementoSelecciona → tecla Supr o botón de la barraZoomRueda del ratónSeleccionar variosClic y arrastra en área vacíaDeseleccionarClic en área vacía
Estructura del proyecto
ExamBox/
├── main.py              # Punto de entrada
├── requirements.txt
├── ui/
│   └── main_window.py   # Ventana principal y barra de herramientas
└── canvas/
    ├── exam_scene.py    # Escena (la "hoja" A4)
    ├── exam_canvas.py   # Vista del canvas con zoom y lógica
    ├── text_item.py     # Caja de texto movible y editable
    └── image_item.py    # Caja de imagen movible y redimensionable
Fases planificadas

 Fase 1 — Canvas con cajas de texto e imagen, movibles y redimensionables
 Fase 2 — Guardar y cargar exámenes (.json)
 Fase 3 — Exportar a PDF e imprimir
 Fase 4 — Undo/Redo, cuadrícula, zoom avanzado
