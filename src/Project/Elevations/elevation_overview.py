from json import tool
from config.status import STATUS_COLORS
from Templates.template_loader import get_template_loader, load_default_template_if_needed
from PySide6.QtCore import Signal, QPointF, Qt, QPoint, QSize, QRect, QLineF
from PySide6.QtWidgets import (
    QDialog, QLineEdit, QTextEdit, QComboBox, QDialogButtonBox, QFormLayout,
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame, QSizePolicy,
    QMenu, QListWidget, QListWidgetItem, QFileDialog
)
from PySide6.QtGui import QPixmap, QImage, QPainter, QColor, QIcon, QAction, QPen
import fitz  # PyMuPDF
from Project.Elevations.finding_card import FindingCard
from Project.Elevations.findings_logic import add_pin_to_master_findings
from Project.master_findings import add_finding_from_pin
from Project.Elevations.chat_data_manager import ChatDataManager

from PySide6.QtCore import Signal

class ElevationOverviewWidget(QWidget):
    finding_added = Signal()  # Signal to notify when a finding is added
    back_to_project = Signal()  # Signal to notify when back button is pressed


    def __init__(self, pdf_path=None, findings=None, sidebar=None, parent=None, project_name=None, elevation_name=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.project_name = project_name  # Store project name for pin persistence
        self.elevation_name = elevation_name  # Store elevation name for proper pin filtering
        
        # Initialize chat data manager
        if self.project_name:
            self.chat_manager = ChatDataManager(self.project_name)
        else:
            self.chat_manager = None
        # --- Load pins from pins.json using findings_logic ---
        try:
            from Project.Elevations.findings_logic import load_pins
            all_pins = load_pins(self.project_name)
            # Filter pins to only show those for the current elevation
            import os
            # Use provided elevation_name if available, otherwise fall back to PDF basename
            current_elevation = self.elevation_name if self.elevation_name else (os.path.basename(self.pdf_path) if self.pdf_path else "Unknown Elevation")
            current_pdf_path = self.pdf_path
            print(f"[DEBUG] Current elevation: '{current_elevation}'")
            print(f"[DEBUG] PDF path: '{current_pdf_path}'")
            print(f"[DEBUG] All pins: {[(pin.get('name'), repr(pin.get('elevation'))) for pin in all_pins]}")
            
            # Enhanced filtering with better matching logic
            filtered_pins = []
            for pin in all_pins:
                pin_elevation = pin.get('elevation', '').strip()
                
                # Normalize names for comparison (remove extension, case insensitive, trim)
                def normalize_name(name):
                    if not name:
                        return ""
                    # Remove file extension, convert to lowercase, strip whitespace
                    name_clean = os.path.splitext(os.path.basename(name))[0].lower().strip()
                    return name_clean
                
                pin_elevation_normalized = normalize_name(pin_elevation)
                current_elevation_normalized = normalize_name(current_elevation)
                
                matches = False
                match_reason = ""
                
                # 1. Normalized name match (most robust)
                if pin_elevation_normalized == current_elevation_normalized and pin_elevation_normalized:
                    matches = True
                    match_reason = f"normalized match: '{pin_elevation_normalized}'"
                
                # 2. Exact elevation name match (case sensitive)
                elif pin_elevation == current_elevation:
                    matches = True
                    match_reason = f"exact match: '{pin_elevation}'"
                
                # 3. Full PDF path match (if pin stores full path)
                elif pin_elevation == current_pdf_path:
                    matches = True
                    match_reason = f"full path match: '{pin_elevation}'"
                
                # 4. Basename match
                elif os.path.basename(pin_elevation) == current_elevation:
                    matches = True
                    match_reason = f"basename match: '{os.path.basename(pin_elevation)}'"
                
                if matches:
                    filtered_pins.append(pin)
                    print(f"[DEBUG] Pin '{pin.get('name')}' MATCHES - {match_reason}")
                else:
                    print(f"[DEBUG] Pin '{pin.get('name')}' NO MATCH: pin='{pin_elevation}' ({pin_elevation_normalized}) vs current='{current_elevation}' ({current_elevation_normalized})")
            
            self.findings = filtered_pins  # Load findings from stored pins
            print(f"[DEBUG] Final filtered findings: {[pin.get('name') for pin in self.findings]}")
            
            # If no pins match elevation filtering, show all pins for debugging (in development)
            if len(filtered_pins) == 0 and len(all_pins) > 0:
                print(f"[DEBUG] No pins matched elevation filter, showing all {len(all_pins)} pins for debugging")
                self.findings = all_pins  # Show all pins for debugging
                
        except Exception as e:
            print(f"[ERROR] Failed to load pins: {e}")
            self.findings = []
        self.sidebar = sidebar  # SidebarNav instance, if provided

        # Top-level vertical layout: [Back Button | Main Horizontal Layout]
        top_layout = QVBoxLayout(self)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)

        # --- Back Button ---
        back_btn = QPushButton("← Back")
        back_btn.setStyleSheet("font-size: 15px; padding: 6px 16px; margin: 8px; border-radius: 6px; background: #e3e3e3; font-weight: bold;")
        back_btn.setFixedWidth(90)
        back_btn.clicked.connect(self.back_to_project)
        top_layout.addWidget(back_btn, alignment=Qt.AlignLeft)

        # Main horizontal layout: [AnnotationToolbar | PDF Viewer | Findings List]
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Annotation Toolbar ---
        self.toolbar = AnnotationToolbar()
        self.toolbar.tool_selected.connect(self.on_tool_selected)
        self.toolbar.zoom_in.connect(self.on_zoom_in)
        self.toolbar.zoom_out.connect(self.on_zoom_out)
        main_layout.addWidget(self.toolbar)

        # --- Center: PDF Viewer with pin/draw overlay ---
        self.pdf_viewer = PDFPinViewer(self.pdf_path, chat_manager=self.chat_manager)
        self.pdf_viewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.pdf_viewer.pin_created.connect(self.on_pin_created)
        self.pdf_viewer.pin_updated.connect(self.on_pin_updated)
        # Pass loaded pins to PDFPinViewer
        # Convert pin['pos'] dicts to QPointF for PDFPinViewer
        from PySide6.QtCore import QPointF
        def dict_to_qpointf(pos):
            if isinstance(pos, dict) and 'x' in pos and 'y' in pos:
                return QPointF(pos['x'], pos['y'])
            return pos
        # Filter out duplicate pins (same pos and elevation)
        unique_pins = []
        seen = set()
        for pin in self.findings:
            pos = pin.get('pos')
            elevation = pin.get('elevation')
            key = (round(pos.x(), 6) if hasattr(pos, 'x') else pos['x'], round(pos.y(), 6) if hasattr(pos, 'y') else pos['y'], elevation)
            if key not in seen:
                seen.add(key)
                pin_copy = pin.copy()
                pin_copy['pos'] = dict_to_qpointf(pin_copy['pos'])
                unique_pins.append(pin_copy)
        self.pdf_viewer.pins = unique_pins
        self.findings = unique_pins
        main_layout.addWidget(self.pdf_viewer, 10)

        # --- Right: Findings List Sidebar ---
        self.findings_sidebar = QFrame()
        self.findings_sidebar.setFixedWidth(260)
        self.findings_sidebar.setStyleSheet("background: #fafbfc; border-left: 1.5px solid #bbb;")
        findings_layout = QVBoxLayout(self.findings_sidebar)
        findings_layout.setContentsMargins(8, 8, 8, 8)
        findings_layout.setSpacing(8)

        header = QLabel("Findings List")
        header.setStyleSheet("font-weight: bold; font-size: 18px; margin-bottom: 8px;")
        findings_layout.addWidget(header)

        self.finding_cards = []
        self.findings_layout = findings_layout  # Save for later use
        
        # Add View Photos button
        self.photos_btn = QPushButton("📷 View Photos")
        self.photos_btn.setStyleSheet("background: #4CAF50; color: white; border-radius: 6px; padding: 8px; font-weight: bold; margin-bottom: 4px;")
        self.photos_btn.clicked.connect(self.show_elevation_photos)
        findings_layout.addWidget(self.photos_btn)
        
        self.add_btn = QPushButton("+ New Task")
        self.add_btn.setStyleSheet("background: #e3e3e3; border-radius: 6px; padding: 8px; font-weight: bold;")
        findings_layout.addStretch(1)
        findings_layout.addWidget(self.add_btn)
        main_layout.addWidget(self.findings_sidebar)

        self.refresh_findings_sidebar()

        # Add main_layout to top_layout
        top_layout.addLayout(main_layout)

        # Always connect finding_added to sidebar.refresh if sidebar is provided
        if self.sidebar is not None:
            self.finding_added.connect(self.sidebar.refresh)




    def reload_findings(self):
        """Reload findings from storage to ensure consistency."""
        try:
            from Project.Elevations.findings_logic import load_pins
            import os
            all_pins = load_pins(self.project_name)
            current_elevation = self.elevation_name if self.elevation_name else (os.path.basename(self.pdf_path) if self.pdf_path else "Unknown Elevation")
            
            # Apply the same filtering logic as in __init__
            filtered_pins = []
            for pin in all_pins:
                pin_elevation = pin.get('elevation', '').strip()
                
                # Normalize names for comparison (same logic as __init__)
                def normalize_name(name):
                    if not name:
                        return ""
                    name_clean = os.path.splitext(os.path.basename(name))[0].lower().strip()
                    return name_clean
                
                pin_elevation_normalized = normalize_name(pin_elevation)
                current_elevation_normalized = normalize_name(current_elevation)
                
                matches = False
                
                # Apply same matching criteria as __init__
                if pin_elevation_normalized == current_elevation_normalized and pin_elevation_normalized:
                    matches = True
                elif pin_elevation == current_elevation:
                    matches = True
                elif pin_elevation == self.pdf_path:
                    matches = True
                elif os.path.basename(pin_elevation) == current_elevation:
                    matches = True
                
                if matches:
                    filtered_pins.append(pin)
            
            self.findings = filtered_pins
            
            # If no pins match elevation filtering, show all pins for debugging (in development)
            if len(filtered_pins) == 0 and len(all_pins) > 0:
                print(f"[DEBUG] No pins matched elevation filter during reload, showing all {len(all_pins)} pins for debugging")
                self.findings = all_pins  # Show all pins for debugging
                
            self.refresh_findings_sidebar()
            print(f"[DEBUG] Reloaded {len(self.findings)} findings")
        except Exception as e:
            print(f"[ERROR] Failed to reload findings: {e}")

    def refresh_findings_sidebar(self):
        print("[DEBUG] refresh_findings_sidebar called. findings:", self.findings)
        # Remove all cards except header, stretch, and add_btn
        for i in reversed(range(1, self.findings_layout.count() - 2)):
            widget = self.findings_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.finding_cards.clear()
        print(f"[DEBUG] Number of findings: {len(self.findings)}")
        for finding in self.findings:
            print("[DEBUG] Adding FindingCard for:", finding)
            card = FindingCard(
                title=finding.get('name', 'Untitled Finding'),
                status=finding.get('status', None),
                material=finding.get('material', ''),
                defect=finding.get('defect', '')
            )
            card.mousePressEvent = self._make_finding_card_click_handler(finding)
            self.findings_layout.insertWidget(self.findings_layout.count() - 2, card)
            self.finding_cards.append(card)

    def _make_finding_card_click_handler(self, finding):
        def handler(event):
            # Only open dialog for editing existing finding, not for new pin creation
            dlg = PinTaskDialog(finding, new_pin=False, pdf_path=self.pdf_path, findings=self.findings, chat_manager=self.chat_manager)
            result = dlg.exec()
            if result == QDialog.Accepted:
                finding['chat'] = dlg.get_chat()
                finding['name'] = dlg.get_name()
                finding['status'] = dlg.get_status()
                self.refresh_findings_sidebar()
        return handler

    def on_tool_selected(self, tool):
        if tool.startswith('draw:'):
            shape = tool.split(':')[1]
            self.pdf_viewer.set_mode('draw', shape)
        else:
            self.pdf_viewer.set_mode(tool)

    def on_zoom_in(self):
        self.pdf_viewer.zoom(1.25)

    def on_zoom_out(self):
        self.pdf_viewer.zoom(0.8)

    def on_pin_created(self, pin):
        print("[DEBUG] on_pin_created called with:", pin)
        import os
        # Use provided elevation_name if available, otherwise fall back to PDF basename
        elevation_name = self.elevation_name if self.elevation_name else (os.path.basename(self.pdf_path) if self.pdf_path else "Unknown Elevation")
        print(f"[DEBUG] Using elevation_name: '{elevation_name}' for pin: '{pin.get('name', 'No name')}'")
        print(f"[DEBUG] Project name: '{self.project_name}'")
        
        # Ensure pin has elevation field set before saving
        pin['elevation'] = elevation_name
        
        # Add pin to master findings and storage
        add_pin_to_master_findings(pin, elevation_name=elevation_name, project_name=self.project_name)
        
        # Reload findings from storage to ensure consistency
        self.reload_findings()
        self.finding_added.emit()
        self.select_tool('mouse')

    def on_pin_updated(self, pin):
        # Update pin in master findings and storage
        import os
        elevation_name = self.elevation_name if self.elevation_name else (os.path.basename(self.pdf_path) if self.pdf_path else "Unknown Elevation")
        add_pin_to_master_findings(pin, elevation_name=elevation_name, project_name=self.project_name)
        
        # Reload findings from storage to ensure consistency
        self.reload_findings()

        # --- Right: Findings List Sidebar ---
        self.findings_sidebar = QFrame()
        self.findings_sidebar.setFixedWidth(260)
        self.findings_sidebar.setStyleSheet("background: #fafbfc; border-left: 1.5px solid #bbb;")
        findings_layout = QVBoxLayout(self.findings_sidebar)
        findings_layout.setContentsMargins(8, 8, 8, 8)
        findings_layout.setSpacing(8)

        header = QLabel("Findings List")
        header.setStyleSheet("font-weight: bold; font-size: 18px; margin-bottom: 8px;")
        findings_layout.addWidget(header)

        self.finding_cards = []
        for finding in self.findings:
            card = QFrame()
            card.setStyleSheet("background: #fff; border: 1px solid #ddd; border-radius: 6px; padding: 8px;")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(8, 8, 8, 8)
            card_layout.addWidget(QLabel(finding.get('title', 'Untitled Finding')))
            findings_layout.addWidget(card)
            self.finding_cards.append(card)

        findings_layout.addStretch(1)
        add_btn = QPushButton("+ New Task")
        add_btn.setStyleSheet("background: #e3e3e3; border-radius: 6px; padding: 8px; font-weight: bold;")
        findings_layout.addWidget(add_btn)



        # Set default tool to mouse
        self.pdf_viewer.set_mode('mouse')
        self.toolbar.mouse_btn.setChecked(True)

    # Sidebar toggle removed: sidebar always hidden


    # Legacy on_pin_updated removed (model is now self.findings)


    def select_tool(self, tool):
        # Only one button should be checked at a time
        self.toolbar.mouse_btn.setChecked(tool == 'mouse')
        self.toolbar.pin_btn.setChecked(tool == 'pin')
        self.toolbar.draw_btn.setChecked(tool == 'draw')
        self.toolbar.pan_btn.setChecked(tool == 'pan')
        self.pdf_viewer.set_mode(tool)
        self.toolbar.tool_selected.emit(tool)
    
    def show_elevation_photos(self):
        """Show photo gallery filtered for this elevation"""
        from Project.Photos.Photo_finding import PhotoGalleryWidget
        from PySide6.QtWidgets import QDialog, QVBoxLayout
        
        # Create a dialog to show the photo gallery
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Photos - {self.elevation_name or 'Current Elevation'}")
        dialog.setModal(True)
        dialog.resize(900, 600)
        
        layout = QVBoxLayout(dialog)
        
        # Create photo gallery widget
        photo_gallery = PhotoGalleryWidget(project_name=self.project_name)
        layout.addWidget(photo_gallery)
        
        # Filter to show only this elevation's photos
        if self.elevation_name:
            # Wait for photos to load, then apply filter
            def apply_elevation_filter():
                for i in range(photo_gallery.elevation_filter.count()):
                    if photo_gallery.elevation_filter.itemText(i) == self.elevation_name:
                        photo_gallery.elevation_filter.setCurrentIndex(i)
                        break
            
            # Apply filter after a short delay to ensure photos are loaded
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, apply_elevation_filter)
        
        dialog.exec()

