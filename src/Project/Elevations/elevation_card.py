from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt, Signal
from styles import ELEVATION_CARD_STYLE

# For PDF preview
import fitz  # PyMuPDF


class ElevationCard(QWidget):
    clicked = Signal(str)  # emits the preview_path

    def __init__(self, name, preview_path=None, parent=None):
        super().__init__(parent)
        self.preview_path = preview_path
        self.setFixedSize(180, 140)  # Slightly larger for sharper look
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Preview at the top
        preview = QLabel()
        preview.setAlignment(Qt.AlignCenter)
        preview.setFixedHeight(110)
        if preview_path and isinstance(preview_path, str):
            ext = preview_path.lower().split('.')[-1]
            if ext in ('png', 'jpg', 'jpeg'):
                pixmap = QPixmap(preview_path).scaled(200, 110, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                preview.setPixmap(pixmap)
            elif ext == 'pdf':
                try:
                    doc = fitz.open(preview_path)
                    if doc.page_count > 0:
                        page = doc.load_page(0)
                        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x for better quality
                        image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGBA8888 if pix.alpha else QImage.Format_RGB888)
                        pixmap = QPixmap.fromImage(image).scaled(200, 110, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        preview.setPixmap(pixmap)
                    else:
                        preview.setText("PDF (empty)")
                        preview.setStyleSheet("font-size: 18px; color: #888; background: #fafafa;")
                except Exception as e:
                    preview.setText("PDF error")
                    preview.setStyleSheet("font-size: 18px; color: #888; background: #fafafa;")
            else:
                preview.setText("No preview available")
                preview.setStyleSheet("color: #888; background: #fafafa;")
        else:
            preview.setText("No preview available")
            preview.setStyleSheet("color: #888; background: #fafafa;")
        layout.addWidget(preview)

        # Name below preview
        name_label = QLabel(name)
        name_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        name_label.setStyleSheet("font-weight: bold; font-size: 15px; padding: 8px 8px 4px 8px; color: #222;")
        layout.addWidget(name_label)

        self.setStyleSheet(ELEVATION_CARD_STYLE)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.preview_path)
        super().mousePressEvent(event)
