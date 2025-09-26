import os
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSplitter,
    QTreeWidget, QTreeWidgetItem, QMessageBox, QInputDialog, QColorDialog,
    QDialog, QTextEdit, QDialogButtonBox, QComboBox, QListWidget, QFrame,
    QLineEdit, QListWidgetItem, QCheckBox, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QIcon, QPixmap, QPainter
from styles import DEFECTS_TREE_STYLE

class MasterListSelectionDialog(QDialog):
    """Dialog for selecting items from the master list"""
    
    def __init__(self, item_type, master_list_data, parent=None):
        super().__init__(parent)
        self.item_type = item_type
        self.master_list_data = master_list_data
        self.selected_items = []
        
        self.setWindowTitle(f"Select {item_type.title()}s from Master List")
        self.setFixedSize(600, 400)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel(f"Select {self.item_type}s to add to your template:")
        instructions.setFont(QFont("Arial", 10))
        layout.addWidget(instructions)
        
        # Tree widget for master list items with checkboxes
        self.items_tree = QTreeWidget()
        self.items_tree.setHeaderLabel(f"Available {self.item_type.title()}s")
        self.items_tree.setStyleSheet(DEFECTS_TREE_STYLE)
        
        # Populate with master list items
        if self.item_type == 'defect':
            # For defects, we need to collect them from materials since they're stored there
            master_items = self.get_all_defects_from_master_list()
        else:
            category_key = f"{self.item_type}s" if self.item_type != 'status' else 'statuses'
            master_items = self.master_list_data.get(category_key, {})
        
        if not master_items:
            no_items_item = QTreeWidgetItem([f"No {self.item_type}s available in master list"])
            no_items_item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.items_tree.addTopLevelItem(no_items_item)
        else:
            for item_name, item_data in master_items.items():
                # Create tree item with checkbox
                if self.item_type == 'material':
                    defects_count = len(item_data.get('defects', []))
                    tree_item = QTreeWidgetItem([f"📦 {item_name} ({defects_count} defects)"])
                elif self.item_type == 'status':
                    tree_item = QTreeWidgetItem([f"🏷️ {item_name}"])
                elif self.item_type == 'defect':
                    tree_item = QTreeWidgetItem([f"⚠️ {item_name}"])
                else:
                    tree_item = QTreeWidgetItem([item_name])
                
                # Make it checkable
                tree_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
                tree_item.setCheckState(0, Qt.CheckState.Unchecked)
                
                # Add description as tooltip if available
                description = item_data.get('description', '')
                if description:
                    tree_item.setToolTip(0, description)
                
                # Add visual styling based on type
                if self.item_type == 'status':
                    color = item_data.get('color', '#cccccc')
                    tree_item.setBackground(0, QColor(color).lighter(170))
                elif self.item_type == 'material':
                    tree_item.setBackground(0, QColor("#e8f4fd"))
                elif self.item_type == 'defect':
                    severity = item_data.get('severity', 'Medium')
                    severity_colors = {
                        'Low': QColor("#d4edda"),
                        'Medium': QColor("#fff3cd"), 
                        'High': QColor("#fdebd0"),
                        'Critical': QColor("#f8d7da")
                    }
                    tree_item.setBackground(0, severity_colors.get(severity, QColor("#f8f9fa")))
                
                # Store the full data
                tree_item.setData(0, Qt.UserRole, {'name': item_name, 'data': item_data})
                self.items_tree.addTopLevelItem(tree_item)
        
        # Connect tree item changes to update tracking
        self.items_tree.itemChanged.connect(self.on_item_checked)
        
        layout.addWidget(self.items_tree)
        
        # Selection controls
        controls_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all)
        controls_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(self.deselect_all)
        controls_layout.addWidget(deselect_all_btn)
        
        controls_layout.addStretch()
        
        # Show count
        self.count_label = QLabel()
        self.update_count()
        controls_layout.addWidget(self.count_label)
        
        layout.addLayout(controls_layout)
        
        # Selection info
        info_label = QLabel("Tip: Use checkboxes to select multiple items")
        info_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(info_label)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_all_defects_from_master_list(self):
        """Collect all defects from the master list materials"""
        all_defects = {}
        
        # Get defects from materials
        materials = self.master_list_data.get('materials', {})
        for material_name, material_data in materials.items():
            defects_list = material_data.get('defects', [])
            for defect_name in defects_list:
                if defect_name not in all_defects:
                    # Create default defect data
                    all_defects[defect_name] = {
                        'severity': 'Medium',
                        'description': f'Defect from {material_name} material',
                        'source_material': material_name
                    }
        
        return all_defects
    
    def on_item_checked(self, item, column):
        """Handle when an item checkbox is checked/unchecked"""
        self.update_count()
    
    def select_all(self):
        """Select all item checkboxes"""
        for i in range(self.items_tree.topLevelItemCount()):
            item = self.items_tree.topLevelItem(i)
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                item.setCheckState(0, Qt.CheckState.Checked)
    
    def deselect_all(self):
        """Deselect all item checkboxes"""
        for i in range(self.items_tree.topLevelItemCount()):
            item = self.items_tree.topLevelItem(i)
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                item.setCheckState(0, Qt.CheckState.Unchecked)
    
    def update_count(self):
        """Update the selection count label"""
        selected_count = 0
        total_count = 0
        
        for i in range(self.items_tree.topLevelItemCount()):
            item = self.items_tree.topLevelItem(i)
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                total_count += 1
                if item.checkState(0) == Qt.CheckState.Checked:
                    selected_count += 1
        
        self.count_label.setText(f"Selected: {selected_count}/{total_count}")
    
    def get_selected_items(self):
        """Get the selected items with their data"""
        selected_items = []
        for i in range(self.items_tree.topLevelItemCount()):
            item = self.items_tree.topLevelItem(i)
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable and item.checkState(0) == Qt.CheckState.Checked:
                item_data = item.data(0, Qt.UserRole)
                if item_data:
                    selected_items.append({'name': item_data['name'], 'data': item_data['data']})
        return selected_items