class PDFPinViewer(QLabel):
    from PySide6.QtCore import Signal
    pin_created = Signal(dict)  # Emitted when a new pin is created
    pin_updated = Signal(dict)  # Emitted when a pin is updated
    def __init__(self, pdf_path=None, parent=None, chat_manager=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background: #eee; border: 1px solid #bbb; font-size: 18px;")
        self.pdf_path = pdf_path
        self.chat_manager = chat_manager
        self.pins = []
        self.shapes = []  # List of dicts: {type, start, end}
        self.current_shape = None
        self.mode = 'pin'  # or 'draw' or 'pan' or 'move'
        self.draw_shape = 'line'  # 'line', 'circle', 'square'
        self.base_pixmap = None
        self.scale = 1.0
        self.offset = QPoint(0, 0)  # Pan offset in pixels
        self.last_pan_point = None
        self.hovered_pin_index = None
        self.hovered_shape_index = None  # Track hovered shape
        self.moving_object = None  # {'type': 'pin'/'shape', 'index': int, 'offset': QPoint}
        self.placing_pin = False
        self.temp_pin = None
        self.display_pdf()

    def set_mode(self, mode, shape=None):
        self.mode = mode
        if mode == 'draw' and shape:
            self.draw_shape = shape
        if mode == 'draw':
            self.setCursor(Qt.CrossCursor)
        elif mode == 'pan':
            self.setCursor(Qt.OpenHandCursor)
        elif mode == 'move':
            self.setCursor(Qt.SizeAllCursor)
        elif mode == 'mouse':
            self.setCursor(Qt.ArrowCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def zoom(self, factor):
        self.scale *= factor
        self.update()

    def display_pdf(self):
        if self.pdf_path and self.pdf_path.lower().endswith('.pdf'):
            try:
                doc = fitz.open(self.pdf_path)
                if doc.page_count > 0:
                    page = doc.load_page(0)
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGBA8888 if pix.alpha else QImage.Format_RGB888)
                    self.base_pixmap = QPixmap.fromImage(image)
                    self.update()
                else:
                    self.setText("PDF (empty)")
            except Exception as e:
                self.setText("PDF error: " + str(e))
        elif self.pdf_path:
            self.setText("Not a PDF file: " + str(self.pdf_path))
        else:
            self.setText("No PDF selected.")

    def mousePressEvent(self, event):
        if not self.base_pixmap:
            return
        label_size = self.size()
        pixmap_size = self.scaled_pixmap_size()
        x_offset = (label_size.width() - pixmap_size.width()) // 2 + self.offset.x()
        y_offset = (label_size.height() - pixmap_size.height()) // 2 + self.offset.y()
        x = (event.x() - x_offset) / self.scale
        y = (event.y() - y_offset) / self.scale
        rel_x = x / self.base_pixmap.width() if self.base_pixmap else 0
        rel_y = y / self.base_pixmap.height() if self.base_pixmap else 0
        click_point = QPointF(rel_x, rel_y)
        if self.mode == 'mouse':
            for pin in self.pins:
                px = pin['pos'].x() * self.base_pixmap.width()
                py = pin['pos'].y() * self.base_pixmap.height()
                if (QPointF(px, py) - QPointF(x, y)).manhattanLength() < 18:
                    self.open_pin_dialog(pin, new_pin=False)
                    return
            return
        if self.mode == 'pin' and event.button() == Qt.LeftButton:
            for pin in self.pins:
                px = pin['pos'].x() * self.base_pixmap.width()
                py = pin['pos'].y() * self.base_pixmap.height()
                if (QPointF(px, py) - QPointF(x, y)).manhattanLength() < 18:
                    self.open_pin_dialog(pin, new_pin=False)
                    return
            if self.point_in_pixmap(event.pos()):
                # Start drag-to-place for new pin
                self.placing_pin = True
                self.temp_pin = {"pos": click_point, "chat": []}
                self.pins.append(self.temp_pin)
                self.update()
        elif self.mode == 'draw' and event.button() == Qt.LeftButton:
            if self.point_in_pixmap(event.pos()):
                self.current_shape = {
                    'type': self.draw_shape,
                    'start': QPoint(int(x), int(y)),
                    'end': QPoint(int(x), int(y))
                }
        elif self.mode == 'move' and event.button() == Qt.LeftButton:
            for i, pin in enumerate(self.pins):
                px = pin['pos'].x() * self.base_pixmap.width()
                py = pin['pos'].y() * self.base_pixmap.height()
                if (QPointF(px, py) - QPointF(x, y)).manhattanLength() < 18:
                    self.moving_object = {'type': 'pin', 'index': i, 'offset': QPoint(int(x - px), int(y - py))}
                    return
            for i in reversed(range(len(self.shapes))):
                shape = self.shapes[i]
                if self._point_in_shape(QPoint(int(x), int(y)), shape):
                    s = shape['start']
                    e = shape['end']
                    offset = QPoint(int(x - s.x()), int(y - s.y()))
                    self.moving_object = {'type': 'shape', 'index': i, 'offset': offset, 'drag_start': QPoint(int(x), int(y)), 'orig_start': s, 'orig_end': e}
                    return
        elif self.mode == 'pan' and event.button() == Qt.LeftButton:
            self.setCursor(Qt.ClosedHandCursor)
            self.last_pan_point = event.pos()

    def open_pin_dialog(self, pin, new_pin=False):
        print(f"[DEBUG] open_pin_dialog called, new_pin={new_pin}")
        dlg = PinTaskDialog(pin, new_pin=new_pin, pdf_path=self.pdf_path, chat_manager=self.chat_manager)
        result = dlg.exec()
        print(f"[DEBUG] PinTaskDialog exec result: {result}")
        if result == QDialog.Accepted:
            pin['chat'] = dlg.get_chat()
            pin['name'] = dlg.get_name()
            pin['status'] = dlg.get_status()
            pin['material'] = dlg.get_material()
            pin['defect'] = dlg.get_defect()
            self.pin_updated.emit(pin)
            self.update()
            return True
        return False

    def mouseMoveEvent(self, event):
        label_size = self.size()
        pixmap_size = self.scaled_pixmap_size()
        x_offset = (label_size.width() - pixmap_size.width()) // 2 + self.offset.x()
        y_offset = (label_size.height() - pixmap_size.height()) // 2 + self.offset.y()
        x = (event.x() - x_offset) / self.scale
        y = (event.y() - y_offset) / self.scale
        hover_point = QPoint(int(x), int(y))
        prev_hover = self.hovered_pin_index
        prev_shape_hover = self.hovered_shape_index
        self.hovered_pin_index = None
        self.hovered_shape_index = None
        # Pin hover
        for i, pin in enumerate(self.pins):
            px = pin['pos'].x() * self.base_pixmap.width()
            py = pin['pos'].y() * self.base_pixmap.height()
            if (QPointF(px, py) - QPointF(x, y)).manhattanLength() < 18:
                self.hovered_pin_index = i
                break
        # Shape hover (check last to first for topmost)
        for i in reversed(range(len(self.shapes))):
            shape = self.shapes[i]
            if self._point_in_shape(QPoint(int(x), int(y)), shape):
                self.hovered_shape_index = i
                break
        if prev_hover != self.hovered_pin_index or prev_shape_hover != self.hovered_shape_index:
            self.update()

        if self.mode == 'mouse':
            return
        if self.mode == 'draw' and self.current_shape:
            if self.point_in_pixmap(event.pos()):
                self.current_shape['end'] = QPoint(int(x), int(y))
                self.update()
        elif self.mode == 'move' and self.moving_object:
            if self.moving_object['type'] == 'pin':
                idx = self.moving_object['index']
                rel_x = x / self.base_pixmap.width()
                rel_y = y / self.base_pixmap.height()
                self.pins[idx]['pos'] = QPointF(rel_x, rel_y)
                self.update()
                parent = self.parent()
                while parent is not None and not hasattr(parent, 'findings'):
                    parent = parent.parent() if hasattr(parent, 'parent') else None
                if parent is not None:
                    for info in parent.findings:
                        if info['pos'] == self.pins[idx]['pos']:
                            break
                        if abs(info['pos'].x() - rel_x) < 1e-6 and abs(info['pos'].y() - rel_y) < 1e-6:
                            info['pos'] = self.pins[idx]['pos']
                            break
                    parent.refresh_findings_sidebar()
                    if hasattr(parent, 'sidebar') and parent.sidebar is not None:
                        parent.finding_added.emit()
            elif self.moving_object['type'] == 'shape':
                idx = self.moving_object['index']
                drag_start = self.moving_object['drag_start']
                orig_start = self.moving_object['orig_start']
                orig_end = self.moving_object['orig_end']
                dx = int(x) - drag_start.x()
                dy = int(y) - drag_start.y()
                self.shapes[idx]['start'] = orig_start + QPoint(dx, dy)
                self.shapes[idx]['end'] = orig_end + QPoint(dx, dy)
                self.update()
        elif self.mode == 'pin' and self.placing_pin and self.temp_pin is not None:
            if self.point_in_pixmap(event.pos()):
                rel_x = x / self.base_pixmap.width()
                rel_y = y / self.base_pixmap.height()
                self.temp_pin['pos'] = QPointF(rel_x, rel_y)
                self.update()
        elif self.mode == 'pan' and self.last_pan_point:
            delta = event.pos() - self.last_pan_point
            self.offset += delta
            self.last_pan_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if self.mode == 'mouse':
            return
        if self.mode == 'draw' and self.current_shape:
            self.shapes.append(self.current_shape)
            self.current_shape = None
            self.update()
        elif self.mode == 'move' and self.moving_object:
            self.moving_object = None
            self.update()
        elif self.mode == 'pin' and self.placing_pin and self.temp_pin is not None:
            # Finish placing pin and open dialog
            self.placing_pin = False
            pin = self.temp_pin
            self.temp_pin = None
            self.update()
            result = self.open_pin_dialog(pin, new_pin=True)
            if not result:
                # If dialog cancelled, remove the pin
                if pin in self.pins:
                    self.pins.remove(pin)
                self.update()
            else:
                self.pin_created.emit(pin)
        elif self.mode == 'pan' and event.button() == Qt.LeftButton:
            self.setCursor(Qt.OpenHandCursor)
            self.last_pan_point = None

    def point_in_pixmap(self, pos):
        label_size = self.size()
        pixmap_size = self.scaled_pixmap_size()
        x_offset = (label_size.width() - pixmap_size.width()) // 2 + self.offset.x()
        y_offset = (label_size.height() - pixmap_size.height()) // 2 + self.offset.y()
        x = pos.x() - x_offset
        y = pos.y() - y_offset
        return 0 <= x < pixmap_size.width() and 0 <= y < pixmap_size.height()

    def scaled_pixmap_size(self):
        if not self.base_pixmap:
            return QSize(0, 0)
        return self.base_pixmap.size() * self.scale

    def _point_in_shape(self, pt, shape):
        s = shape['start']
        e = shape['end']
        if shape['type'] == 'line':
            # Manual distance from pt to line segment (s, e)
            # Convert to float for precision
            x0, y0 = pt.x(), pt.y()
            x1, y1 = s.x(), s.y()
            x2, y2 = e.x(), e.y()
            dx = x2 - x1
            dy = y2 - y1
            if dx == 0 and dy == 0:
                # Start and end are the same point
                dist = ((x0 - x1) ** 2 + (y0 - y1) ** 2) ** 0.5
            else:
                t = max(0, min(1, ((x0 - x1) * dx + (y0 - y1) * dy) / (dx * dx + dy * dy)))
                proj_x = x1 + t * dx
                proj_y = y1 + t * dy
                dist = ((x0 - proj_x) ** 2 + (y0 - proj_y) ** 2) ** 0.5
            if dist < 10:
                return True
        elif shape['type'] in ('square', 'circle'):
            rect = QRect(s, e).normalized()
            if rect.contains(pt):
                return True
        return False

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.base_pixmap:
            from config.status import STATUS_COLORS
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            pixmap_size = self.scaled_pixmap_size()
            label_size = self.size()
            x_offset = (label_size.width() - pixmap_size.width()) // 2 + self.offset.x()
            y_offset = (label_size.height() - pixmap_size.height()) // 2 + self.offset.y()
            # Draw scaled PDF
            scaled_pixmap = self.base_pixmap.scaled(pixmap_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter.drawPixmap(x_offset, y_offset, scaled_pixmap)
            # Draw shapes
            for i, shape in enumerate(self.shapes):
                highlight = (i == self.hovered_shape_index)
                self._draw_shape(painter, shape, x_offset, y_offset, highlight)
            if self.current_shape:
                self._draw_shape(painter, self.current_shape, x_offset, y_offset, False)
            # Draw pins
            for i, pin in enumerate(self.pins):
                px = pin['pos'].x() * pixmap_size.width()
                py = pin['pos'].y() * pixmap_size.height()
                pin_x = int(px) + x_offset
                pin_y = int(py) + y_offset
                status = pin.get('status', None)
                color = STATUS_COLORS.get(status, '#FF4500')  # fallback to orange-red
                if i == self.hovered_pin_index:
                    painter.setBrush(QColor(color).lighter(130))
                    painter.setPen(QPen(QColor(30, 30, 30), 4))  # dark border
                else:
                    painter.setBrush(QColor(color))
                    painter.setPen(QPen(QColor(color)))
                painter.drawEllipse(QPoint(pin_x, pin_y), 10, 10)

    def _draw_shape(self, painter, shape, x_offset, y_offset, highlight=False):
        pen = QPen(QColor(0, 0, 255), 2)
        if highlight:
            pen = QPen(QColor(30, 30, 30), 4)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        s = shape['start']
        e = shape['end']
        if shape['type'] == 'line':
            painter.drawLine(s + QPoint(x_offset, y_offset), e + QPoint(x_offset, y_offset))
        elif shape['type'] == 'square':
            rect = QRect(s + QPoint(x_offset, y_offset), e + QPoint(x_offset, y_offset))
            painter.drawRect(rect.normalized())
        elif shape['type'] == 'circle':
            rect = QRect(s + QPoint(x_offset, y_offset), e + QPoint(x_offset, y_offset))
            painter.drawEllipse(rect.normalized())

# --- Pin Task Dialog with Chat ---

class PinTaskDialog(QDialog):
    def __init__(self, pin=None, new_pin=False, pdf_path=None, findings=None, parent=None, chat_manager=None):
        print(f"[DEBUG] PinTaskDialog __init__ called, pin: {pin}, new_pin: {new_pin}")
        super().__init__(parent)
        self.setWindowTitle("Pin Details")
        self.pin = pin or {}
        self.new_pin = new_pin
        self.pdf_path = pdf_path
        self.findings = findings or []
        self.chat_manager = chat_manager

        # Load existing chat data if available
        pin_id = self.pin.get('pin_id')
        if pin_id and self.chat_manager:
            self.existing_chat = self.chat_manager.load_pin_chat(pin_id)
        else:
            # Fallback to old chat format in pin data
            self.existing_chat = self.pin.get('chat', [])

        # For new pins, generate a temporary pin_id immediately so photos can be attached
        if self.new_pin and not pin_id and self.chat_manager:
            # Get next available pin_id using the same logic as findings_logic
            import os
            import json
            pins_file = os.path.join(self.chat_manager.project_dir, 'pins.json')
            if os.path.exists(pins_file):
                try:
                    with open(pins_file, 'r', encoding='utf-8') as f:
                        existing_pins = json.load(f)
                    next_id = max([p.get('pin_id', 0) for p in existing_pins], default=100) + 1
                except:
                    next_id = 101  # First pin if file corrupted
            else:
                next_id = 101  # First pin
            
            # Use the standard next ID - concurrent dialogs are rare in single-user application
            
            self.pin['pin_id'] = next_id
            pin_id = next_id
            print(f"[DEBUG] Assigned temporary pin_id {pin_id} to new pin")
        
        if pin_id and self.chat_manager:
            self.existing_chat = self.chat_manager.load_pin_chat(pin_id)
        else:
            # Fallback to old chat format in pin data
            self.existing_chat = self.pin.get('chat', [])

        self.resize(600, 500)  # Make the popup larger (width, height)
        main_layout = QVBoxLayout(self)
        # --- Title at top ---
        self.name_edit = QLineEdit(self.pin.get('name', ''))
        self.name_edit.setPlaceholderText("Enter pin title/name")
        self.name_edit.setStyleSheet("font-size: 18px; font-weight: bold; padding: 6px;")
        main_layout.addWidget(self.name_edit)

        # --- Main content: 2 columns ---
        content_layout = QHBoxLayout()
        # Left: Chat log with input and send button
        chat_layout = QVBoxLayout()
        chat_label = QLabel("Chat / Comments:")
        chat_label.setStyleSheet("font-weight: bold;")
        chat_layout.addWidget(chat_label)
        from Project.Elevations.chat_item_widget import ChatItemWidget
        self.chat_log = QListWidget()
        self.chat_log.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Load chat messages from chat manager or fallback to pin data
        from datetime import datetime
        for msg in self.existing_chat:
            if isinstance(msg, dict) and msg.get('type') == 'photo':
                # Convert date string to datetime object
                date_obj = None
                date_str = msg.get('date')
                if date_str:
                    try:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        try:
                            # Try ISO format as fallback
                            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        except:
                            date_obj = None
                widget = ChatItemWidget(image_path=msg['path'], date=date_obj)
                item = QListWidgetItem()
                item.setSizeHint(widget.sizeHint())
                self.chat_log.addItem(item)
                self.chat_log.setItemWidget(item, widget)
            else:
                # Assume text message
                date_obj = None
                if isinstance(msg, dict) and 'date' in msg:
                    date_str = msg.get('date')
                    if date_str:
                        try:
                            date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            try:
                                # Try ISO format as fallback
                                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            except:
                                date_obj = None
                text = msg.get('text') if isinstance(msg, dict) and 'text' in msg else str(msg)
                widget = ChatItemWidget(text=text, date=date_obj)
                item = QListWidgetItem()
                item.setSizeHint(widget.sizeHint())
                self.chat_log.addItem(item)
                self.chat_log.setItemWidget(item, widget)
        chat_layout.addWidget(self.chat_log, 2)
        chat_input_row = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Enter message here...")
        chat_input_row.addWidget(self.chat_input, 1)
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.add_chat_message)
        chat_input_row.addWidget(self.send_btn)
        self.attach_btn = QPushButton("📎 Attach Photo")
        self.attach_btn.clicked.connect(self.attach_photo)

        chat_input_row.addWidget(self.attach_btn)
        chat_layout.addLayout(chat_input_row)
        content_layout.addLayout(chat_layout, 2)

        # Right: Attributes and mini-map
        attr_layout = QVBoxLayout()
        # Status dropdown
        status_label = QLabel("Status:")
        attr_layout.addWidget(status_label)
        from PySide6.QtGui import QColor
        self.status_combo = QComboBox()
        
        # Load template if available
        template_loader = get_template_loader()
        if not template_loader.current_template:
            load_default_template_if_needed()
        
        # Get status options from template
        status_options = template_loader.get_status_options_for_pin_dialog()
        if not status_options:
            # Fallback to master list, then hardcoded options
            master_data = template_loader.load_master_list()
            status_options = list(master_data.get('statuses', {}).keys())
            if not status_options:
                status_options = [
                    "Unsafe",
                    "Pre-con", 
                    "Require Repair",
                    "Completed Before Last Week",
                    "For Verification",
                    "Completed Last Week",
                    "Verified"
                ]
        
        self.status_combo.addItem("")
        for status in status_options:
            # Create a colored circle icon
            # Try template colors first, then master list, then fallback to STATUS_COLORS
            template_colors = template_loader.get_status_colors_dict()
            color = template_colors.get(status)
            if not color:
                master_colors = template_loader.get_master_list_statuses()
                color = master_colors.get(status) or STATUS_COLORS.get(status, "#cccccc")
            pixmap = QPixmap(16, 16)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QColor(color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(2, 2, 12, 12)
            painter.end()
            self.status_combo.addItem(QIcon(pixmap), status)
        if self.pin.get('status'):
            idx = self.status_combo.findText(self.pin.get('status'))
            if idx >= 0:
                self.status_combo.setCurrentIndex(idx)
        attr_layout.addWidget(self.status_combo)
        # --- Material/Defect dropdowns ---
        material_label = QLabel("Material:")
        attr_layout.addWidget(material_label)
        self.material_combo = QComboBox()
        self.material_combo.addItem("")
        
        # Get category options from template
        template_category_options = template_loader.get_category_options_for_pin_dialog()
        if not template_category_options:
            # Fallback to master list, then config file
            template_category_options = template_loader.get_master_list_categories()
            if not template_category_options:
                try:
                    from config.categories import CATEGORY_OPTIONS
                    template_category_options = CATEGORY_OPTIONS
                except ImportError:
                    template_category_options = {}
        
        self.CATEGORY_OPTIONS = template_category_options
        for material in template_category_options.keys():
            self.material_combo.addItem(material)
        if self.pin.get('material'):
            idx = self.material_combo.findText(self.pin['material'])
            if idx >= 0:
                self.material_combo.setCurrentIndex(idx)
        self.material_combo.currentTextChanged.connect(self.on_material_changed)
        attr_layout.addWidget(self.material_combo)

        defect_label = QLabel("Defect:")
        attr_layout.addWidget(defect_label)
        self.defect_combo = QComboBox()
        self.defect_combo.addItem("")
        if self.pin.get('material'):
            defects = template_category_options.get(self.pin['material'], [])
            self.defect_combo.addItems(defects)
            if self.pin.get('defect'):
                idx = self.defect_combo.findText(self.pin['defect'])
                if idx >= 0:
                    self.defect_combo.setCurrentIndex(idx)
        attr_layout.addWidget(self.defect_combo)

        # Mini-map and finish layout
        mini_label = QLabel("Mini Map:")
        attr_layout.addWidget(mini_label)
        self.mini_map = QLabel()
        self.mini_map.setFixedSize(160, 120)
        self.mini_map.setStyleSheet("border: 1px solid #bbb; background: #fff;")
        self.update_mini_map()
        attr_layout.addWidget(self.mini_map)
        attr_layout.addStretch(1)
        content_layout.addLayout(attr_layout, 1)
        main_layout.addLayout(content_layout, 1)

        # Photo gallery button (only if pin has ID and photos exist)
        pin_id = self.pin.get('pin_id')
        if pin_id and self.chat_manager:
            pin_photos = [msg for msg in self.existing_chat if msg.get('type') == 'photo']
            if pin_photos:
                photos_btn = QPushButton(f"📷 View Pin Photos ({len(pin_photos)})")
                photos_btn.setStyleSheet("background: #4CAF50; color: white; border-radius: 4px; padding: 8px; font-weight: bold; margin: 4px;")
                photos_btn.clicked.connect(self.show_pin_photos)
                main_layout.addWidget(photos_btn)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

    def validate_and_accept(self):
        from PySide6.QtWidgets import QMessageBox
        name = self.get_name().strip()
        status = self.get_status().strip()
        material = self.get_material().strip()
        defect = self.get_defect().strip()
        missing = []
        if not name:
            missing.append("Title/Name")
        if not status:
            missing.append("Status")
        if not material:
            missing.append("Material")
        if not defect:
            missing.append("Defect")
        if missing:
            QMessageBox.warning(self, "Missing Required Fields", f"Please fill in: {', '.join(missing)}")
            return
        self.accept()

    def on_material_changed(self, material):
        self.defect_combo.clear()
        self.defect_combo.addItem("")
        defects = self.CATEGORY_OPTIONS.get(material, [])
        self.defect_combo.addItems(defects)

    def attach_photo(self):
        from PySide6.QtWidgets import QFileDialog, QListWidgetItem, QMessageBox
        from Project.Elevations.chat_item_widget import ChatItemWidget
        import datetime
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Photo", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if file_path:
            pin_id = self.pin.get('pin_id')
            print(f"[DEBUG] attach_photo: pin_id={pin_id}, chat_manager={self.chat_manager is not None}")
            
            # Save photo using chat manager if available
            if pin_id and self.chat_manager:
                saved_path = self.chat_manager.add_photo_message(pin_id, file_path)
                if saved_path:
                    # Use the saved path for the widget
                    widget = ChatItemWidget(image_path=saved_path, date=datetime.datetime.now())
                    item = QListWidgetItem()
                    item.setSizeHint(widget.sizeHint())
                    self.chat_log.addItem(item)
                    self.chat_log.setItemWidget(item, widget)
                    
                    # Update existing_chat to reflect the new photo
                    self.existing_chat = self.chat_manager.load_pin_chat(pin_id)
                    print(f"[DEBUG] Photo attached successfully to pin {pin_id}")
                else:
                    QMessageBox.warning(self, "Photo Error", "Failed to save photo. Please try again.")
            else:
                # This should not happen for new pins anymore since they get pin_id
                QMessageBox.warning(self, "Photo Error", "Cannot attach photo: Pin ID not available. Please save the pin first.")
                print(f"[ERROR] attach_photo failed: pin_id={pin_id}, chat_manager available={self.chat_manager is not None}")

    def update_mini_map(self):
        # Show a small version of the PDF with a pin icon at the correct location
        if not self.pdf_path or not self.pin or 'pos' not in self.pin:
            self.mini_map.clear()
            return
        try:
            doc = fitz.open(self.pdf_path)
            if doc.page_count > 0:
                page = doc.load_page(0)
                page_rect = page.rect
                page_width = float(page_rect.width)
                page_height = float(page_rect.height)
                target_w, target_h = self.mini_map.width(), self.mini_map.height()
                scale_x = target_w / page_width
                scale_y = target_h / page_height
                scale = min(scale_x, scale_y)
                pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
                self._mini_map_image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGBA8888 if pix.alpha else QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(self._mini_map_image)
                # Calculate pin position in PDF points, then scale to minimap
                # If pin['pos'] is in main pixmap pixel space, convert to PDF points
                # Assume pin['pos'] is in PDF pixel space (from main PDF rendering)
                rel_x = self.pin['pos'].x()
                rel_y = self.pin['pos'].y()
                pin_x_pdf = rel_x * page_width
                pin_y_pdf = rel_y * page_height
                pin_x = int(pin_x_pdf * scale)
                pin_y = int(pin_y_pdf * scale)
                print(f"[DEBUG] update_mini_map: rel=({rel_x}, {rel_y}), page=({page_width}, {page_height}), scale={scale}, pin_x_pdf={pin_x_pdf}, pin_y_pdf={pin_y_pdf}, pin_x={pin_x}, pin_y={pin_y}")
                # Draw pin icon overlay
                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                shadow_color = QColor(0, 0, 0, 60)
                painter.setBrush(shadow_color)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPoint(pin_x+2, pin_y+8), 8, 4)
                painter.setBrush(QColor(255, 69, 0))
                painter.setPen(QColor(255, 69, 0))
                painter.drawEllipse(QPoint(pin_x, pin_y), 8, 8)
                painter.setPen(QColor(255,255,255))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(QPoint(pin_x, pin_y), 8, 8)
                painter.end()
                # Center the pixmap in the minimap QLabel
                final_pixmap = QPixmap(target_w, target_h)
                final_pixmap.fill(Qt.white)
                painter = QPainter(final_pixmap)
                x_offset = (target_w - pixmap.width()) // 2
                y_offset = (target_h - pixmap.height()) // 2
                painter.drawPixmap(x_offset, y_offset, pixmap)
                painter.end()
                self.mini_map.setPixmap(final_pixmap)
            else:
                self.mini_map.clear()
        except Exception as e:
            print(f"[DEBUG] update_mini_map: Exception {e}")
            self.mini_map.clear()

    def get_name(self):
        return self.name_edit.text()

    def get_status(self):
        return self.status_combo.currentText()

    def get_material(self):
        return self.material_combo.currentText()

    def get_defect(self):
        return self.defect_combo.currentText()

    def get_chat(self):
        # Return chat messages - now handled by chat manager, so return existing chat
        pin_id = self.pin.get('pin_id')
        if pin_id and self.chat_manager:
            return self.chat_manager.load_pin_chat(pin_id)
        else:
            # Fallback to existing chat in pin data
            return self.pin.get('chat', [])

    def add_chat_message(self):
        from Project.Elevations.chat_item_widget import ChatItemWidget
        import datetime
        msg = self.chat_input.text().strip()
        if msg:
            # Add to UI
            widget = ChatItemWidget(text=msg, date=datetime.datetime.now())
            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())
            self.chat_log.addItem(item)
            self.chat_log.setItemWidget(item, widget)
            self.chat_input.clear()
            
            # Save to chat manager if available
            pin_id = self.pin.get('pin_id')
            if pin_id and self.chat_manager:
                self.chat_manager.add_text_message(pin_id, msg)

    def show_pin_photos(self):
        """Show photo gallery focused on this specific pin"""
        from Project.Photos.Photo_finding import PhotoDetailDialog
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QWidget
        
        pin_id = self.pin.get('pin_id')
        if not pin_id or not self.chat_manager:
            return
        
        # Get pin photos
        pin_photos = [msg for msg in self.existing_chat if msg.get('type') == 'photo']
        if not pin_photos:
            return
        
        # Create dialog to show pin photos
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Photos - Pin {pin_id}: {self.pin.get('name', 'Unnamed Pin')}")
        dialog.setModal(True)
        dialog.resize(800, 600)
        
        layout = QVBoxLayout(dialog)
        
        # Header
        header_label = QLabel(f"Pin {pin_id} Photos ({len(pin_photos)} photos)")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(header_label)
        
        # Scroll area for photos
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        photos_widget = QWidget()
        photos_layout = QVBoxLayout(photos_widget)
        
        # Add photo thumbnails
        from Project.Photos.Photo_finding import PhotoThumbnail
        photos_per_row = 4
        row_layout = None
        
        for i, photo in enumerate(pin_photos):
            if i % photos_per_row == 0:
                row_layout = QHBoxLayout()
                photos_layout.addLayout(row_layout)
            
            thumbnail = PhotoThumbnail(photo)
            thumbnail.photo_clicked.connect(lambda photo_info: PhotoDetailDialog(photo_info, dialog).exec())
            row_layout.addWidget(thumbnail)
        
        # Fill remaining spaces in last row
        if row_layout and len(pin_photos) % photos_per_row != 0:
            remaining = photos_per_row - (len(pin_photos) % photos_per_row)
            for _ in range(remaining):
                row_layout.addStretch()
        
        scroll_area.setWidget(photos_widget)
        layout.addWidget(scroll_area)
        
        dialog.exec()

    def wheelEvent(self, event):
        # Zoom in/out with Ctrl+scroll or just scroll wheel
        if hasattr(event, 'angleDelta'):
            delta = event.angleDelta().y()
        else:
            delta = event.delta()
        if event.modifiers() & Qt.ControlModifier or True:  # Always zoom on scroll
            if delta > 0:
                self.zoom(1.15)
            elif delta < 0:
                self.zoom(0.87)
            event.accept()
        else:
            super().wheelEvent(event)

