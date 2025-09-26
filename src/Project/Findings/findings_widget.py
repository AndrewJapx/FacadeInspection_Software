
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, QLabel, QFrame, 
                              QHBoxLayout, QPushButton, QSizePolicy)
from PySide6.QtCore import Qt
from ..Elevations.finding_card import FindingCard
from config.status import STATUS_OPTIONS, STATUS_COLORS
from styles import (FINDINGS_COLUMN_CONTAINER_STYLE, FINDINGS_SCROLL_AREA_STYLE, 
                   FINDINGS_NEW_TASK_BTN_STYLE, get_findings_card_style, 
                   get_findings_column_header_style)


class FindingsWidget(QWidget):
    def __init__(self, parent=None, project_name=None):
        super().__init__(parent)
        
        self.project_name = project_name
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Project header
        if self.project_name:
            project_header = QLabel(f"Findings for: {self.project_name}")
            project_header.setStyleSheet("font-weight: bold; font-size: 14px; color: #333; margin-bottom: 8px;")
            main_layout.addWidget(project_header)

        # Horizontal scroll area for the kanban board
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.board = QWidget()
        self.board_layout = QHBoxLayout(self.board)
        self.board_layout.setSpacing(16)
        self.board_layout.setContentsMargins(8, 8, 8, 8)

        self._populate_kanban_board()

        scroll.setWidget(self.board)
        main_layout.addWidget(scroll)
    
    def _populate_kanban_board(self):
        """Populate the kanban board with project-specific findings"""
        if not self.project_name:
            # Show empty state
            empty_label = QLabel("No project selected")
            empty_label.setStyleSheet("color: #666; font-style: italic; font-size: 16px;")
            self.board_layout.addWidget(empty_label)
            return
        
        try:
            # Load project pins directly since we're working with pin-based findings
            from ..Elevations.findings_logic import load_pins
            pins = load_pins(self.project_name)
            print(f"[FindingsWidget] Loaded {len(pins)} pins for project '{self.project_name}'")
            
            # Group pins by status
            findings_by_status = {status: [] for status in STATUS_OPTIONS}
            findings_by_status['Other'] = []
            
            for pin in pins:
                status = pin.get('status', STATUS_OPTIONS[0]) or STATUS_OPTIONS[0]
                if status in findings_by_status:
                    findings_by_status[status].append(pin)
                else:
                    findings_by_status['Other'].append(pin)
            
            print(f"[FindingsWidget] Grouped pins by status: {[(status, len(pins)) for status, pins in findings_by_status.items() if pins]}")
                    
        except Exception as e:
            print(f"[ERROR] Failed to load pins for project {self.project_name}: {e}")
            error_label = QLabel("Error loading findings")
            error_label.setStyleSheet("color: #d32f2f; font-style: italic; font-size: 16px;")
            self.board_layout.addWidget(error_label)
            return

        # Create a column for each status
        for status in STATUS_OPTIONS:
            status_pins = findings_by_status.get(status, [])
            
            # Create column container
            col_container = QWidget()
            col_container.setFixedWidth(280)  # Fixed width for consistent columns
            col_container.setStyleSheet(FINDINGS_COLUMN_CONTAINER_STYLE)
            
            col_main_layout = QVBoxLayout(col_container)
            col_main_layout.setContentsMargins(12, 12, 12, 12)
            col_main_layout.setSpacing(8)

            # Column header with status and count - colored by status
            count = len(status_pins)
            status_color = STATUS_COLORS.get(status, "#cccccc")
            header = QLabel(f"{status} ({count})")
            header.setStyleSheet(get_findings_column_header_style(status_color))
            col_main_layout.addWidget(header)

            # Scrollable area for findings in this column
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            scroll_area.setStyleSheet(FINDINGS_SCROLL_AREA_STYLE)
            
            # Container for the findings cards
            cards_widget = QWidget()
            cards_layout = QVBoxLayout(cards_widget)
            cards_layout.setContentsMargins(0, 0, 0, 0)
            cards_layout.setSpacing(8)

            # Add finding cards for this status
            for pin in status_pins:
                card = self._create_finding_card(pin)
                cards_layout.addWidget(card)

            # Add stretch to push cards to top
            cards_layout.addStretch(1)
            
            scroll_area.setWidget(cards_widget)
            col_main_layout.addWidget(scroll_area)

            # '+ New task' button at bottom of column
            new_task_btn = QPushButton("+ New task")
            new_task_btn.setStyleSheet(FINDINGS_NEW_TASK_BTN_STYLE)
            col_main_layout.addWidget(new_task_btn)

            self.board_layout.addWidget(col_container)
        
        # Add stretch at the end
        self.board_layout.addStretch(1)
    
    def _create_finding_card(self, pin):
        """Create a finding card widget for a pin"""
        # Get status color for the card
        status = pin.get('status', STATUS_OPTIONS[0]) or STATUS_OPTIONS[0]
        status_color = STATUS_COLORS.get(status, "#cccccc")
        
        card = QFrame()
        card.setStyleSheet(get_findings_card_style(status_color))
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)
        
        # Pin name/title
        title = QLabel(pin.get('name', 'Untitled Finding'))
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: #333;")
        title.setWordWrap(True)
        layout.addWidget(title)
        
        # Material and defect info
        material = pin.get('material', '')
        defect = pin.get('defect', '')
        if material or defect:
            info_text = []
            if material:
                info_text.append(f"Material: {material}")
            if defect:
                info_text.append(f"Defect: {defect}")
            
            info_label = QLabel(" | ".join(info_text))
            info_label.setStyleSheet("font-size: 12px; color: #666;")
            info_label.setWordWrap(True)
            layout.addWidget(info_label)
        
        # Elevation info
        elevation = pin.get('elevation', '')
        if elevation:
            elev_label = QLabel(f"📍 {elevation}")
            elev_label.setStyleSheet("font-size: 11px; color: #888;")
            layout.addWidget(elev_label)
        
        # Pin ID (for debugging/reference)
        pin_id = pin.get('pin_id', '')
        if pin_id:
            id_label = QLabel(f"Pin #{pin_id}")
            id_label.setStyleSheet("font-size: 10px; color: #aaa;")
            layout.addWidget(id_label)
        
        return card
    
    def refresh(self, project_name=None):
        """Refresh the kanban board with updated project findings"""
        if project_name:
            self.project_name = project_name
        
        # Clear existing columns
        while self.board_layout.count() > 0:
            item = self.board_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Repopulate
        self._populate_kanban_board()
    
    def set_project(self, project_name):
        """Set the current project and refresh the kanban board"""
        self.refresh(project_name)
