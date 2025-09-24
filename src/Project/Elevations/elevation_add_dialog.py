from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog

class ElevationAddDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Elevation")
        self.selected_file = None

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Elevation Name:"))
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_edit)

        file_row = QHBoxLayout()
        self.file_label = QLabel("No file selected")
        upload_btn = QPushButton("Upload")
        upload_btn.clicked.connect(self.upload_file)
        file_row.addWidget(self.file_label)
        file_row.addWidget(upload_btn)
        layout.addLayout(file_row)

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn)

    def upload_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select File", "", "PDF Files (*.pdf);;Image Files (*.png *.jpg *.jpeg)")
        if file:
            self.selected_file = file
            self.file_label.setText(file.split("/")[-1])

    def get_data(self):
        return self.name_edit.text(), self.selected_file