
import json
import os
import shutil
from aws_utils import upload_to_s3
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QStackedLayout, QFrame, QFileDialog, QMessageBox, QGridLayout,
    QToolButton, QMenu, QInputDialog, QGroupBox, QSizePolicy
)
from styles import (
    SIDEBAR_STYLE, HEADER_STYLE, ADD_ELEVATION_BTN_STYLE,
    ELEVATION_CARD_STYLE, ADD_ELEVATION_CARD_STYLE, FOLDER_CONTAINER_STYLE
)
from layout.flowlayout import FlowLayout
from Project.Sidebar import SidebarNav
from Project.Elevations.elevation_card import ElevationCard
from Project.Findings.findings_widget import FindingsWidget
from Project.Elevations.elevation_add_dialog import ElevationAddDialog
from Project.Elevations.elevation_overview import ElevationOverviewWidget
from Project.Photos.Photo_finding import PhotoGalleryWidget
from functools import partial

class AddElevationCard(QWidget):
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(180, 140)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        label = QLabel("+ Add Elevation")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: #bbb; font-size: 16px;")
        layout.addWidget(label)
        self.setStyleSheet(ADD_ELEVATION_CARD_STYLE)

    def mousePressEvent(self, event):
        self.clicked.emit()


class ProjectPage(QWidget):

    def go_back(self):
        self.back_to_home.emit()
    back_to_home = Signal()  # Signal to notify parent to go back


    def __init__(self, project_data, parent=None):
        print("[ProjectPage] __init__ called")
        super().__init__(parent)
        self.project_data = project_data
        # Ensure file_path is set for saving
        if 'file_path' not in self.project_data or not self.project_data['file_path']:
            folder = self.project_data.get('folder')
            if folder:
                self.project_data['file_path'] = os.path.join(folder, 'project.json')
            else:
                # Try to infer from project name/code
                storage_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'storage'))
                project_name = self.project_data.get('name')
                project_code = self.project_data.get('subtitle') or self.project_data.get('code')
                if project_name and project_code:
                    folder_name = f"{project_name}_{project_code}"
                    folder_path = os.path.join(storage_dir, folder_name)
                    self.project_data['file_path'] = os.path.join(folder_path, 'project.json')
                    self.project_data['folder'] = folder_path
                else:
                    print("[DEBUG] Could not infer file_path: missing name or code.")

        # Always reload project.json from disk to get latest elevations
        file_path = self.project_data.get('file_path')
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                print(f"[DEBUG] Reloaded project_data from disk in __init__: {loaded}")
                self.project_data = loaded
            except Exception as e:
                print(f"[DEBUG] Failed to reload project.json in __init__: {e}")
        # Main vertical layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        print("[ProjectPage] main_layout created")

        # Header at the top
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 8, 16, 8)
        print("[ProjectPage] header created")

        # Back button
        back_btn = QPushButton("← Back")
        back_btn.setFixedWidth(80)
        back_btn.clicked.connect(self.go_back)
        header_layout.addWidget(back_btn)

        project_label = QLabel(f"Project Overview: {project_data.get('name', 'Project')}")
        project_label.setStyleSheet(HEADER_STYLE)
        header_layout.addWidget(project_label)
        header_layout.addStretch()
        main_layout.addWidget(header)
        print("[ProjectPage] header added")

        # Horizontal layout for sidebar and content
        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(0)
        main_layout.addLayout(content_row, 1)
        print("[ProjectPage] content_row created")

        # Sidebar - pass project name for findings list
        project_name = None
        if 'folder' in self.project_data and self.project_data['folder']:
            project_name = os.path.basename(self.project_data['folder'])
        elif 'name' in self.project_data:
            project_name = self.project_data['name']
        
        self.sidebar = SidebarNav(project_name=project_name)
        self.sidebar.setFixedWidth(240)
        self.sidebar.setStyleSheet(SIDEBAR_STYLE)
        sidebar_container = QVBoxLayout()
        sidebar_container.setContentsMargins(0, 0, 0, 0)
        sidebar_container.addWidget(self.sidebar, alignment=Qt.AlignTop)
        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar_container)
        sidebar_widget.setStyleSheet(SIDEBAR_STYLE)
        content_row.addWidget(sidebar_widget)
        print("[ProjectPage] sidebar created")

        # Stacked layout for main content
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setAlignment(Qt.AlignTop)
        self.stacked_content = QStackedLayout()
        content_layout.addLayout(self.stacked_content)
        content_row.addWidget(content_container, 1)
        print("[ProjectPage] stacked_content created")

        # Elevations section widget
        self.elevations_widget = QWidget()
        elevations_layout = QVBoxLayout(self.elevations_widget)
        elevations_layout.setContentsMargins(24, 12, 24, 24)
        elevations_layout.setAlignment(Qt.AlignTop)
        print("[ProjectPage] elevations_widget created")

        # Add Elevation, New Folder, and Action buttons
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.setSpacing(8)

        add_elevation_btn = QPushButton("+ Add Elevation")
        add_elevation_btn.setStyleSheet(ADD_ELEVATION_BTN_STYLE)
        add_elevation_btn.setFixedWidth(140)
        add_elevation_btn.clicked.connect(self.add_elevation)
        btn_row.addWidget(add_elevation_btn)

        new_folder_btn = QPushButton("+ New Folder")
        new_folder_btn.setStyleSheet(ADD_ELEVATION_BTN_STYLE)
        new_folder_btn.setFixedWidth(140)
        new_folder_btn.clicked.connect(self.add_folder)
        btn_row.addWidget(new_folder_btn)

        action_btn = QToolButton()
        action_btn.setText("Action")
        action_btn.setFixedWidth(140)
        action_menu = QMenu()
        action_menu.addAction("Select all", self.select_all)
        action_menu.addAction("Deselect all", self.deselect_all)
        action_menu.addSeparator()
        action_menu.addAction("Delete", self.delete_selected)
        action_btn.setMenu(action_menu)
        action_btn.setPopupMode(QToolButton.InstantPopup)
        btn_row.addWidget(action_btn)

        btn_row.addStretch()
        elevations_layout.addLayout(btn_row)
        print("[ProjectPage] btn_row created")

        # Elevation grid
        # Always load folders from project_data['elevations'] if present, else default
        self.folders = self.project_data.get('elevations', [
            {"name": "Folder 1", "items": []}
        ])
        print(f"[DEBUG] Loaded folders in __init__: {self.folders}")
        self.project_data['elevations'] = self.folders
        self.grid_widget = QWidget()
        self.grid_layout = QVBoxLayout(self.grid_widget)
        self.grid_layout.setSpacing(16)
        elevations_layout.addWidget(self.grid_widget)

        self.stacked_content.addWidget(self.elevations_widget)  # index 0
        print("[ProjectPage] elevation grid created")

        # Scaffold other section widgets
        # Get project name for findings widget
        project_name = None
        if 'folder' in self.project_data and self.project_data['folder']:
            project_name = os.path.basename(self.project_data['folder'])
        elif 'name' in self.project_data:
            project_name = self.project_data['name']
        
        self.findings_widget = FindingsWidget(project_name=project_name)
        self.stacked_content.addWidget(self.findings_widget)  # index 1

        self.photos_widget = PhotoGalleryWidget(project_name=project_name)
        self.stacked_content.addWidget(self.photos_widget)  # index 2

        self.drops_widget = QLabel("Drops Section (Coming Soon)")
        self.stacked_content.addWidget(self.drops_widget)  # index 3

        self.forms_widget = QLabel("Forms Section (Coming Soon)")
        self.stacked_content.addWidget(self.forms_widget)  # index 4

        self.files_widget = QLabel("Files Section (Coming Soon)")
        self.stacked_content.addWidget(self.files_widget)  # index 5

        self.model_widget = QLabel("3D Model Section (Coming Soon)")
        self.stacked_content.addWidget(self.model_widget)  # index 6
        print("[ProjectPage] other sections created")

        # Connect sidebar navigation to section switching
        self.sidebar.nav_bar.section_selected.connect(self.switch_section)
        print("[ProjectPage] sidebar nav connected")

    # Always show folders/cards on load
        self.populate_elevation_grid()
        print(f"[DEBUG] Called populate_elevation_grid() in __init__")

    def save_project(self):
        """Save the current project_data (including elevations) to its file."""
        file_path = self.project_data.get('file_path')
        print(f"[DEBUG] save_project: file_path={file_path}")
        if not file_path:
            print("[ProjectPage] No file_path in project_data, cannot save.")
            print(f"[DEBUG] project_data: {self.project_data}")
            return
        self.project_data['elevations'] = self.folders
        try:
            print(f"[DEBUG] Writing project_data to {file_path}: {self.project_data}")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.project_data, f, indent=2)
            print(f"[ProjectPage] Project saved to {file_path}")
            # Reload from disk to ensure UI and memory match
            with open(file_path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            self.project_data = loaded
            self.folders = loaded.get('elevations', [])
            print(f"[DEBUG] Reloaded project_data from disk: {self.project_data}")
        except Exception as e:
            print(f"[ProjectPage] Error saving project: {e}")

    def add_elevation(self):
        dialog = ElevationAddDialog(self)
        while True:
            if not dialog.exec():
                break  # User cancelled
            name, file_path = dialog.get_data()
            if not file_path:
                QMessageBox.information(self, "Missing File", "Need PDF or photo of elevation.")
                continue
            if not name:
                QMessageBox.information(self, "Missing Name", "Please enter a name for the elevation.")
                continue
            if not self.folders:
                self.folders.append({"name": "Default Folder", "items": []})
            self.folders[-1]["items"].append([name, file_path])
            self.save_project()
            self.populate_elevation_grid()
            break

    def add_folder(self):
        name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
        if ok and name:
            self.folders.append({"name": name, "items": []})
            self.save_project()
            self.populate_elevation_grid()

    def switch_section(self, section_name):
        section_map = {
            "Elevation": 0,
            "Findings": 1,
            "Photos": 2,
            "Drops": 3,
            "Forms": 4,
            "Files": 5,
            "3D Model": 6,
        }
        idx = section_map.get(section_name, 0)
        self.stacked_content.setCurrentIndex(idx)
        
        # If switching to findings, refresh the findings widget to show latest data
        if section_name == "Findings":
            # Get project name
            project_name = None
            if 'folder' in self.project_data and self.project_data['folder']:
                project_name = os.path.basename(self.project_data['folder'])
            elif 'name' in self.project_data:
                project_name = self.project_data['name']
            
            if project_name:
                self.findings_widget.refresh(project_name)

    def populate_elevation_grid(self):
        # Clear previous
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            widget = item.widget()
            if widget:
                widget.setParent(None)
        # For each folder, add a container with its own grid layout
        for folder_idx, folder in enumerate(self.folders):
            folder_container = QWidget()
            folder_container.setStyleSheet(FOLDER_CONTAINER_STYLE)
            folder_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
            folder_vbox = QVBoxLayout(folder_container)
            folder_label = QLabel(folder["name"])
            folder_label.setStyleSheet("font-weight: bold; font-size: 15px; margin-bottom: 4px;")
            folder_vbox.addWidget(folder_label)
            # QGridLayout for cards
            grid = QGridLayout()
            grid.setSpacing(8)
            row = 0
            col = 0
            max_cols = 3
            for item in folder["items"]:
                # Support both [name, path] and [name, local_path, s3_url]
                if len(item) == 3:
                    name, local_path, s3_url = item
                else:
                    name, local_path = item
                    s3_url = None
                card = ElevationCard(name, local_path)
                card.clicked.connect(lambda path=local_path, elev_name=name: self.open_elevation_overview(path, elev_name))
                grid.addWidget(card, row, col)
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
            add_card = AddElevationCard()
            add_card.clicked.connect(partial(self.add_elevation_to_folder, folder_idx))
            grid.addWidget(add_card, row, col)
            folder_vbox.addLayout(grid)
            self.grid_layout.addWidget(folder_container)

    def open_elevation_overview(self, pdf_path, elevation_name=None):
        print(f"[DEBUG] open_elevation_overview called with pdf_path: {pdf_path}, elevation_name: {elevation_name}")
        if not os.path.exists(pdf_path):
            print(f"[DEBUG] File does NOT exist: {pdf_path}")
        else:
            print(f"[DEBUG] File exists: {pdf_path}")
        # Get project_name from self.project_data['folder'] if available, else fallback to self.project_data['name']
        project_name = None
        if 'folder' in self.project_data and self.project_data['folder']:
            project_name = os.path.basename(self.project_data['folder'])
        elif 'name' in self.project_data:
            project_name = self.project_data['name']
        overview = ElevationOverviewWidget(pdf_path=pdf_path, sidebar=self.sidebar, project_name=project_name, elevation_name=elevation_name)
        overview.back_to_project.connect(self.show_elevations_overview)
        self.stacked_content.addWidget(overview)
        self.stacked_content.setCurrentWidget(overview)

    def show_elevations_overview(self):
        # Assumes self.elevations_widget is the main elevations overview
        self.stacked_content.setCurrentWidget(self.elevations_widget)

    def delete_selected(self):
        QMessageBox.information(self, "Delete", "Delete Selected clicked (implement selection logic).")

    def delete_all(self):
        reply = QMessageBox.question(self, "Delete All", "Are you sure you want to delete all elevations?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            for folder in self.folders:
                folder["items"].clear()
            self.save_project()
            self.populate_elevation_grid()

    def select_all(self):
        QMessageBox.information(self, "Select All", "Select all clicked (implement selection logic).")

    def deselect_all(self):
        QMessageBox.information(self, "Deselect All", "Deselect all clicked (implement selection logic).")

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def add_elevation_to_folder(self, folder_idx):
        dialog = ElevationAddDialog(self)
        if dialog.exec():
            name, file_path = dialog.get_data()
            print(f"[DEBUG] add_elevation_to_folder: name={name}, file_path={file_path}")
            if not file_path:
                print("[DEBUG] No file selected.")
                QMessageBox.information(self, "Missing File", "Need PDF or photo of elevation.")
                return
            if not name:
                print("[DEBUG] No name entered.")
                QMessageBox.information(self, "Missing Name", "Please enter a name for the elevation.")
                return

            # Always save to storage/ProjectName_Code/elevations/filename
            storage_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'storage'))
            print(f"[DEBUG] storage_dir={storage_dir}")
            project_folder_name = None
            if 'folder' in self.project_data:
                project_folder_name = os.path.basename(self.project_data['folder'])
            elif 'file_path' in self.project_data:
                project_folder_name = os.path.basename(os.path.dirname(self.project_data['file_path']))
            print(f"[DEBUG] project_folder_name={project_folder_name}")
            if not project_folder_name:
                print("[DEBUG] Cannot determine project folder name.")
                QMessageBox.warning(self, "Project Error", "Cannot determine project folder name.")
                return
            project_folder = os.path.join(storage_dir, project_folder_name)
            print(f"[DEBUG] project_folder={project_folder}")
            elevations_folder = os.path.join(project_folder, 'elevations')
            print(f"[DEBUG] elevations_folder={elevations_folder}")
            os.makedirs(elevations_folder, exist_ok=True)

            ext = os.path.splitext(file_path)[1]
            safe_name = name.replace(' ', '_')
            local_filename = f"{safe_name}{ext}"
            local_path = os.path.join(elevations_folder, local_filename)
            print(f"[DEBUG] local_path={local_path}")
            try:
                shutil.copy2(file_path, local_path)
                print(f"[DEBUG] Copied file to {local_path}")
            except Exception as e:
                print(f"[DEBUG] File copy error: {e}")
                QMessageBox.warning(self, "File Copy Error", f"Could not copy file: {e}")
                return

            # Always add to local project data and save locally
            s3_url = None
            try:
                project_name = os.path.basename(project_folder)
                s3_key = f"{project_name}/elevations/{local_filename}"
                bucket = os.environ.get('S3_BUCKET', 'your-default-bucket')
                print(f"[DEBUG] Uploading to S3: bucket={bucket}, s3_key={s3_key}")
                s3_url = upload_to_s3(local_path, bucket, s3_key)
                print(f"[DEBUG] S3 URL: {s3_url}")
            except Exception as e:
                print(f"[DEBUG] S3 upload error: {e}")
                # S3 upload is optional, continue with local save
                s3_url = None

            self.folders[folder_idx]["items"].append([name, local_path, s3_url])
            print(f"[DEBUG] Added elevation to folder: {[name, local_path, s3_url]}")
            self.save_project()
            print(f"[DEBUG] Called save_project()")
            # Confirm file exists locally
            if os.path.exists(local_path):
                print(f"[DEBUG] Local elevation file exists: {local_path}")
            else:
                print(f"[DEBUG] Local elevation file NOT FOUND: {local_path}")
            # Confirm project.json update
            if os.path.exists(self.project_data['file_path']):
                with open(self.project_data['file_path'], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"[DEBUG] project.json content after save: {json.dumps(data, indent=2)}")
            else:
                print(f"[DEBUG] project.json NOT FOUND: {self.project_data['file_path']}")
            self.populate_elevation_grid()
            print(f"[DEBUG] Called populate_elevation_grid()")


class AddElevationCard(QWidget):
    clicked = Signal()

    def __init__(self, parent=None):
        print("[AddElevationCard] __init__ called")
        super().__init__(parent)
        self.setFixedSize(180, 140)  # Make sure this matches ElevationCard
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        label = QLabel("+ Add Elevation")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: #bbb; font-size: 16px;")
        layout.addWidget(label)
        self.setStyleSheet(ADD_ELEVATION_CARD_STYLE)

    def mousePressEvent(self, event):
        self.clicked.emit()