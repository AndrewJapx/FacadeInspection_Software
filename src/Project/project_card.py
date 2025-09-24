from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout, QApplication
from PySide6.QtCore import Signal, Qt
from styles import PROJECT_CARD_STYLE

class ProjectCard(QFrame):
    project_clicked = Signal(dict)  # Emit project data

    def __init__(self, project_name, subtitle="", members=0, code="", parent=None):
        super().__init__(parent)
        self.setObjectName("ProjectCard")
        self.setFixedSize(260, 100)
        self.setStyleSheet(PROJECT_CARD_STYLE)
        self.project_data = {
            "name": project_name,
            "subtitle": subtitle,
            "members": members,
            "code": code
        }

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(4)

        title = QLabel(project_name)
        title.setObjectName("ProjectTitle")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("ProjectSubtitle")
        members_row = QHBoxLayout()
        members_row.addStretch()
        members_label = QLabel(f"{members} 👥")
        members_label.setObjectName("ProjectMembers")
        members_row.addWidget(members_label)

        layout.addWidget(title)
        layout.addWidget(subtitle_label)
        layout.addLayout(members_row)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.project_clicked.emit(self.project_data)
        super().mousePressEvent(event)