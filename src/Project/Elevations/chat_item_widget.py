from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
import os
from datetime import datetime

class ChatItemWidget(QWidget):
    def __init__(self, text=None, image_path=None, date=None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        if image_path:
            img_label = QLabel()
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                img_label.setPixmap(pixmap.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                img_label.setText("[Image not found]")
            layout.addWidget(img_label)
        if text:
            text_label = QLabel(text)
            text_label.setWordWrap(True)
            layout.addWidget(text_label)
        if date:
            # Use Windows-compatible format string
            date_label = QLabel(date.strftime('%m/%d/%y %H:%M'))
            date_label.setStyleSheet("color: #888; font-size: 12px;")
            layout.addWidget(date_label, alignment=Qt.AlignRight)
        layout.addStretch(1)
