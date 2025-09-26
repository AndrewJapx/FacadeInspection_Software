"""
Photo Gallery Widget - Shows all photos organized by elevation and pin
Provides a visual overview of all uploaded photos in the project
"""

import os
import json
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QFrame, QGridLayout, QComboBox, QGroupBox, QSizePolicy, QDialog,
    QDialogButtonBox, QTextEdit
)
from PySide6.QtGui import QPixmap, QFont, QPalette, QColor
from PySide6.QtCore import Qt, QSize, Signal
from Project.Elevations.chat_data_manager import ChatDataManager


class PhotoThumbnail(QLabel):
    """Individual photo thumbnail with click functionality"""
    photo_clicked = Signal(dict)  # Emits photo info when clicked
    
    def __init__(self, photo_info, parent=None):
        super().__init__(parent)
        self.photo_info = photo_info
        self.setFixedSize(120, 120)
        self.setStyleSheet("""
            QLabel {
                border: 2px solid #ddd;
                border-radius: 8px;
                background: #f9f9f9;
            }
            QLabel:hover {
                border: 2px solid #4CAF50;
                background: #f0f8ff;
            }
        """)
        self.setAlignment(Qt.AlignCenter)
        self.setCursor(Qt.PointingHandCursor)
        
        # Load and display thumbnail
        self.load_thumbnail()
    
    def load_thumbnail(self):
        """Load and display the photo thumbnail"""
        photo_path = self.photo_info.get('path')
        if photo_path and os.path.exists(photo_path):
            pixmap = QPixmap(photo_path)
            if not pixmap.isNull():
                # Scale to fit the thumbnail size while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(116, 116, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.setPixmap(scaled_pixmap)
            else:
                self.setText("Invalid\nImage")
        else:
            self.setText("Image\nNot Found")
    
    def mousePressEvent(self, event):
        """Handle click to show photo details"""
        if event.button() == Qt.LeftButton:
            self.photo_clicked.emit(self.photo_info)


class PinPhotoGroup(QGroupBox):
    """Group widget showing all photos for a specific pin"""
    photo_clicked = Signal(dict)
    
    def __init__(self, pin_id, pin_name, photos, parent=None):
        super().__init__(f"Pin {pin_id}: {pin_name}", parent)
        self.pin_id = pin_id
        self.pin_name = pin_name
        self.photos = photos
        
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 2px solid #ccc;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI for the pin photo group"""
        layout = QVBoxLayout(self)
        
        # Photo count info
        info_label = QLabel(f"{len(self.photos)} photo(s)")
        info_label.setStyleSheet("color: #666; font-size: 10px; font-weight: normal;")
        layout.addWidget(info_label)
        
        # Photos grid
        photos_widget = QWidget()
        photos_layout = QGridLayout(photos_widget)
        photos_layout.setSpacing(8)
        
        # Add photo thumbnails in a grid (4 per row)
        row, col = 0, 0
        for photo in self.photos:
            thumbnail = PhotoThumbnail(photo)
            thumbnail.photo_clicked.connect(self.photo_clicked.emit)
            
            # Add photo date as tooltip
            date_str = photo.get('date', 'Unknown date')
            thumbnail.setToolTip(f"Uploaded: {date_str}\nClick to view details")
            
            photos_layout.addWidget(thumbnail, row, col)
            col += 1
            if col >= 4:  # 4 photos per row
                col = 0
                row += 1
        
        layout.addWidget(photos_widget)


