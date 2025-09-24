from json import tool
from config.status import STATUS_COLORS
from PySide6.QtCore import Signal, QPointF, Qt, QPoint, QSize, QRect, QLineF
from PySide6.QtWidgets import (
    QDialog, QLineEdit, QTextEdit, QComboBox, QDialogButtonBox, QFormLayout,
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame, QSizePolicy,
    QMenu, QListWidget, QListWidgetItem, QFileDialog
)
from PySide6.QtGui import QPixmap, QImage, QPainter, QColor, QIcon, QAction, QPen
import fitz  # PyMuPDF
from Project.Elevations.finding_card import FindingCard
from Project.master_findings import add_finding_from_pin

from PySide6.QtCore import Signal

class ElevationOverviewWidget(QWidget):
    finding_added = Signal()  # Signal to notify when a finding is added
    back_to_project = Signal()  # Signal to notify when back button is pressed

    def __init__(self, pdf_path=None, findings=None, sidebar=None, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.findings = findings or []  # This is the single source of truth for findings/pins for this elevation
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
        self.pdf_viewer = PDFPinViewer(self.pdf_path)
        self.pdf_viewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.pdf_viewer.pin_created.connect(self.on_pin_created)
        self.pdf_viewer.pin_updated.connect(self.on_pin_updated)
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
            dlg = PinTaskDialog(finding, new_pin=False, pdf_path=self.pdf_path, findings=self.findings)
            result = dlg.exec()
            if result == QDialog.Accepted:
                finding['chat'] = dlg.get_chat()
                finding['name'] = dlg.get_name()
                finding['status'] = dlg.get_status()
                finding['category'] = dlg.get_category()
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
        # Add pin info to findings list (model) only after dialog is accepted
        import os
        elevation_name = os.path.basename(self.pdf_path) if self.pdf_path else "Unknown Elevation"
        info = {
            'name': pin.get('name', ''),
            'pos': pin['pos'],
            'status': pin.get('status', ''),
            'material': pin.get('material', ''),
            'defect': pin.get('defect', ''),
            'chat': pin.get('chat', []),
            'elevation_name': elevation_name
        }
        # Prevent duplicate findings for the same pin
        if not any(f['pos'] == info['pos'] for f in self.findings):
            self.findings.append(info)
            self.refresh_findings_sidebar()  # <-- Immediately refresh findings list
        add_finding_from_pin(pin)  # <-- Add pin to master_findings
        self.finding_added.emit()  # <-- Emit signal so sidebar refreshes
        # After adding a pin, set tool to mouse and update toolbar button states
        self.select_tool('mouse')

    def on_pin_updated(self, pin):
        # Update findings list (model) by position
        for info in self.findings:
            if info['pos'].x() == pin['pos'].x() and info['pos'].y() == pin['pos'].y():
                info['name'] = pin.get('name', info['name'])
                info['status'] = pin.get('status', info['status'])
                info['material'] = pin.get('material', info.get('material', ''))
                info['defect'] = pin.get('defect', info.get('defect', ''))
                info['chat'] = pin.get('chat', info.get('chat', []))
                break
        self.refresh_findings_sidebar()

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

class PDFPinViewer(QLabel):
    from PySide6.QtCore import Signal
    pin_created = Signal(dict)  # Emitted when a new pin is created
    pin_updated = Signal(dict)  # Emitted when a pin is updated
    def __init__(self, pdf_path=None, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background: #eee; border: 1px solid #bbb; font-size: 18px;")
        self.pdf_path = pdf_path
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
                    self.open_pin_dialog(pin)
                    return
            return
        if self.mode == 'pin' and event.button() == Qt.LeftButton:
            for pin in self.pins:
                px = pin['pos'].x() * self.base_pixmap.width()
                py = pin['pos'].y() * self.base_pixmap.height()
                if (QPointF(px, py) - QPointF(x, y)).manhattanLength() < 18:
                    self.open_pin_dialog(pin)
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
        dlg = PinTaskDialog(pin, new_pin=new_pin, pdf_path=self.pdf_path)
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
    def __init__(self, pin=None, new_pin=False, pdf_path=None, findings=None, parent=None):
        print(f"[DEBUG] PinTaskDialog __init__ called, pin: {pin}, new_pin: {new_pin}")
    def open_pin_dialog(self, pin, new_pin=False):
        print(f"[DEBUG] open_pin_dialog called, new_pin={new_pin}, pin before dialog: {pin}")
        dlg = PinTaskDialog(pin, new_pin=new_pin, pdf_path=self.pdf_path)
        result = dlg.exec()
        print(f"[DEBUG] PinTaskDialog exec result: {result}")
        if result == QDialog.Accepted:
            pin['chat'] = dlg.get_chat()
            pin['name'] = dlg.get_name()
            pin['status'] = dlg.get_status()
            pin['category'] = dlg.get_category()
            print(f"[DEBUG] PinTaskDialog accepted, pin after dialog: {pin}")
            self.pin_updated.emit(pin)
            self.update()
            return True
        print("[DEBUG] PinTaskDialog cancelled or closed")
        return False
    def on_pin_created(self, pin):
        print("[DEBUG] on_pin_created called with:", pin)
        # Add pin info to findings list (model)
        import os
        elevation_name = os.path.basename(self.pdf_path) if self.pdf_path else "Unknown Elevation"
        info = {
            'name': pin.get('name', ''),
            'pos': pin['pos'],
            'status': pin.get('status', ''),
            'material': pin.get('material', ''),
            'defect': pin.get('defect', ''),
            'chat': pin.get('chat', []),
            'elevation_name': elevation_name
        }
        self.findings.append(info)
        add_finding_from_pin(pin)  # <-- Add pin to master_findings
        self.refresh_findings_sidebar()
        self.finding_added.emit()  # Notify listeners to refresh sidebar
        # After adding a pin, set tool to mouse and update toolbar button states
        self.select_tool('mouse')
    def __init__(self, pin=None, new_pin=False, pdf_path=None, findings=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pin Details")
        self.pin = pin or {}
        self.new_pin = new_pin
        self.pdf_path = pdf_path
        self.findings = findings or []

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
        for msg in self.pin.get('chat', []):
            if isinstance(msg, dict) and msg.get('type') == 'photo':
                widget = ChatItemWidget(image_path=msg['path'], date=msg.get('date'))
                item = QListWidgetItem()
                item.setSizeHint(widget.sizeHint())
                self.chat_log.addItem(item)
                self.chat_log.setItemWidget(item, widget)
            else:
                # Assume text message
                date = msg['date'] if isinstance(msg, dict) and 'date' in msg else None
                text = msg['text'] if isinstance(msg, dict) and 'text' in msg else str(msg)
                widget = ChatItemWidget(text=text, date=date)
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
            color = STATUS_COLORS.get(status, "#cccccc")
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
        try:
            from config.categories import CATEGORY_OPTIONS
        except ImportError:
            CATEGORY_OPTIONS = {}
        self.CATEGORY_OPTIONS = CATEGORY_OPTIONS
        for material in CATEGORY_OPTIONS.keys():
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
            defects = CATEGORY_OPTIONS.get(self.pin['material'], [])
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

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

    def on_material_changed(self, material):
        self.defect_combo.clear()
        self.defect_combo.addItem("")
        defects = self.CATEGORY_OPTIONS.get(material, [])
        self.defect_combo.addItems(defects)

    def attach_photo(self):
        from PySide6.QtWidgets import QFileDialog, QListWidgetItem
        from Project.Elevations.chat_item_widget import ChatItemWidget
        import datetime
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Photo", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if file_path:
            widget = ChatItemWidget(image_path=file_path, date=datetime.datetime.now())
            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())
            self.chat_log.addItem(item)
            self.chat_log.setItemWidget(item, widget)

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
        # Return all chat messages as a list, including photo paths
        chat = []
        for i in range(self.chat_log.count()):
            item = self.chat_log.item(i)
            if item.icon().isNull():
                chat.append(item.text())
            else:
                # Store as a tuple or special string for photo
                chat.append(item.text())
        return chat

    def add_chat_message(self):
        from Project.Elevations.chat_item_widget import ChatItemWidget
        import datetime
        msg = self.chat_input.text().strip()
        if msg:
            widget = ChatItemWidget(text=msg, date=datetime.datetime.now())
            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())
            self.chat_log.addItem(item)
            self.chat_log.setItemWidget(item, widget)
            self.chat_input.clear()
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






###SHIT CODE BELOW###
import os
from json import tool
from config.status import STATUS_COLORS
from PySide6.QtCore import Signal, QPointF, Qt, QPoint, QSize, QRect, QLineF
from PySide6.QtWidgets import (
    QDialog, QLineEdit, QTextEdit, QComboBox, QDialogButtonBox, QFormLayout,
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame, QSizePolicy,
    QMenu, QListWidget, QListWidgetItem, QFileDialog
)
from PySide6.QtGui import QPixmap, QImage, QPainter, QColor, QIcon, QAction, QPen
from Project.Elevations.finding_card import FindingCard
from Project.master_findings import add_finding_from_pin

from PySide6.QtCore import Signal

class ElevationOverviewWidget(QWidget):
    finding_added = Signal()  # Signal to notify when a finding is added
    back_to_project = Signal()  # Signal to notify when back button is pressed

    def __init__(self, pdf_path=None, findings=None, sidebar=None, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.findings = findings or []  # This is the single source of truth for findings/pins for this elevation
        self.sidebar = sidebar  # SidebarNav instance, if provided

        # Top-level vertical layout: [Back Button | Main Horizontal Layout]
        top_layout = QVBoxLayout(self)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)

        # --- Back Button ---
        back_btn = QPushButton("\u2190 Back")
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
        self.pdf_viewer = PDFPinViewer(self.pdf_path)
        self.pdf_viewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.pdf_viewer.pin_created.connect(self.on_pin_created)
        self.pdf_viewer.pin_updated.connect(self.on_pin_updated)
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



    def refresh_findings_sidebar(self):
        print("[DEBUG] refresh_findings_sidebar called. findings:", self.findings)
        # Remove all cards except header, stretch, and add_btn
        for i in reversed(range(1, self.findings_layout.count() - 2)):
            widget = self.findings_layout.itemAt(i).widget()
            if widget:
                pass
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
            dlg = PinTaskDialog(finding, new_pin=False, pdf_path=self.pdf_path, findings=self.findings)
            result = dlg.exec()
            if result == QDialog.Accepted:
                pass
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
        # Add pin info to findings list (model) only after dialog is accepted
        elevation_name = os.path.basename(self.pdf_path) if self.pdf_path else "Unknown Elevation"
        info = {
            'name': pin.get('name', ''),
            'pos': pin['pos'],
            'status': pin.get('status', ''),
            'material': pin.get('material', ''),
            'defect': pin.get('defect', ''),
            'chat': pin.get('chat', []),
            'elevation_name': elevation_name
        }
        # Prevent duplicate findings for the same pin
        if not any(f['pos'] == info['pos'] for f in self.findings):
            self.findings.append(info)
        self.refresh_findings_sidebar()  # <-- Immediately refresh findings list
        add_finding_from_pin(pin)  # <-- Add pin to master_findings
        self.finding_added.emit()  # <-- Emit signal so sidebar refreshes
        # After adding a pin, set tool to mouse and update toolbar button states
        self.select_tool('mouse')

    def on_pin_updated(self, pin):
        # Update findings list (model) by position
        for info in self.findings:
            if info['pos'].x() == pin['pos'].x() and info['pos'].y() == pin['pos'].y():
                pass
        self.refresh_findings_sidebar()

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

class PDFPinViewer(QLabel):
    from PySide6.QtCore import Signal
    pin_created = Signal(dict)  # Emitted when a new pin is created
    pin_updated = Signal(dict)  # Emitted when a pin is updated
    def __init__(self, pdf_path=None, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background: #eee; border: 1px solid #bbb; font-size: 18px;")
        self.pdf_path = pdf_path
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
                import fitz
                doc = fitz.open(self.pdf_path)
                page = doc.load_page(0)
                pix = page.get_pixmap()
                image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGBA8888 if pix.alpha else QImage.Format_RGB888)
                self.base_pixmap = QPixmap.fromImage(image)
                self.setPixmap(self.base_pixmap)
            except Exception as e:
                self.setText(f"Error loading PDF: {e}")
                self.base_pixmap = None
        elif self.pdf_path:
            self.setText("Not a PDF file: " + str(self.pdf_path))
            self.base_pixmap = None
        else:
            self.setText("No PDF selected.")
            self.base_pixmap = None

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
            # Clickable pin editing
            for i, pin in enumerate(self.pins):
                pin_px = pin['pos'].x() * self.base_pixmap.width() * self.scale + x_offset
                pin_py = pin['pos'].y() * self.base_pixmap.height() * self.scale + y_offset
                dist = ((event.x() - pin_px) ** 2 + (event.y() - pin_py) ** 2) ** 0.5
                if dist < 18:
                    self.open_pin_dialog(pin, new_pin=False)
                    return
            return
        if self.mode == 'pin' and event.button() == Qt.LeftButton:
            # Only place a new pin in pin mode
            pin = {
                'pos': click_point,
                'name': '',
                'status': '',
                'material': '',
                'defect': '',
                'chat': []
            }
            dlg = PinTaskDialog(pin, new_pin=True, pdf_path=self.pdf_path)
            result = dlg.exec()
            if result == QDialog.Accepted:
                pin['name'] = dlg.get_name()
                pin['status'] = dlg.get_status()
                pin['material'] = dlg.get_material()
                pin['defect'] = dlg.get_defect()
                pin['chat'] = dlg.get_chat()
                self.pins.append(pin)
                self.pin_created.emit(pin)
                self.update()
            return
        if self.mode == 'move' and event.button() == Qt.LeftButton:
            # Only allow moving pins, never placing
            for i, pin in enumerate(self.pins):
                pin_px = pin['pos'].x() * self.base_pixmap.width() * self.scale + x_offset
                pin_py = pin['pos'].y() * self.base_pixmap.height() * self.scale + y_offset
                dist = ((event.x() - pin_px) ** 2 + (event.y() - pin_py) ** 2) ** 0.5
                if dist < 18:
                    self.moving_object = {'type': 'pin', 'index': i, 'offset': QPoint(event.x() - pin_px, event.y() - pin_py)}
                    self.setCursor(Qt.ClosedHandCursor)
                    return
            return
        if self.mode == 'pan' and event.button() == Qt.LeftButton:
            self.last_pan_point = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            return

    def mouseMoveEvent(self, event):
        label_size = self.size()
        pixmap_size = self.scaled_pixmap_size()
        x_offset = (label_size.width() - pixmap_size.width()) // 2 + self.offset.x()
        y_offset = (label_size.height() - pixmap_size.height()) // 2 + self.offset.y()
        x = (event.x() - x_offset) / self.scale
        y = (event.y() - y_offset) / self.scale
        if self.mode == 'move' and self.moving_object:
            if self.moving_object['type'] == 'pin':
                i = self.moving_object['index']
                offset = self.moving_object['offset']
                new_x = (event.x() - offset.x() - x_offset) / (self.base_pixmap.width() * self.scale)
                new_y = (event.y() - offset.y() - y_offset) / (self.base_pixmap.height() * self.scale)
                self.pins[i]['pos'] = QPointF(new_x, new_y)
                self.pin_updated.emit(self.pins[i])
                self.update()
            return

    def mouseReleaseEvent(self, event):
        if self.mode == 'move' and self.moving_object:
            self.moving_object = None
            self.setCursor(Qt.SizeAllCursor)
            self.update()
            return

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
            pass
            pass
        elif shape['type'] in ('square', 'circle'):
            pass
        return False

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.base_pixmap:
            return
        painter = QPainter(self)
        # Draw the scaled PDF pixmap
        pixmap_size = self.scaled_pixmap_size()
        label_size = self.size()
        x_offset = (label_size.width() - pixmap_size.width()) // 2 + self.offset.x()
        y_offset = (label_size.height() - pixmap_size.height()) // 2 + self.offset.y()
        scaled_pixmap = self.base_pixmap.scaled(pixmap_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        painter.drawPixmap(x_offset, y_offset, scaled_pixmap)

        # Draw pins (no name text)
        pin_radius = 12
        for pin in self.pins:
            rel_x = pin['pos'].x()
            rel_y = pin['pos'].y()
            px = int(rel_x * self.base_pixmap.width() * self.scale) + x_offset
            py = int(rel_y * self.base_pixmap.height() * self.scale) + y_offset
            painter.setPen(QPen(QColor(220, 0, 0), 2))
            painter.setBrush(QColor(220, 0, 0))
            painter.drawEllipse(QPoint(px, py), pin_radius, pin_radius)
        painter.end()
# ...existing code...

# --- Pin Task Dialog with Chat ---

class PinTaskDialog(QDialog):
    def __init__(self, pin=None, new_pin=False, pdf_path=None, findings=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pin Details")
        self.pin = pin or {}
        self.new_pin = new_pin
        self.pdf_path = pdf_path
        self.findings = findings or []

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
        for msg in self.pin.get('chat', []):
            pass
        chat_layout.addWidget(self.chat_log, 2)
        chat_input_row = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Enter message here...")
        chat_input_row.addWidget(self.chat_input, 1)
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.add_chat_message)
        chat_input_row.addWidget(self.send_btn)
        self.attach_btn = QPushButton("\ud83d\udcce Attach Photo")
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
            self.status_combo.addItem(status)
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
        # Define CATEGORY_OPTIONS here
        CATEGORY_OPTIONS = {
            "Concrete": ["Crack", "Spall", "Stain", "Efflorescence"],
            "Brick": ["Crack", "Spall", "Stain", "Efflorescence"],
            "Stone": ["Crack", "Spall", "Stain", "Efflorescence"],
            "Metal": ["Corrosion", "Deformation", "Loose"],
            "Glass": ["Breakage", "Stain", "Seal Failure"],
            "Other": ["Other"]
        }
        self.CATEGORY_OPTIONS = CATEGORY_OPTIONS
        for material in CATEGORY_OPTIONS.keys():
            self.material_combo.addItem(material)
        if self.pin.get('material'):
            idx = self.material_combo.findText(self.pin.get('material'))
            if idx >= 0:
                self.material_combo.setCurrentIndex(idx)
        self.material_combo.currentTextChanged.connect(self.on_material_changed)
        attr_layout.addWidget(self.material_combo)

        defect_label = QLabel("Defect:")
        attr_layout.addWidget(defect_label)
        self.defect_combo = QComboBox()
        self.defect_combo.addItem("")
        if self.pin.get('material'):
            defects = self.CATEGORY_OPTIONS.get(self.pin.get('material'), [])
            self.defect_combo.addItems(defects)
            idx = self.defect_combo.findText(self.pin.get('defect', ''))
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

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

    def on_material_changed(self, material):
        self.defect_combo.clear()
        self.defect_combo.addItem("")
        defects = self.CATEGORY_OPTIONS.get(material, [])
        self.defect_combo.addItems(defects)

    def attach_photo(self):
        from PySide6.QtWidgets import QFileDialog, QListWidgetItem
        from Project.Elevations.chat_item_widget import ChatItemWidget
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Photo", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if file_path:
            widget = ChatItemWidget(image_path=file_path)
            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())
            self.chat_log.addItem(item)
            self.chat_log.setItemWidget(item, widget)

    def update_mini_map(self):
        if not self.pdf_path or not self.pin or 'pos' not in self.pin:
            self.mini_map.clear()
            return
        try:
            import fitz
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
                image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGBA8888 if pix.alpha else QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(image)
                rel_x = self.pin['pos'].x()
                rel_y = self.pin['pos'].y()
                pin_x_pdf = rel_x * page_width
                pin_y_pdf = rel_y * page_height
                pin_x = int(pin_x_pdf * scale)
                pin_y = int(pin_y_pdf * scale)
                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setBrush(QColor(255, 69, 0))
                painter.setPen(QColor(255, 69, 0))
                painter.drawEllipse(QPoint(pin_x, pin_y), 8, 8)
                painter.end()
                self.mini_map.setPixmap(pixmap)
            else:
                self.mini_map.clear()
        except Exception as e:
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
        # Return all chat messages as a list, including photo paths
        chat = []
        for i in range(self.chat_log.count()):
            pass
        return chat

    def add_chat_message(self):
        from Project.Elevations.chat_item_widget import ChatItemWidget
        msg = self.chat_input.text().strip()
        if msg:
            widget = ChatItemWidget(text=msg)
            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())
            self.chat_log.addItem(item)
            self.chat_log.setItemWidget(item, widget)
            self.chat_input.clear()

    def wheelEvent(self, event):
        # Zoom in/out with Ctrl+scroll or just scroll wheel
        if hasattr(event, 'angleDelta'):
            pass
        else:
            pass
        if event.modifiers() & Qt.ControlModifier or True:  
            pass
        else:
            pass

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
            pass
        else:
            pass

    def select_tool(self, tool):
        self.mouse_btn.setChecked(tool == 'mouse')
        self.pin_btn.setChecked(tool == 'pin')
        self.draw_btn.setChecked(tool == 'draw')
        self.pan_btn.setChecked(tool == 'pan')
        self.move_btn.setChecked(tool == 'move')
        if tool == 'draw':
            pass
        else:
            pass