class TemplateItemEditDialog(QDialog):
    """Dialog for editing template items (status, material, defect)"""
    
    def __init__(self, item_type, item_name="", item_data=None, parent=None):
        super().__init__(parent)
        self.item_type = item_type
        self.item_name = item_name
        self.item_data = item_data or {}
        
        self.setWindowTitle(f"{'Edit' if item_name else 'Add'} {item_type.title()}")
        self.setFixedSize(500, 400)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Name field (for new items)
        if not self.item_name:
            layout.addWidget(QLabel("Name:"))
            self.name_edit = QLineEdit()
            layout.addWidget(self.name_edit)
        
        if self.item_type == 'status':
            self.setup_status_ui(layout)
        elif self.item_type == 'material':
            self.setup_material_ui(layout)
        elif self.item_type == 'defect':
            self.setup_defect_ui(layout)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def setup_status_ui(self, layout):
        # Color selection
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Color:"))
        
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(60, 30)
        current_color = self.item_data.get('color', '#cccccc')
        self.color_btn.setStyleSheet(f"background-color: {current_color}; border: 1px solid #999;")
        self.color_btn.clicked.connect(self.choose_color)
        color_layout.addWidget(self.color_btn)
        color_layout.addStretch()
        
        layout.addLayout(color_layout)
        
        # Description
        layout.addWidget(QLabel("Description:"))
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        self.description_edit.setPlainText(self.item_data.get('description', ''))
        layout.addWidget(self.description_edit)
    
    def setup_material_ui(self, layout):
        # Description
        layout.addWidget(QLabel("Description:"))
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlainText(self.item_data.get('description', ''))
        layout.addWidget(self.description_edit)
        
        # Associated defects
        layout.addWidget(QLabel("Associated Defects:"))
        
        defects_layout = QHBoxLayout()
        
        self.defects_list = QListWidget()
        defects = self.item_data.get('defects', [])
        for defect in defects:
            self.defects_list.addItem(defect)
        defects_layout.addWidget(self.defects_list)
        
        # Controls
        controls_layout = QVBoxLayout()
        
        add_btn = QPushButton("Add Defect")
        add_btn.clicked.connect(self.add_defect)
        controls_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self.remove_defect)
        controls_layout.addWidget(remove_btn)
        
        controls_layout.addStretch()
        defects_layout.addLayout(controls_layout)
        
        layout.addLayout(defects_layout)
    
    def setup_defect_ui(self, layout):
        # Severity
        layout.addWidget(QLabel("Severity:"))
        self.severity_combo = QComboBox()
        self.severity_combo.addItems(["Low", "Medium", "High", "Critical"])
        current_severity = self.item_data.get('severity', 'Medium')
        index = self.severity_combo.findText(current_severity)
        if index >= 0:
            self.severity_combo.setCurrentIndex(index)
        layout.addWidget(self.severity_combo)
        
        # Description
        layout.addWidget(QLabel("Description:"))
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        self.description_edit.setPlainText(self.item_data.get('description', ''))
        layout.addWidget(self.description_edit)
    
    def choose_color(self):
        current_color = QColor(self.item_data.get('color', '#cccccc'))
        color = QColorDialog.getColor(current_color, self)
        if color.isValid():
            self.item_data['color'] = color.name()
            self.color_btn.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #999;")
    
    def add_defect(self):
        # This method is no longer used since we only select from master list
        QMessageBox.information(self, "Information", "Defects are managed through the Master List. Please add defects there first.")
    
    def remove_defect(self):
        current_row = self.defects_list.currentRow()
        if current_row >= 0:
            self.defects_list.takeItem(current_row)
    
    def get_data(self):
        result = {'name': '', 'data': self.item_data.copy()}
        
        # Get name for new items
        if hasattr(self, 'name_edit'):
            result['name'] = self.name_edit.text()
        else:
            result['name'] = self.item_name
        
        # Get specific data based on type
        if self.item_type == 'status':
            result['data']['description'] = self.description_edit.toPlainText()
        elif self.item_type == 'material':
            result['data']['description'] = self.description_edit.toPlainText()
            defects = []
            for i in range(self.defects_list.count()):
                defects.append(self.defects_list.item(i).text())
            result['data']['defects'] = defects
        elif self.item_type == 'defect':
            result['data']['severity'] = self.severity_combo.currentText()
            result['data']['description'] = self.description_edit.toPlainText()
        
        return result

