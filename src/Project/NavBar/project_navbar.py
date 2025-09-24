# filepath: c:\Users\andre\OneDrive\Documents\FacadeInspection_Software\src\Project\nav_buttons.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PySide6.QtCore import Signal

class ProjectNavBar(QWidget):
    section_selected = Signal(str)  # Signal to emit section name

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.buttons = {}
        for name in ["Elevation", "Findings", "Photos", "Drops", "Forms", "Files", "3D Model"]:
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, n=name: self.section_selected.emit(n))
            layout.addWidget(btn)
            self.buttons[name] = btn