# --- Annotation Toolbar Widget ---
class AnnotationToolbar(QWidget):
    tool_selected = Signal(str)  # 'pin', 'draw', 'pan'
    zoom_in = Signal()
    zoom_out = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 8, 2, 8)
        layout.setSpacing(12)
        self.mouse_btn = QPushButton("🖱️")
        self.mouse_btn.setCheckable(True)
        self.mouse_btn.setChecked(True)
        self.mouse_btn.clicked.connect(lambda: self.select_tool('mouse'))
        layout.addWidget(self.mouse_btn)

        self.pin_btn = QPushButton("📍")
        self.pin_btn.setCheckable(True)
        self.pin_btn.clicked.connect(lambda: self.select_tool('pin'))
        layout.addWidget(self.pin_btn)

        self.draw_btn = QPushButton("✏️ Draw")
        self.draw_btn.setCheckable(True)
        self.draw_menu = QMenu(self)
        self.action_line = QAction("Line", self)
        self.action_circle = QAction("Circle", self)
        self.action_square = QAction("Square", self)
        self.draw_menu.addAction(self.action_line)
        self.draw_menu.addAction(self.action_circle)
        self.draw_menu.addAction(self.action_square)
        self.draw_btn.setMenu(self.draw_menu)
        self.action_line.triggered.connect(lambda: self.select_draw_shape('line'))
        self.action_circle.triggered.connect(lambda: self.select_draw_shape('circle'))
        self.action_square.triggered.connect(lambda: self.select_draw_shape('square'))
        self.draw_btn.clicked.connect(self.on_draw_btn_clicked)
        self._last_draw_shape = 'line'  # Default
        layout.addWidget(self.draw_btn)

        self.pan_btn = QPushButton("🖐️")
        self.pan_btn.setCheckable(True)
        self.pan_btn.clicked.connect(lambda: self.select_tool('pan'))
        layout.addWidget(self.pan_btn)

        self.move_btn = QPushButton("🔀 Move")
        self.move_btn.setCheckable(True)
        self.move_btn.clicked.connect(lambda: self.select_tool('move'))
        layout.addWidget(self.move_btn)

        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        layout.addWidget(self.zoom_in_btn)

        self.zoom_out_btn = QPushButton("−")
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        layout.addWidget(self.zoom_out_btn)

        layout.addStretch(1)

    def select_draw_shape(self, shape):
        self._last_draw_shape = shape
        self.select_tool('draw')
        self.tool_selected.emit(f'draw:{shape}')

    def on_draw_btn_clicked(self):
        if self.draw_btn.isChecked():
            self.select_tool('draw')
            self.tool_selected.emit(f'draw:{self._last_draw_shape}')
        else:
            self.select_tool('mouse')

    def select_tool(self, tool):
        self.mouse_btn.setChecked(tool == 'mouse')
        self.pin_btn.setChecked(tool == 'pin')
        self.draw_btn.setChecked(tool == 'draw')
        self.pan_btn.setChecked(tool == 'pan')
        self.move_btn.setChecked(tool == 'move')
        if tool == 'draw':
            self.tool_selected.emit(f'draw:{self._last_draw_shape}')
        else:
            self.tool_selected.emit(tool)