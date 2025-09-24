# from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QFormLayout, QHBoxLayout, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from styles import LOGIN_WINDOW_STYLESHEET

class LoginWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login")
        self.setStyleSheet(LOGIN_WINDOW_STYLESHEET)

        # Inner layout for the login form
        form_widget = QWidget()
        # FIX: Make the form_widget expand to fill available space
        form_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        form_layout = QVBoxLayout(form_widget)
        form_layout.setAlignment(Qt.AlignTop)

        # Profile photo area (circular QLabel)
        self.photo_label = QLabel()
        self.photo_label.setObjectName("PhotoLabel")
        self.photo_label.setFixedSize(80, 80)
        self.photo_label.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(80, 80)
        pixmap.fill(Qt.transparent)
        self.photo_label.setPixmap(pixmap)
        form_layout.addWidget(self.photo_label, alignment=Qt.AlignHCenter)

        # Login form
        login_form = QFormLayout()
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        login_form.addRow("Email:", self.email_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        login_form.addRow("Password:", self.password_input)

        form_layout.addLayout(login_form)

        self.login_button = QPushButton("Login")
        form_layout.addWidget(self.login_button, alignment=Qt.AlignCenter)

        # Outer layout to center the form_widget
        outer_layout = QVBoxLayout(self)
        outer_layout.addStretch(1)
        h_center = QHBoxLayout()
        h_center.addStretch(1)
        h_center.addWidget(form_widget)
        h_center.addStretch(1)
        outer_layout.addLayout(h_center)
        outer_layout.addStretch(2)

        self.setLayout(outer_layout)

    def sizeHint(self):
        from PySide6.QtCore import QSize
        return QSize(1200, 800)
