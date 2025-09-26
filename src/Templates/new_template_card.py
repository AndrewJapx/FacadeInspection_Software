from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

class NewTemplateCard(QFrame):
    """Special card for creating new templates"""
    create_template = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set same size as regular template cards
        self.setFixedSize(260, 200)
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #bbb;
                border-radius: 8px;
                background-color: #f9f9f9;
                margin: 4px;
            }
            QFrame:hover {
                border-color: #2196F3;
                background-color: #f0f8ff;
            }
        """)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Center everything
        layout.addStretch()
        
        # Plus icon
        plus_label = QLabel("+")
        plus_label.setFont(QFont("Arial", 48, QFont.Bold))
        plus_label.setStyleSheet("color: #999; text-align: center;")
        plus_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(plus_label)
        
        # Create new text
        text_label = QLabel("Create New Template")
        text_label.setFont(QFont("Arial", 12, QFont.Bold))
        text_label.setStyleSheet("color: #666; text-align: center; margin-top: 8px;")
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setWordWrap(True)
        layout.addWidget(text_label)
        
        layout.addStretch()
    
    def mousePressEvent(self, event):
        """Handle click to create new template"""
        if event.button() == Qt.LeftButton:
            self.create_template.emit()
        super().mousePressEvent(event)