class DefectSelectionDialog(QDialog):
    """Dialog for selecting defects with dropdown for a specific material"""
    
    def __init__(self, material_name, master_list_data, current_defects=None, parent=None):
        super().__init__(parent)
        self.material_name = material_name
        self.master_list_data = master_list_data
        self.current_defects = current_defects or []
        self.selected_defects = self.current_defects.copy()
        
        self.setWindowTitle(f"Select Defects for {material_name}")
        self.setFixedSize(500, 400)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel(f"Add Defects to: {self.material_name}")
        header_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_label.setStyleSheet("color: #2c3e50; padding: 5px;")
        layout.addWidget(header_label)
        
        # Available defects list with multi-selection
        available_header = QHBoxLayout()
        available_label = QLabel("Available defects for this material:")
        available_header.addWidget(available_label)
        
        # Add selection helper buttons
        select_all_available_btn = QPushButton("Select All")
        select_all_available_btn.setMaximumWidth(80)
        select_all_available_btn.setStyleSheet("font-size: 10px; padding: 2px 4px;")
        select_all_available_btn.clicked.connect(self.select_all_available)
        available_header.addWidget(select_all_available_btn)
        
        clear_selection_btn = QPushButton("Clear")
        clear_selection_btn.setMaximumWidth(60)
        clear_selection_btn.setStyleSheet("font-size: 10px; padding: 2px 4px;")
        clear_selection_btn.clicked.connect(self.clear_available_selection)
        available_header.addWidget(clear_selection_btn)
        
        available_header.addStretch()
        layout.addLayout(available_header)
        
        self.available_list = QListWidget()
        self.available_list.setSelectionMode(QListWidget.MultiSelection)
        
        # Get available defects for this material
        material_defects = self.get_defects_for_material()
        for defect_name, defect_data in material_defects.items():
            if defect_name not in self.selected_defects:  # Only show unselected defects
                severity = defect_data.get('severity', 'Medium')
                list_item = QListWidgetItem(f"⚠️ {defect_name} ({severity})")
                list_item.setData(Qt.UserRole, defect_name)
                self.available_list.addItem(list_item)
        
        layout.addWidget(self.available_list)
        
        # Multi-selection instructions
        instruction_label = QLabel("💡 Tip: Hold Ctrl and click to select multiple defects, or use Select All button")
        instruction_label.setStyleSheet("color: #666; font-size: 10px; font-style: italic; padding: 2px;")
        instruction_label.setWordWrap(True)
        layout.addWidget(instruction_label)
        
        # Add multiple button with enhanced styling
        add_multiple_btn = QPushButton("➕ Add Selected Defects")
        add_multiple_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        add_multiple_btn.clicked.connect(self.add_multiple_defects)
        layout.addWidget(add_multiple_btn)
        
        # Current defects list
        selected_header = QHBoxLayout()
        selected_label = QLabel("Selected defects:")
        selected_header.addWidget(selected_label)
        selected_header.addStretch()
        
        # Count label
        self.count_label = QLabel()
        self.count_label.setStyleSheet("color: #666; font-size: 10px;")
        selected_header.addWidget(self.count_label)
        
        layout.addLayout(selected_header)
        
        self.selected_list = QListWidget()
        self.selected_list.setSelectionMode(QListWidget.MultiSelection)  # Allow multi-selection for removal too
        self.refresh_selected_list()
        layout.addWidget(self.selected_list)
        
        # Remove controls
        remove_controls = QHBoxLayout()
        
        remove_btn = QPushButton("🗑️ Remove Selected")
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        remove_btn.clicked.connect(self.remove_defects)
        remove_controls.addWidget(remove_btn)
        
        clear_all_btn = QPushButton("Clear All")
        clear_all_btn.setStyleSheet("font-size: 10px; padding: 4px 8px;")
        clear_all_btn.clicked.connect(self.clear_all_selected)
        remove_controls.addWidget(clear_all_btn)
        
        remove_controls.addStretch()
        layout.addLayout(remove_controls)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_defects_for_material(self):
        """Get defects available for this material"""
        material_defects = {}
        
        # Get defects from the specific material in master list
        materials = self.master_list_data.get('materials', {})
        if self.material_name in materials:
            material_data = materials[self.material_name]
            defects_data = material_data.get('defects', {})
            
            if isinstance(defects_data, dict):
                # New format: defects as dictionary with full data
                for defect_name, defect_data in defects_data.items():
                    material_defects[defect_name] = defect_data
            elif isinstance(defects_data, list):
                # Old format: defects as list of names
                for defect_name in defects_data:
                    material_defects[defect_name] = {
                        'severity': 'Medium',
                        'description': f'Defect for {self.material_name}',
                        'source_material': self.material_name
                    }
        
        return material_defects
    
    def select_all_available(self):
        """Select all available defects in the list"""
        for i in range(self.available_list.count()):
            item = self.available_list.item(i)
            item.setSelected(True)
    
    def clear_available_selection(self):
        """Clear all selections in the available defects list"""
        self.available_list.clearSelection()
    
    def add_multiple_defects(self):
        """Add multiple selected defects from available list"""
        selected_items = self.available_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select one or more defects to add.")
            return
        
        added_count = 0
        for item in selected_items:
            defect_name = item.data(Qt.UserRole)
            if defect_name and defect_name not in self.selected_defects:
                self.selected_defects.append(defect_name)
                added_count += 1
        
        if added_count > 0:
            # Show brief confirmation
            self.show_brief_message(f"Added {added_count} defect{'s' if added_count > 1 else ''}")
        
        self.refresh_both_lists()
    
    def remove_defects(self):
        """Remove multiple selected defects from list"""
        selected_items = self.selected_list.selectedItems()
        if not selected_items:
            # Fallback to single selection if no multi-selection
            current_item = self.selected_list.currentItem()
            if current_item:
                selected_items = [current_item]
            else:
                QMessageBox.information(self, "No Selection", "Please select one or more defects to remove.")
                return
        
        removed_count = 0
        for item in selected_items:
            defect_name = item.text().replace('⚠️ ', '').split(' (')[0]
            if defect_name in self.selected_defects:
                self.selected_defects.remove(defect_name)
                removed_count += 1
        
        if removed_count > 0:
            self.show_brief_message(f"Removed {removed_count} defect{'s' if removed_count > 1 else ''}")
        
        self.refresh_both_lists()
    
    def clear_all_selected(self):
        """Clear all selected defects"""
        if self.selected_defects:
            count = len(self.selected_defects)
            self.selected_defects.clear()
            self.show_brief_message(f"Cleared {count} defect{'s' if count > 1 else ''}")
            self.refresh_both_lists()
    
    def show_brief_message(self, message):
        """Show a brief status message"""
        # Update the count label temporarily to show the message
        if hasattr(self, 'count_label'):
            original_text = self.count_label.text()
            self.count_label.setText(f"✓ {message}")
            self.count_label.setStyleSheet("color: #28a745; font-size: 10px; font-weight: bold;")
            
            # Use QTimer to restore original text after 2 seconds
            from PySide6.QtCore import QTimer
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: self.restore_count_label(original_text))
            timer.start(2000)
    
    def restore_count_label(self, original_text):
        """Restore the count label to its original state"""
        if hasattr(self, 'count_label'):
            self.count_label.setText(original_text)
            self.count_label.setStyleSheet("color: #666; font-size: 10px;")
    
    def refresh_both_lists(self):
        """Refresh both the available and selected defects lists"""
        material_defects = self.get_defects_for_material()
        
        # Refresh selected list
        self.selected_list.clear()
        for defect_name in self.selected_defects:
            if defect_name in material_defects:
                defect_data = material_defects[defect_name]
                severity = defect_data.get('severity', 'Medium')
                list_item = QListWidgetItem(f"⚠️ {defect_name} ({severity})")
                self.selected_list.addItem(list_item)
        
        # Refresh available list (only show unselected defects)
        self.available_list.clear()
        available_count = 0
        for defect_name, defect_data in material_defects.items():
            if defect_name not in self.selected_defects:
                severity = defect_data.get('severity', 'Medium')
                list_item = QListWidgetItem(f"⚠️ {defect_name} ({severity})")
                list_item.setData(Qt.UserRole, defect_name)
                self.available_list.addItem(list_item)
                available_count += 1
        
        # Update count display
        self.update_count_display(available_count)
    
    def update_count_display(self, available_count):
        """Update the count display"""
        if hasattr(self, 'count_label'):
            selected_count = len(self.selected_defects)
            total_defects = available_count + selected_count
            self.count_label.setText(f"Selected: {selected_count} | Available: {available_count} | Total: {total_defects}")
    
    def refresh_selected_list(self):
        """Refresh the selected defects list (kept for compatibility)"""
        self.refresh_both_lists()
    
    def get_selected_defects(self):
        """Get list of selected defect names"""
        return self.selected_defects.copy()