class ElevationPhotoSection(QFrame):
    """Section showing all photos for a specific elevation"""
    photo_clicked = Signal(dict)
    
    def __init__(self, elevation_name, elevation_photos, parent=None):
        super().__init__(parent)
        self.elevation_name = elevation_name
        self.elevation_photos = elevation_photos
        
        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background: #fafafa;
                border: 1px solid #ddd;
                border-radius: 10px;
                margin: 5px;
            }
        """)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI for the elevation section"""
        layout = QVBoxLayout(self)
        
        # Elevation header
        header_layout = QHBoxLayout()
        
        title = QLabel(self.elevation_name)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #2c3e50; margin: 10px;")
        header_layout.addWidget(title)
        
        # Total photo count for this elevation
        total_photos = sum(len(photos) for photos in self.elevation_photos.values())
        count_label = QLabel(f"Total: {total_photos} photos")
        count_label.setStyleSheet("color: #7f8c8d; font-size: 12px; margin: 10px;")
        header_layout.addWidget(count_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Pin groups
        if not self.elevation_photos:
            no_photos_label = QLabel("No photos uploaded for this elevation")
            no_photos_label.setStyleSheet("color: #999; font-style: italic; padding: 20px;")
            no_photos_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(no_photos_label)
        else:
            for pin_id, pin_data in self.elevation_photos.items():
                pin_name = pin_data.get('pin_name', f'Pin {pin_id}')
                photos = pin_data.get('photos', [])
                
                if photos:  # Only show pins that have photos
                    pin_group = PinPhotoGroup(pin_id, pin_name, photos)
                    pin_group.photo_clicked.connect(self.photo_clicked.emit)
                    layout.addWidget(pin_group)


class PhotoDetailDialog(QDialog):
    """Dialog showing detailed view of a photo"""
    
    def __init__(self, photo_info, parent=None):
        super().__init__(parent)
        self.photo_info = photo_info
        self.setWindowTitle("Photo Details")
        self.setModal(True)
        self.resize(600, 500)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the photo detail dialog UI"""
        layout = QVBoxLayout(self)
        
        # Photo display
        photo_label = QLabel()
        photo_label.setAlignment(Qt.AlignCenter)
        photo_label.setStyleSheet("border: 1px solid #ccc; background: white;")
        photo_label.setMinimumSize(400, 300)
        
        photo_path = self.photo_info.get('path')
        if photo_path and os.path.exists(photo_path):
            pixmap = QPixmap(photo_path)
            if not pixmap.isNull():
                # Scale to fit dialog while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(500, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                photo_label.setPixmap(scaled_pixmap)
            else:
                photo_label.setText("Invalid Image")
        else:
            photo_label.setText("Image Not Found")
        
        layout.addWidget(photo_label)
        
        # Photo information
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.StyledPanel)
        info_layout = QVBoxLayout(info_frame)
        
        # File info
        filename = self.photo_info.get('filename', 'Unknown')
        date_uploaded = self.photo_info.get('date', 'Unknown')
        author = self.photo_info.get('author', 'Unknown')
        
        info_text = f"""
        <b>Filename:</b> {filename}<br>
        <b>Uploaded:</b> {date_uploaded}<br>
        <b>Author:</b> {author}<br>
        <b>Original Path:</b> {self.photo_info.get('original_path', 'N/A')}
        """
        
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_layout.addWidget(info_label)
        
        # Caption if available
        caption = self.photo_info.get('caption', '').strip()
        if caption:
            caption_label = QLabel("<b>Caption:</b>")
            info_layout.addWidget(caption_label)
            
            caption_text = QTextEdit()
            caption_text.setPlainText(caption)
            caption_text.setReadOnly(True)
            caption_text.setMaximumHeight(80)
            info_layout.addWidget(caption_text)
        
        layout.addWidget(info_frame)
        
        # Close button
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class PhotoGalleryWidget(QWidget):
    """Main photo gallery widget showing all photos organized by elevation and pin"""
    
    def __init__(self, project_name=None, parent=None):
        super().__init__(parent)
        self.project_name = project_name
        self.chat_manager = None
        
        if self.project_name:
            self.chat_manager = ChatDataManager(self.project_name)
        
        self.setup_ui()
        self.load_photos()
    
    def setup_ui(self):
        """Setup the main UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Photo Gallery")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #2980b9;
            }
        """)
        refresh_btn.clicked.connect(self.load_photos)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Filter options
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Filter by elevation:")
        filter_layout.addWidget(filter_label)
        
        self.elevation_filter = QComboBox()
        self.elevation_filter.addItem("All Elevations")
        self.elevation_filter.currentTextChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.elevation_filter)
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # Scroll area for photos
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; }")
        
        self.photos_container = QWidget()
        self.photos_layout = QVBoxLayout(self.photos_container)
        self.photos_layout.setSpacing(15)
        
        self.scroll_area.setWidget(self.photos_container)
        layout.addWidget(self.scroll_area)
        
        # Status bar
        self.status_label = QLabel("Loading photos...")
        self.status_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        layout.addWidget(self.status_label)
    
    def load_photos(self):
        """Load all photos from the project"""
        if not self.chat_manager:
            self.status_label.setText("No project selected")
            return
        
        self.status_label.setText("Loading photos...")
        
        # Clear existing content
        for i in reversed(range(self.photos_layout.count())):
            child = self.photos_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Clear elevation filter
        self.elevation_filter.clear()
        self.elevation_filter.addItem("All Elevations")
        
        try:
            # Get all chat files
            chat_data_dir = self.chat_manager.chat_data_dir
            if not os.path.exists(chat_data_dir):
                self.status_label.setText("No chat data found")
                return
            
            # Load pins.json to get pin information including elevation names
            pins_file = os.path.join(self.chat_manager.project_dir, 'pins.json')
            pins_data = {}
            if os.path.exists(pins_file):
                with open(pins_file, 'r', encoding='utf-8') as f:
                    pins_list = json.load(f)
                    # Convert to dict for easier lookup
                    pins_data = {pin.get('pin_id', 0): pin for pin in pins_list}
            
            # Organize photos by elevation and pin
            elevation_photos = {}
            total_photos = 0
            
            # Scan all chat files for photos
            for filename in os.listdir(chat_data_dir):
                if filename.endswith('_chat.json'):
                    try:
                        # Extract pin_id from filename
                        pin_id = int(filename.split('_')[1])
                        
                        # Load chat data
                        chat_messages = self.chat_manager.load_pin_chat(pin_id)
                        photos = [msg for msg in chat_messages if msg.get('type') == 'photo']
                        
                        if photos:
                            # Get pin information
                            pin_info = pins_data.get(pin_id, {})
                            elevation_name = pin_info.get('elevation_name') or pin_info.get('elevation', 'Unknown Elevation')
                            pin_name = pin_info.get('name', f'Pin {pin_id}')
                            
                            # Organize by elevation
                            if elevation_name not in elevation_photos:
                                elevation_photos[elevation_name] = {}
                            
                            elevation_photos[elevation_name][pin_id] = {
                                'pin_name': pin_name,
                                'photos': photos
                            }
                            total_photos += len(photos)
                    
                    except (ValueError, IndexError) as e:
                        print(f"[ERROR] Failed to parse chat file {filename}: {e}")
                        continue
            
            # Update elevation filter
            elevations = sorted(elevation_photos.keys())
            for elevation in elevations:
                self.elevation_filter.addItem(elevation)
            
            # Display photos by elevation
            if not elevation_photos:
                no_photos_label = QLabel("No photos found in this project")
                no_photos_label.setStyleSheet("""
                    color: #999; 
                    font-size: 16px; 
                    font-style: italic; 
                    padding: 50px;
                """)
                no_photos_label.setAlignment(Qt.AlignCenter)
                self.photos_layout.addWidget(no_photos_label)
                self.status_label.setText("No photos found")
            else:
                for elevation_name in sorted(elevation_photos.keys()):
                    elevation_section = ElevationPhotoSection(
                        elevation_name, 
                        elevation_photos[elevation_name]
                    )
                    elevation_section.photo_clicked.connect(self.show_photo_detail)
                    self.photos_layout.addWidget(elevation_section)
                
                self.status_label.setText(f"Loaded {total_photos} photos from {len(elevations)} elevations")
        
        except Exception as e:
            print(f"[ERROR] Failed to load photos: {e}")
            self.status_label.setText(f"Error loading photos: {str(e)}")
    
    def apply_filter(self, elevation_name):
        """Apply elevation filter to show only selected elevation"""
        if elevation_name == "All Elevations":
            # Show all elevation sections
            for i in range(self.photos_layout.count()):
                item = self.photos_layout.itemAt(i)
                if item and item.widget():
                    item.widget().setVisible(True)
        else:
            # Hide all sections except the selected one
            for i in range(self.photos_layout.count()):
                item = self.photos_layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    if isinstance(widget, ElevationPhotoSection):
                        widget.setVisible(widget.elevation_name == elevation_name)
                    else:
                        widget.setVisible(True)  # Show other widgets like "no photos" label
    
    def show_photo_detail(self, photo_info):
        """Show detailed view of a photo"""
        dialog = PhotoDetailDialog(photo_info, self)
        dialog.exec()
    
    def set_project(self, project_name):
        """Set the project and reload photos"""
        self.project_name = project_name
        if project_name:
            self.chat_manager = ChatDataManager(project_name)
            self.load_photos()
        else:
            self.chat_manager = None
            self.status_label.setText("No project selected")