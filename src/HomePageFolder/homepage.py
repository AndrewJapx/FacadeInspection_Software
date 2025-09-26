import boto3
import os
import json
def get_s3_client():
    """
    Returns a boto3 S3 client. Uses LocalStack if USE_LOCALSTACK=1 is set in the environment.
    """
    if os.environ.get('USE_LOCALSTACK') == '1':
        return boto3.client(
            's3',
            aws_access_key_id='test',
            aws_secret_access_key='test',
            region_name='us-east-1',
            endpoint_url='http://localhost:4566'
        )
    else:
        return boto3.client('s3')
from PySide6.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpacerItem, QSizePolicy, QGridLayout, QScrollArea, QDialog, QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QResizeEvent
from Project.project_card import ProjectCard
from Project.project_page import ProjectPage

class NewProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create new project")
        self.setFixedSize(400, 200)
        layout = QVBoxLayout(self)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter project name")
        self.code_input = QLineEdit()
        self.code_input.setReadOnly(True)
        self.code_input.setText(self.generate_code())

        layout.addWidget(QLabel("Name *"))
        layout.addWidget(self.name_input)
        layout.addWidget(QLabel("Code"))
        layout.addWidget(self.code_input)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def generate_code(self):
        # Simple auto-generated code, can be improved
        from random import randint
        return f"PRJ{randint(1000,9999)}"

    def accept(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Input Error", "Project name is required.")
            return
        super().accept()

class NavBar(QWidget):
    def __init__(self, homepage_parent=None):
        super().__init__()
        self.homepage_parent = homepage_parent
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        layout.addStretch(1)
        for name in ["Projects", "People", "Account", "Templates", "Integrations"]:
            btn = QPushButton(name)
            if name == "Templates" and homepage_parent:
                btn.clicked.connect(self.show_templates)
            layout.addWidget(btn)
        layout.addStretch(1)
    
    def show_templates(self):
        if self.homepage_parent:
            main_window = self.homepage_parent.window()
            if hasattr(main_window, 'show_templates'):
                main_window.show_templates()

class HomePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)

        # --- Header widget ---
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Left: Logo or picture
        logo_label = QLabel()
        logo_pixmap = QPixmap(40, 40)
        logo_pixmap.fill(Qt.gray)  # Placeholder, replace with your logo
        logo_label.setPixmap(logo_pixmap)
        header_layout.addWidget(logo_label)

        # Center: NavBar widget (centered)
        nav_bar = NavBar(self)
        header_layout.addStretch(1)
        header_layout.addWidget(nav_bar, alignment=Qt.AlignCenter)
        header_layout.addStretch(1)

        # Right: Notification, Help, Business Plan, Profile
        header_layout.addWidget(QPushButton("🔔"))  # Notification
        header_layout.addWidget(QPushButton("?"))   # Help
        header_layout.addWidget(QPushButton("Business Plan"))
        profile_btn = QPushButton("Lin huixiong")   # Profile button with user name
        header_layout.addWidget(profile_btn)

        # --- Top widget: Navigation buttons (as before) ---
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)

        new_project_btn = QPushButton("+ New project")
        generate_reports_btn = QPushButton("Generate reports")
        sort_btn = QPushButton("Sort")
        filter_btn = QPushButton("Filter projects")
        search_box = QLineEdit()
        search_box.setPlaceholderText("Search projects")
        search_box.setMaximumWidth(200)

        top_layout.addWidget(new_project_btn)
        top_layout.addWidget(generate_reports_btn)
        top_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        top_layout.addWidget(sort_btn)
        top_layout.addWidget(filter_btn)
        top_layout.addWidget(search_box)

        # --- Project grid area with side margins ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        grid_outer = QWidget()
        grid_outer_layout = QHBoxLayout(grid_outer)
        grid_outer_layout.setContentsMargins(40, 0, 40, 0)  # 40px margin left/right, adjust as needed

        grid_container = QWidget()
        self.grid_layout = QGridLayout(grid_container)
        self.grid_layout.setSpacing(24)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        grid_container.setLayout(self.grid_layout)

        grid_outer_layout.addWidget(grid_container)
        scroll.setWidget(grid_outer)

        # Store project data (not widgets)
        self.projects = []

        self.load_projects_from_storage()

        # --- Assemble main layout ---
        main_layout.addWidget(header_widget)
        main_layout.addWidget(top_widget)
        main_layout.addWidget(scroll, 1)
        main_layout.setStretch(0, 0)
        main_layout.setStretch(1, 0)
        main_layout.setStretch(2, 1)

        new_project_btn.clicked.connect(self.handle_new_project)

    def showEvent(self, event):
        # Reload projects from disk every time the homepage is shown
        self.projects = []
        self.load_projects_from_storage()
        self.refresh_grid()
        super().showEvent(event)

    def load_projects_from_storage(self):
        storage_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'storage'))
        if not os.path.exists(storage_dir):
            return
        for foldername in os.listdir(storage_dir):
            folder_path = os.path.join(storage_dir, foldername)
            if os.path.isdir(folder_path):
                project_json = os.path.join(folder_path, "project.json")
                if os.path.exists(project_json):
                    try:
                        with open(project_json) as f:
                            project_data = json.load(f)
                        name = project_data.get('name', foldername)
                        subtitle = project_data.get('subtitle', '')
                        members = project_data.get('members', 0)
                        code = project_data.get('subtitle', '') or project_data.get('code', '')
                        file_path = project_json
                        self.projects.append({
                            "name": name,
                            "subtitle": subtitle,
                            "members": members,
                            "code": code,
                            "file_path": file_path,
                            "folder": folder_path
                        })
                    except Exception as e:
                        print(f"[WARN] Could not load project {foldername}: {e}")

    def handle_new_project(self):
        dialog = NewProjectDialog(self)
        if dialog.exec():
            name = dialog.name_input.text()
            code = dialog.code_input.text()
            # Prepare all fields for project.json
            storage_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'storage'))
            os.makedirs(storage_dir, exist_ok=True)
            project_folder = os.path.join(storage_dir, f"{name}_{code}")
            os.makedirs(project_folder, exist_ok=True)
            local_path = os.path.join(project_folder, "project.json")
            project_data = {
                "name": name,
                "subtitle": code,
                "members": 0,
                "file_path": local_path,
                "folder": project_folder,
                "elevations": []
            }
            with open(local_path, 'w') as f:
                json.dump(project_data, f, indent=2)
            # Add to UI
            self.add_project_card(name, code, 0)
            # Upload project.json to S3 (bucket must exist)
            s3 = get_s3_client()
            bucket = "my-bucket"  # Change to your bucket name
            s3_key = f"projects/{name}_{code}/project.json"
            try:
                s3.upload_file(local_path, bucket, s3_key)
            except Exception as e:
                print(f"[WARN] S3 upload failed: {e}")

    def add_project_card(self, name, subtitle, members):
        # Add all fields for consistency
        storage_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'storage'))
        folder = os.path.join(storage_dir, f"{name}_{subtitle}")
        file_path = os.path.join(folder, "project.json")
        self.projects.append({
            "name": name,
            "subtitle": subtitle,
            "members": members,
            "code": subtitle,
            "file_path": file_path,
            "folder": folder
        })
        self.refresh_grid()

    def refresh_grid(self):
        # Remove all widgets from the grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        grid_width = self.grid_layout.geometry().width() or self.width()
        card_width = 260 + 24
        columns = max(1, (grid_width // card_width))

        for idx, proj in enumerate(self.projects):
            row = idx // columns
            col = idx % columns
            # Pass the full project dict to ProjectCard and connect with full data
            card = ProjectCard(
                proj["name"],
                proj["subtitle"],
                proj["members"],
                proj.get("code", "")
            )
            # Attach the full project dict to the card for click events
            card.project_data = proj
            card.project_clicked.connect(self.open_project_page)
            self.grid_layout.addWidget(card, row, col)

    def open_project_page(self, project_data):
        # Always reload project.json from disk to ensure elevations are up to date
        file_path = project_data.get('file_path')
        folder = project_data.get('folder')
        if not file_path and folder:
            file_path = os.path.join(folder, 'project.json')
        loaded_data = None
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                print(f"[DEBUG] Loaded project_data from disk in open_project_page: {loaded_data}")
            except Exception as e:
                print(f"[DEBUG] Failed to load project.json: {e}")
        if loaded_data:
            project_data = loaded_data
        from mainwindow import MainWindow
        mw = self.window()
        if hasattr(mw, "setCentralWidget"):
            project_page = ProjectPage(project_data)
            if hasattr(mw, "show_homepage"):
                project_page.back_to_home.connect(mw.show_homepage)
            mw.setCentralWidget(project_page)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.refresh_grid()