class TemplateDefectsEditDialog(QDialog):
    """Dialog for editing all defects in a template (add/remove)"""
    
    def __init__(self, template_data, master_list_data, parent=None):
        super().__init__(parent)
        self.template_data = template_data
        self.master_list_data = master_list_data
        self.template_defects = template_data.get('defects', {}).copy()
        
        self.setWindowTitle("Edit Template Defects")
        self.setFixedSize(700, 500)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Manage Template Defects")
        header_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_label.setStyleSheet("color: #2c3e50; padding: 10px;")
        layout.addWidget(header_label)
        
        # Create horizontal splitter for two sides
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side: Available defects from master list
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        
        available_header = QHBoxLayout()
        available_label = QLabel("Available Defects (Master List)")
        available_label.setFont(QFont("Arial", 12, QFont.Bold))
        available_header.addWidget(available_label)
        available_header.addStretch()
        
        # Add selection controls for available defects
        select_all_master_btn = QPushButton("Select All")
        select_all_master_btn.setMaximumWidth(80)
        select_all_master_btn.clicked.connect(self.select_all_available)
        available_header.addWidget(select_all_master_btn)
        
        left_layout.addLayout(available_header)
        
        # Available defects list
        self.available_list = QListWidget()
        self.available_list.setSelectionMode(QListWidget.MultiSelection)
        self.populate_available_defects()
        left_layout.addWidget(self.available_list)
        
        # Add button
        add_btn = QPushButton("➡️ Add Selected")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        add_btn.clicked.connect(self.add_selected_defects)
        left_layout.addWidget(add_btn)
        
        splitter.addWidget(left_frame)
        
        # Right side: Current template defects
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        
        template_header = QHBoxLayout()
        template_label = QLabel("Current Template Defects")
        template_label.setFont(QFont("Arial", 12, QFont.Bold))
        template_header.addWidget(template_label)
        template_header.addStretch()
        
        # Count label
        self.count_label = QLabel()
        self.count_label.setStyleSheet("color: #666; font-size: 10px;")
        template_header.addWidget(self.count_label)
        
        right_layout.addLayout(template_header)
        
        # Template defects list
        self.template_list = QListWidget()
        self.template_list.setSelectionMode(QListWidget.MultiSelection)
        self.populate_template_defects()
        right_layout.addWidget(self.template_list)
        
        # Remove controls
        remove_controls = QHBoxLayout()
        
        remove_btn = QPushButton("🗑️ Remove Selected")
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        remove_btn.clicked.connect(self.remove_selected_defects)
        remove_controls.addWidget(remove_btn)
        
        clear_all_btn = QPushButton("Clear All")
        clear_all_btn.setStyleSheet("font-size: 10px; padding: 4px 8px;")
        clear_all_btn.clicked.connect(self.clear_all_template_defects)
        remove_controls.addWidget(clear_all_btn)
        
        remove_controls.addStretch()
        right_layout.addLayout(remove_controls)
        
        splitter.addWidget(right_frame)
        
        # Set equal sizes
        splitter.setSizes([350, 350])
        layout.addWidget(splitter)
        
        # Instructions
        instruction_label = QLabel("💡 Tip: Select defects on the left to add them, or select defects on the right to remove them.")
        instruction_label.setStyleSheet("color: #666; font-size: 10px; font-style: italic; padding: 5px;")
        instruction_label.setWordWrap(True)
        layout.addWidget(instruction_label)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def populate_available_defects(self):
        """Populate the available defects list from master list"""
        self.available_list.clear()
        
        # Get all defects from master list materials
        all_master_defects = {}
        materials = self.master_list_data.get('materials', {})
        for material_name, material_data in materials.items():
            defects_list = material_data.get('defects', [])
            for defect_name in defects_list:
                if defect_name not in all_master_defects:
                    all_master_defects[defect_name] = {
                        'severity': 'Medium',
                        'description': f'Defect from {material_name} material',
                        'source_material': material_name
                    }
        
        # Add items that are not already in template
        for defect_name, defect_data in all_master_defects.items():
            if defect_name not in self.template_defects:
                severity = defect_data.get('severity', 'Medium')
                source = defect_data.get('source_material', 'Unknown')
                list_item = QListWidgetItem(f"⚠️ {defect_name} ({severity}) - from {source}")
                list_item.setData(Qt.UserRole, {'name': defect_name, 'data': defect_data})
                self.available_list.addItem(list_item)
    
    def populate_template_defects(self):
        """Populate the current template defects list"""
        self.template_list.clear()
        
        for defect_name, defect_data in self.template_defects.items():
            severity = defect_data.get('severity', 'Medium')
            source = defect_data.get('source_material', 'Unknown')
            list_item = QListWidgetItem(f"⚠️ {defect_name} ({severity}) - from {source}")
            list_item.setData(Qt.UserRole, defect_name)
            self.template_list.addItem(list_item)
        
        # Update count
        self.update_count()
    
    def update_count(self):
        """Update the defects count display"""
        count = len(self.template_defects)
        self.count_label.setText(f"Count: {count}")
    
    def select_all_available(self):
        """Select all available defects"""
        for i in range(self.available_list.count()):
            item = self.available_list.item(i)
            item.setSelected(True)
    
    def add_selected_defects(self):
        """Add selected defects from available list to template"""
        selected_items = self.available_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select one or more defects to add.")
            return
        
        added_count = 0
        materials_updated = 0
        
        for item in selected_items:
            item_data = item.data(Qt.UserRole)
            if item_data:
                defect_name = item_data['name']
                defect_data = item_data['data']
                
                if defect_name not in self.template_defects:
                    self.template_defects[defect_name] = defect_data.copy()
                    added_count += 1
                    
                    # Also add this defect to materials that should have it based on master list
                    source_material = defect_data.get('source_material')
                    if source_material:
                        # Check if this material exists in the template
                        materials = self.template_data.get('materials', {})
                        if source_material in materials:
                            material_defects = materials[source_material].get('defects', [])
                            if defect_name not in material_defects:
                                material_defects.append(defect_name)
                                materials[source_material]['defects'] = material_defects
                                materials_updated += 1
        
        if added_count > 0:
            # Synchronize defects with materials
            additional_materials_updated = self.sync_defects_with_materials()
            total_materials_updated = materials_updated + additional_materials_updated
            
            # Refresh both lists
            self.populate_available_defects()
            self.populate_template_defects()
            
            # Create detailed success message
            success_message = f"Added {added_count} defect{'s' if added_count > 1 else ''} to template."
            if total_materials_updated > 0:
                success_message += f"\nAlso updated {total_materials_updated} material{'s' if total_materials_updated > 1 else ''} with associated defects."
            
            QMessageBox.information(self, "Success", success_message)
    
    def remove_selected_defects(self):
        """Remove selected defects from template"""
        selected_items = self.template_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select one or more defects to remove.")
            return
        
        removed_count = 0
        for item in selected_items:
            defect_name = item.data(Qt.UserRole)
            if defect_name and defect_name in self.template_defects:
                # Check if defect is used by any material
                is_used_by_material = False
                materials = self.template_data.get('materials', {})
                for material_name, material_data in materials.items():
                    if defect_name in material_data.get('defects', []):
                        is_used_by_material = True
                        break
                
                if is_used_by_material:
                    reply = QMessageBox.question(
                        self, "Defect In Use",
                        f"Defect '{defect_name}' is currently used by materials in this template.\n"
                        f"Removing it will also remove it from those materials.\n\n"
                        f"Do you want to continue?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply != QMessageBox.Yes:
                        continue
                    
                    # Remove from materials too
                    for material_name, material_data in materials.items():
                        defects_list = material_data.get('defects', [])
                        if defect_name in defects_list:
                            defects_list.remove(defect_name)
                            material_data['defects'] = defects_list
                
                del self.template_defects[defect_name]
                removed_count += 1
        
        if removed_count > 0:
            # Refresh both lists
            self.populate_available_defects()
            self.populate_template_defects()
            
            # Show brief success message
            QMessageBox.information(self, "Success", f"Removed {removed_count} defect{'s' if removed_count > 1 else ''} from template.")
    
    def clear_all_template_defects(self):
        """Clear all defects from template"""
        if not self.template_defects:
            return
        
        reply = QMessageBox.question(
            self, "Clear All Defects",
            "Are you sure you want to remove ALL defects from this template?\n"
            "This will also remove them from all materials.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Clear from materials too
            materials = self.template_data.get('materials', {})
            for material_name, material_data in materials.items():
                material_data['defects'] = []
            
            # Clear template defects
            count = len(self.template_defects)
            self.template_defects.clear()
            
            # Refresh both lists
            self.populate_available_defects()
            self.populate_template_defects()
            
            QMessageBox.information(self, "Success", f"Cleared {count} defects from template.")
    
    def get_template_defects(self):
        """Get the current template defects"""
        return self.template_defects.copy()
    
    def get_updated_template_data(self):
        """Get the updated template data with material changes"""
        return self.template_data
    
    def sync_defects_with_materials(self):
        """Synchronize defects with materials based on master list"""
        materials = self.template_data.get('materials', {})
        master_materials = self.master_list_data.get('materials', {})
        
        updated_materials = 0
        
        # For each material in the template, check if it should have any of the template defects
        for material_name, material_data in materials.items():
            if material_name in master_materials:
                master_defects = master_materials[material_name].get('defects', [])
                current_defects = material_data.get('defects', [])
                
                # Add any template defects that belong to this material but aren't in its list
                for defect_name in self.template_defects.keys():
                    if defect_name in master_defects and defect_name not in current_defects:
                        current_defects.append(defect_name)
                        updated_materials += 1
                
                material_data['defects'] = current_defects
        
        return updated_materials


class TemplateOverviewPage(QWidget):
    """Overview page for editing a specific template"""
    back_to_templates = Signal()
    
    def __init__(self, template_name, template_data=None, templates_dir="", parent=None):
        super().__init__(parent)
        self.template_name = template_name
        self.template_data = template_data or {'statuses': {}, 'materials': {}, 'defects': {}}
        self.templates_dir = templates_dir
        self.master_list_data = {}
        
        self.load_master_list()
        self.setup_ui()
        self.populate_trees()
    
    def load_master_list(self):
        """Load the master list of all available items"""
        master_file = os.path.join(self.templates_dir, 'master_list.json')
        if os.path.exists(master_file):
            try:
                with open(master_file, 'r', encoding='utf-8') as f:
                    self.master_list_data = json.load(f)
            except Exception as e:
                print(f"[WARN] Could not load master list: {e}")
                self.master_list_data = {'statuses': {}, 'materials': {}, 'defects': {}}
        else:
            self.master_list_data = {'statuses': {}, 'materials': {}, 'defects': {}}
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        back_btn = QPushButton("← Back to Templates")
        back_btn.clicked.connect(self.back_to_templates.emit)
        header_layout.addWidget(back_btn)
        
        header_layout.addStretch()
        
        title_label = QLabel(f"Template: {self.template_name}")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Save button
        save_btn = QPushButton("💾 Save Template")
        save_btn.clicked.connect(self.save_template)
        header_layout.addWidget(save_btn)
        
        main_layout.addLayout(header_layout)
        
        # Create splitter for two tree widgets
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side: Statuses tree
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        
        # Statuses header and controls
        statuses_header = QHBoxLayout()
        statuses_title = QLabel("Statuses")
        statuses_title.setFont(QFont("Arial", 14, QFont.Bold))
        statuses_header.addWidget(statuses_title)
        statuses_header.addStretch()
        
        add_status_btn = QPushButton("+ Add from Master List")
        add_status_btn.clicked.connect(lambda: self.add_item('status'))
        statuses_header.addWidget(add_status_btn)
        
        left_layout.addLayout(statuses_header)
        
        # Statuses tree
        self.statuses_tree = QTreeWidget()
        self.statuses_tree.setHeaderLabel("Status Items")
        self.statuses_tree.itemDoubleClicked.connect(lambda item: self.edit_item('status', item))
        left_layout.addWidget(self.statuses_tree)
        
        # Status controls
        status_controls = QHBoxLayout()
        view_status_btn = QPushButton("View Details")
        view_status_btn.clicked.connect(lambda: self.edit_selected_item('status'))
        remove_status_btn = QPushButton("Remove")
        remove_status_btn.clicked.connect(lambda: self.delete_selected_item('status'))
        
        status_controls.addWidget(view_status_btn)
        status_controls.addWidget(remove_status_btn)
        status_controls.addStretch()
        left_layout.addLayout(status_controls)
        
        splitter.addWidget(left_frame)
        
        # Right side: Materials & Defects tree
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        
        # Materials & Defects header and controls
        materials_header = QHBoxLayout()
        materials_title = QLabel("Materials & Defects")
        materials_title.setFont(QFont("Arial", 14, QFont.Bold))
        materials_header.addWidget(materials_title)
        materials_header.addStretch()
        
        add_material_btn = QPushButton("+ Add Material")
        add_material_btn.clicked.connect(lambda: self.add_item('material'))
        materials_header.addWidget(add_material_btn)
        
        edit_defects_btn = QPushButton("✏️ Edit Defects")
        edit_defects_btn.clicked.connect(lambda: self.edit_template_defects())
        materials_header.addWidget(edit_defects_btn)
        
        right_layout.addLayout(materials_header)
        
        # Materials & Defects tree
        self.materials_tree = QTreeWidget()
        self.materials_tree.setHeaderLabels(["Materials & Defects", "Actions"])
        self.materials_tree.setColumnWidth(0, 300)  # Make first column wider
        self.materials_tree.setColumnWidth(1, 150)  # Set width for button column
        self.materials_tree.itemDoubleClicked.connect(self.edit_tree_item)
        right_layout.addWidget(self.materials_tree)
        
        # Material controls
        material_controls = QHBoxLayout()
        remove_material_btn = QPushButton("Remove")
        remove_material_btn.clicked.connect(lambda: self.delete_selected_material_item())
        
        material_controls.addWidget(remove_material_btn)
        material_controls.addStretch()
        right_layout.addLayout(material_controls)
        
        splitter.addWidget(right_frame)
        
        # Set equal sizes
        splitter.setSizes([400, 400])
        main_layout.addWidget(splitter)
    
    def populate_trees(self):
        """Populate both tree widgets with template data"""
        self.populate_statuses_tree()
        self.populate_materials_tree()
    
    def populate_statuses_tree(self):
        """Populate the statuses tree"""
        self.statuses_tree.clear()
        
        statuses = self.template_data.get('statuses', {})
        for status_name, status_data in statuses.items():
            item = QTreeWidgetItem([status_name])
            
            # Add colored icon
            color = status_data.get('color', '#cccccc')
            pixmap = QPixmap(16, 16)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QColor(color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(2, 2, 12, 12)
            painter.end()
            item.setIcon(0, QIcon(pixmap))
            
            # Store data
            item.setData(0, Qt.UserRole, status_data)
            
            self.statuses_tree.addTopLevelItem(item)
    
    def populate_materials_tree(self):
        """Populate the materials and defects tree"""
        self.materials_tree.clear()
        
        materials = self.template_data.get('materials', {})
        defects = self.template_data.get('defects', {})
        
        # Add materials as top-level items
        for material_name, material_data in materials.items():
            material_item = QTreeWidgetItem([f"📦 {material_name}", ""])
            material_item.setData(0, Qt.UserRole, {'type': 'material', 'data': material_data, 'name': material_name})
            
            # Create and add the Select Defects button
            select_button = QPushButton("Select Defects")
            select_button.setMaximumWidth(120)
            select_button.setStyleSheet("""
                QPushButton {
                    background-color: #007ACC;
                    color: white;
                    border: none;
                    padding: 4px 8px;
                    border-radius: 3px;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #005a9e;
                }
            """)
            select_button.clicked.connect(lambda checked, name=material_name: self.select_material_defects(name))
            
            self.materials_tree.addTopLevelItem(material_item)
            self.materials_tree.setItemWidget(material_item, 1, select_button)
            
            # Add associated defects as children with indentation
            associated_defects = material_data.get('defects', [])
            for defect_name in associated_defects:
                if defect_name in defects:
                    defect_item = QTreeWidgetItem([f"    ⚠️ {defect_name}", ""])
                    defect_item.setData(0, Qt.UserRole, {'type': 'defect', 'data': defects[defect_name]})
                    material_item.addChild(defect_item)
        
        # Add standalone defects (not associated with any material)
        standalone_defects = []
        for defect_name in defects.keys():
            is_associated = False
            for material_data in materials.values():
                if defect_name in material_data.get('defects', []):
                    is_associated = True
                    break
            if not is_associated:
                standalone_defects.append(defect_name)
        
        if standalone_defects:
            standalone_item = QTreeWidgetItem(["🔧 Standalone Defects", ""])
            standalone_item.setData(0, Qt.UserRole, {'type': 'category', 'name': 'standalone_defects'})
            for defect_name in standalone_defects:
                defect_item = QTreeWidgetItem([f"    ⚠️ {defect_name}", ""])
                defect_item.setData(0, Qt.UserRole, {'type': 'defect', 'data': defects[defect_name], 'name': defect_name})
                standalone_item.addChild(defect_item)
            self.materials_tree.addTopLevelItem(standalone_item)
        
        # Add a dedicated defects section showing all defects in template
        if defects:
            all_defects_item = QTreeWidgetItem(["📋 All Template Defects", ""])
            all_defects_item.setData(0, Qt.UserRole, {'type': 'category', 'name': 'all_defects'})
            
            for defect_name, defect_data in defects.items():
                severity = defect_data.get('severity', 'Medium')
                defect_item = QTreeWidgetItem([f"    ⚠️ {defect_name} ({severity})", ""])
                defect_item.setData(0, Qt.UserRole, {'type': 'defect', 'data': defect_data, 'name': defect_name})
                all_defects_item.addChild(defect_item)
            
            self.materials_tree.addTopLevelItem(all_defects_item)
        
        # Expand all items
        self.materials_tree.expandAll()
    
    def select_material_defects(self, material_name):
        """Open checkbox-based defect selection dialog for a material"""
        # Get current defects for this material in the template
        current_defects = []
        if 'materials' in self.template_data and material_name in self.template_data['materials']:
            material_defects = self.template_data['materials'][material_name].get('defects', [])
            # Handle both list and dict formats
            if isinstance(material_defects, list):
                current_defects = material_defects
            elif isinstance(material_defects, dict):
                current_defects = list(material_defects.keys())
        
        # Open the defect selection dialog
        dialog = DefectSelectionDialog(material_name, self.master_list_data, current_defects, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_defects = dialog.get_selected_defects()
            
            # Update template data
            if 'materials' not in self.template_data:
                self.template_data['materials'] = {}
            
            # Get master material data if not already in template
            if material_name not in self.template_data['materials']:
                master_materials = self.master_list_data.get('materials', {})
                if material_name in master_materials:
                    self.template_data['materials'][material_name] = master_materials[material_name].copy()
                else:
                    # Create basic material data if not in master list
                    self.template_data['materials'][material_name] = {
                        'description': f'Material: {material_name}',
                        'defects': []
                    }
            
            # Update defects list
            self.template_data['materials'][material_name]['defects'] = selected_defects
            
            # Also ensure we have the defects data in the template defects section
            if 'defects' not in self.template_data:
                self.template_data['defects'] = {}
            
            # Add selected defects to template defects section
            all_master_defects = self.get_all_defects_from_master_list()
            for defect_name in selected_defects:
                if defect_name in all_master_defects:
                    self.template_data['defects'][defect_name] = all_master_defects[defect_name].copy()
            
            # Refresh the materials tree
            self.populate_materials_tree()
    
    def get_all_defects_from_master_list(self):
        """Collect all defects from the master list materials"""
        all_defects = {}
        
        # Get defects from materials
        materials = self.master_list_data.get('materials', {})
        for material_name, material_data in materials.items():
            defects_data = material_data.get('defects', {})
            
            if isinstance(defects_data, dict):
                # New format: defects as dictionary with full data
                for defect_name, defect_data in defects_data.items():
                    if defect_name not in all_defects:
                        defect_copy = defect_data.copy()
                        defect_copy['source_material'] = material_name
                        all_defects[defect_name] = defect_copy
            elif isinstance(defects_data, list):
                # Old format: defects as list of names
                for defect_name in defects_data:
                    if defect_name not in all_defects:
                        all_defects[defect_name] = {
                            'severity': 'Medium',
                            'description': f'Defect from {material_name} material',
                            'source_material': material_name
                        }
        
        return all_defects

    def add_item(self, item_type):
        """Add items from master list to the template"""
        dialog = MasterListSelectionDialog(item_type, self.master_list_data, self)
        if dialog.exec():
            selected_items = dialog.get_selected_items()
            
            if not selected_items:
                QMessageBox.information(self, "No Selection", "No items were selected.")
                return
            
            # Add selected items to template data
            category_key = f"{item_type}s" if item_type != 'status' else 'statuses'
            
            # Ensure the category exists in template data
            if category_key not in self.template_data:
                self.template_data[category_key] = {}
            
            added_count = 0
            defects_added = 0
            
            for item in selected_items:
                name = item['name']
                data = item['data']
                
                # Check if item already exists in template
                if name not in self.template_data[category_key]:
                    self.template_data[category_key][name] = data
                    added_count += 1
                    
                    # If adding a material, also add its defects to the template defects section
                    if item_type == 'material' and 'defects' in data:
                        # Ensure defects section exists in template
                        if 'defects' not in self.template_data:
                            self.template_data['defects'] = {}
                        
                        # Add each defect from this material to the template
                        material_defects = data.get('defects', [])
                        for defect_name in material_defects:
                            if defect_name not in self.template_data['defects']:
                                # Create defect data (since master list stores defects as simple lists in materials)
                                defect_data = {
                                    'severity': 'Medium',  # Default severity
                                    'description': f'Defect from {name} material',
                                    'source_material': name
                                }
                                self.template_data['defects'][defect_name] = defect_data
                                defects_added += 1
            
            # Show confirmation
            if added_count > 0:
                # Create appropriate success message
                success_message = f"Added {added_count} {item_type}(s) to template."
                if item_type == 'material' and defects_added > 0:
                    success_message += f"\nAlso added {defects_added} associated defects."
                
                QMessageBox.information(self, "Success", success_message)
                
                # Auto-save the template
                self.save_template_quietly()
                
                # Refresh the trees to show new items
                self.populate_trees()
            else:
                QMessageBox.information(self, "No Changes", "All selected items already exist in template.")
            
            # Refresh appropriate tree
            if item_type == 'status':
                self.populate_statuses_tree()
            else:
                self.populate_materials_tree()
    
    def edit_item(self, item_type, tree_item):
        """View item details (read-only since items come from master list)"""
        stored_data = tree_item.data(0, Qt.UserRole)
        if not stored_data:
            return
        
        if item_type == 'status':
            item_name = tree_item.text(0)
            item_data = stored_data
        else:
            # For materials tree, get name and data from stored data
            item_name = stored_data.get('name', tree_item.text(0).replace('📦 ', '').replace('⚠️ ', '').split(' (')[0].strip())
            item_data = stored_data.get('data', {})
        
        # Show read-only view of the item
        self.show_item_details(item_type, item_name, item_data)
    
    def show_item_details(self, item_type, item_name, item_data):
        """Show read-only details of an item"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{item_type.title()} Details: {item_name}")
        dialog.setFixedSize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        # Title
        title_label = QLabel(f"{item_type.title()}: {item_name}")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title_label)
        
        # Details based on type
        if item_type == 'status':
            color = item_data.get('color', '#cccccc')
            description = item_data.get('description', 'No description')
            
            color_layout = QHBoxLayout()
            color_layout.addWidget(QLabel("Color:"))
            color_btn = QPushButton()
            color_btn.setFixedSize(60, 30)
            color_btn.setStyleSheet(f"background-color: {color}; border: 1px solid #999;")
            color_btn.setEnabled(False)
            color_layout.addWidget(color_btn)
            color_layout.addStretch()
            layout.addLayout(color_layout)
            
            layout.addWidget(QLabel("Description:"))
            desc_text = QTextEdit()
            desc_text.setPlainText(description)
            desc_text.setReadOnly(True)
            desc_text.setMaximumHeight(100)
            layout.addWidget(desc_text)
            
        elif item_type == 'material':
            description = item_data.get('description', 'No description')
            defects = item_data.get('defects', [])
            
            layout.addWidget(QLabel("Description:"))
            desc_text = QTextEdit()
            desc_text.setPlainText(description)
            desc_text.setReadOnly(True)
            desc_text.setMaximumHeight(80)
            layout.addWidget(desc_text)
            
            layout.addWidget(QLabel(f"Associated Defects ({len(defects)}):"))
            defects_list = QListWidget()
            for defect in defects:
                defects_list.addItem(defect)
            defects_list.setMaximumHeight(100)
            layout.addWidget(defects_list)
            
        elif item_type == 'defect':
            severity = item_data.get('severity', 'Medium')
            description = item_data.get('description', 'No description')
            
            layout.addWidget(QLabel(f"Severity: {severity}"))
            
            layout.addWidget(QLabel("Description:"))
            desc_text = QTextEdit()
            desc_text.setPlainText(description)
            desc_text.setReadOnly(True)
            desc_text.setMaximumHeight(100)
            layout.addWidget(desc_text)
        
        # Note about editing
        note_label = QLabel("Note: Items are managed in the Master List. To edit, go to Templates → Master List tab.")
        note_label.setStyleSheet("color: #666; font-size: 10px; font-style: italic;")
        note_label.setWordWrap(True)
        layout.addWidget(note_label)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def edit_tree_item(self, item):
        """Handle double-click on materials tree item"""
        stored_data = item.data(0, Qt.UserRole)
        if stored_data:
            item_type = stored_data['type']
            # Don't allow editing of category headers
            if item_type == 'category':
                return
            self.edit_item(item_type, item)
    
    def edit_selected_item(self, tree_type):
        """Edit the selected item in the specified tree"""
        if tree_type == 'status':
            current_item = self.statuses_tree.currentItem()
            if current_item:
                self.edit_item('status', current_item)
        else:
            current_item = self.materials_tree.currentItem()
            if current_item:
                self.edit_tree_item(current_item)
    
    def edit_selected_material_item(self):
        """Edit selected item in materials tree"""
        current_item = self.materials_tree.currentItem()
        if current_item:
            self.edit_tree_item(current_item)
    
    def delete_selected_item(self, tree_type):
        """Delete the selected item from the specified tree"""
        if tree_type == 'status':
            current_item = self.statuses_tree.currentItem()
            if current_item:
                self.delete_status_item(current_item)
        else:
            current_item = self.materials_tree.currentItem()
            if current_item:
                self.delete_material_item(current_item)
    
    def delete_selected_material_item(self):
        """Delete selected item in materials tree"""
        current_item = self.materials_tree.currentItem()
        if current_item:
            self.delete_material_item(current_item)
    
    def delete_status_item(self, item):
        """Delete a status item"""
        status_name = item.text(0)
        reply = QMessageBox.question(
            self, "Delete Status",
            f"Are you sure you want to delete status '{status_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.template_data['statuses'].pop(status_name, None)
            self.populate_statuses_tree()
    
    def delete_material_item(self, item):
        """Delete a material or defect item"""
        stored_data = item.data(0, Qt.UserRole)
        if not stored_data:
            return
        
        item_type = stored_data['type']
        
        # Don't allow deletion of category headers
        if item_type == 'category':
            QMessageBox.information(self, "Cannot Delete", "Cannot delete category headers.")
            return
        
        item_name = stored_data.get('name', item.text(0).replace('📦 ', '').replace('⚠️ ', '').split(' (')[0].strip())
        
        reply = QMessageBox.question(
            self, f"Delete {item_type.title()}",
            f"Are you sure you want to delete {item_type} '{item_name}' from this template?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if item_type == 'material':
                self.template_data['materials'].pop(item_name, None)
            elif item_type == 'defect':
                # Remove defect from template
                self.template_data['defects'].pop(item_name, None)
                
                # Also remove from any materials that reference it
                for material_name, material_data in self.template_data.get('materials', {}).items():
                    defects_list = material_data.get('defects', [])
                    if item_name in defects_list:
                        defects_list.remove(item_name)
                        material_data['defects'] = defects_list
            
            self.populate_materials_tree()
    
    def save_template(self):
        """Save the template to file with user feedback"""
        if self.save_template_quietly():
            QMessageBox.information(self, "Success", f"Template '{self.template_name}' saved successfully!")
    
    def save_template_quietly(self):
        """Save the template to file without user feedback, returns success status"""
        template_file = os.path.join(self.templates_dir, f"{self.template_name}.json")
        
        try:
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(self.template_data, f, indent=2)
            return True
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save template: {e}")
            return False
    
    def edit_template_defects(self):
        """Open dialog to edit (add/remove) defects in the template"""
        dialog = TemplateDefectsEditDialog(self.template_data, self.master_list_data, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Update template data with changes
            self.template_data['defects'] = dialog.get_template_defects()
            
            # Auto-save the template
            self.save_template_quietly()
            
            # Refresh the materials tree to show changes
            self.populate_materials_tree()