from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QPoint
from styles import FINDING_CARD_STYLE, FINDING_CARD_TITLE_STYLE, FINDING_CARD_META_STYLE

class FindingCard(QFrame):
    def __init__(self, title, status=None, material=None, defect=None, pin_id=None, context_text=None, parent=None):
        super().__init__(parent)
        self.setStyleSheet(FINDING_CARD_STYLE + "margin-bottom: 8px; border: 1px solid #ccc;")
        from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel
        from PySide6.QtGui import QPixmap, QPainter, QColor
        from PySide6.QtCore import Qt, QSize

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # --- Left: Large Status Color Circle ---
        icon_label = QLabel()
        from config.status import STATUS_COLORS
        color = STATUS_COLORS.get(status, '#FF4500')  # fallback to orange-red
        icon_label.setFixedSize(QSize(40, 40))
        icon_label.setStyleSheet(f"background: {color}; border-radius: 8px;")
        main_layout.addWidget(icon_label, alignment=Qt.AlignTop)

        # --- Right: Content ---
        content_layout = QVBoxLayout()
        content_layout.setSpacing(0)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Title
        if title and title.strip():
            title_label = QLabel(title)
            title_label.setStyleSheet("font-size: 15px; font-weight: 500; color: #222;")
            content_layout.addWidget(title_label)
        else:
            content_layout.addWidget(QLabel("<i>Enter title</i>"))

        # Material and Defect
        mat_def = []
        if material:
            mat_def.append(str(material))
        if defect:
            mat_def.append(str(defect))
        if mat_def:
            mat_def_label = QLabel(" | ".join(mat_def))
            mat_def_label.setStyleSheet("font-size: 13px; color: #888; margin-top: 2px;")
            content_layout.addWidget(mat_def_label)

        main_layout.addLayout(content_layout)
