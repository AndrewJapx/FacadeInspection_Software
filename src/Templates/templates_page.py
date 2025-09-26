import os
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QScrollArea, 
    QGridLayout, QDialog, QLineEdit, QComboBox, QMessageBox, QDialogButtonBox,
    QTabWidget, QListWidget, QListWidgetItem, QInputDialog, QColorDialog,
    QFrame, QTextEdit, QSpacerItem, QSizePolicy, QTreeWidget, QTreeWidgetItem,
    QAbstractItemView, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap, QPalette, QColor
from .new_template_card import NewTemplateCard
from styles import (
    DEFECTS_TREE_STYLE, EDITABLE_ITEM_CARD_STYLE, EDIT_DEFECTS_BUTTON_STYLE,
    MATERIAL_DESCRIPTION_STYLE, DEFECTS_COUNT_STYLE,
    MATERIAL_DIALOG_TITLE_STYLE,
    MATERIAL_INFO_SECTION_STYLE,
    MATERIAL_INFO_HEADER_STYLE,
    MATERIAL_INFO_INPUT_STYLE,
    MATERIAL_INFO_LABEL_STYLE,
    DEFECTS_SECTION_STYLE,
    DEFECTS_HEADER_STYLE,
    DEFECTS_LIST_WIDGET_STYLE,
    DEFECTS_INSTRUCTIONS_STYLE,
    ADD_DEFECT_BUTTON_STYLE,
    REMOVE_DEFECT_BUTTON_STYLE,
    EXISTING_DEFECTS_SECTION_STYLE,
    EXISTING_DEFECTS_HEADER_STYLE,
    EXISTING_DEFECTS_SCROLL_STYLE,
    EXISTING_DEFECTS_CHECKBOX_STYLE,
    EXISTING_DEFECTS_INSTRUCTIONS_STYLE
)

class EditableItemCard(QFrame):
    """Card widget for displaying and editing template items (materials, defects, statuses)"""
    item_updated = Signal(str, dict)  # Signal when item is updated
    item_deleted = Signal(str)        # Signal when item is deleted
    
    def __init__(self, item_type, item_name, item_data=None, parent=None):
        super().__init__(parent)
        self.item_type = item_type  # 'material', 'defect', 'status'
        self.item_name = item_name
        self.item_data = item_data or {}
        
        self.setFrameStyle(QFrame.Box)
        self.setMinimumHeight(140)  # Increased minimum height
        self.setMaximumHeight(220)  # Increased maximum height  
        self.setStyleSheet(EDITABLE_ITEM_CARD_STYLE)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Header with name and actions
        header_layout = QHBoxLayout()
        
        # Item name with icon based on type
        icon = "📊" if self.item_type == 'status' else "🏗️" if self.item_type == 'material' else "⚠️"
        name_label = QLabel(f"{icon} {self.item_name}")
        name_label.setFont(QFont("Arial", 11, QFont.Bold))
        header_layout.addWidget(name_label)
        
        header_layout.addStretch()
        
        # Edit and delete buttons
        edit_btn = QPushButton("✏️")
        edit_btn.setFixedSize(24, 24)
        edit_btn.setToolTip("Edit")
        edit_btn.clicked.connect(self.edit_item)
        
        delete_btn = QPushButton("🗑")
        delete_btn.setFixedSize(24, 24)
        delete_btn.setToolTip("Delete")
        delete_btn.clicked.connect(self.delete_item)
        
        header_layout.addWidget(edit_btn)
        header_layout.addWidget(delete_btn)
        
        layout.addLayout(header_layout)
        
        # Content based on item type
        if self.item_type == 'status':
            self.setup_status_content(layout)
        elif self.item_type == 'material':
            self.setup_material_content(layout)
        elif self.item_type == 'defect':
            self.setup_defect_content(layout)
    
    def setup_status_content(self, layout):
        color = self.item_data.get('color', '#cccccc')
        description = self.item_data.get('description', '')
        
        # Color indicator
        color_frame = QFrame()
        color_frame.setFixedSize(40, 20)
        color_frame.setStyleSheet(f"background-color: {color}; border: 1px solid #999;")
        
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Color:"))
        color_layout.addWidget(color_frame)
        color_layout.addStretch()
        layout.addLayout(color_layout)
        
        # Description
        if description:
            desc_label = QLabel(description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: #666; font-size: 10px;")
            layout.addWidget(desc_label)
    
    def setup_material_content(self, layout):
        defects = self.item_data.get('defects', [])
        description = self.item_data.get('description', '')
        
        # Description (truncated if too long)
        if description:
            desc_text = description if len(description) <= 50 else description[:47] + "..."
            desc_label = QLabel(desc_text)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet(MATERIAL_DESCRIPTION_STYLE)
            desc_label.setMaximumHeight(30)
            layout.addWidget(desc_label)
        
        # Defects count - always show, even if 0
        defects_count_label = QLabel(f"Defects: {len(defects)}")
        defects_count_label.setStyleSheet(DEFECTS_COUNT_STYLE)
        layout.addWidget(defects_count_label)
        
        # Add some spacing before button
        layout.addStretch()
        
        # Edit Defects button - ensure it's always visible
        edit_defects_btn = QPushButton("Edit Defects")
        edit_defects_btn.setMinimumHeight(25)
        edit_defects_btn.setMaximumHeight(30)
        edit_defects_btn.setStyleSheet(EDIT_DEFECTS_BUTTON_STYLE)
        edit_defects_btn.clicked.connect(self.edit_material_defects)
        layout.addWidget(edit_defects_btn)
    
    def edit_material_defects(self):
        """Edit defects for this material"""
        # Get parent TemplatesPage to access master list data
        templates_page = None
        parent_widget = self.parent()
        while parent_widget:
            if hasattr(parent_widget, 'master_list_data'):
                templates_page = parent_widget
                break
            parent_widget = parent_widget.parent()
        
        if not templates_page:
            QMessageBox.warning(self, "Error", "Cannot access master list data.")
            return
        
        # Create a dialog to edit defects for this material
        dialog = MaterialDefectsEditDialog(self.item_name, templates_page.master_list_data, 
                                         template_mode=False, parent=self)
        if dialog.exec():
            # Don't update item_data here - let the parent refresh handle it
            # The dialog has already updated the master_list_data
            
            # Save the updated master list
            templates_page.save_master_list()
            
            # Refresh the entire master list display instead of just this card
            templates_page.refresh_master_category_display('material')
    
    def setup_defect_content(self, layout):
        severity = self.item_data.get('severity', 'Medium')
        description = self.item_data.get('description', '')
        
        # Severity
        severity_label = QLabel(f"Severity: {severity}")
        severity_label.setStyleSheet("color: #FF9800; font-size: 10px; font-weight: bold;")
        layout.addWidget(severity_label)
        
        # Description
        if description:
            desc_label = QLabel(description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: #666; font-size: 10px;")
            layout.addWidget(desc_label)
    
    def edit_item(self):
        if self.item_type == 'status':
            self.edit_status()
        elif self.item_type == 'material':
            self.edit_material()
        elif self.item_type == 'defect':
            self.edit_defect()
    
    def edit_status(self):
        dialog = StatusEditDialog(self.item_name, self.item_data, self)
        if dialog.exec():
            new_data = dialog.get_data()
            self.item_data = new_data
            self.item_updated.emit(self.item_name, new_data)
            self.refresh_display()
    
    def edit_material(self):
        # Get master list data from parent if available
        master_list_data = {}
        parent_widget = self.parent()
        while parent_widget:
            if hasattr(parent_widget, 'master_list_data'):
                master_list_data = parent_widget.master_list_data
                break
            parent_widget = parent_widget.parent()
        
        dialog = MaterialEditDialog(self.item_name, self.item_data, self, master_list_data)
        if dialog.exec():
            new_data = dialog.get_data()
            self.item_data = new_data
            self.item_updated.emit(self.item_name, new_data)
            self.refresh_display()
    
    def edit_defect(self):
        dialog = DefectEditDialog(self.item_name, self.item_data, self)
        if dialog.exec():
            new_data = dialog.get_data()
            self.item_data = new_data
            self.item_updated.emit(self.item_name, new_data)
            self.refresh_display()
    
    def delete_item(self):
        reply = QMessageBox.question(
            self, "Delete Item", 
            f"Are you sure you want to delete '{self.item_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.item_deleted.emit(self.item_name)
    
    def refresh_display(self):
        # Clear and rebuild the UI
        for i in reversed(range(self.layout().count())): 
            item = self.layout().itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.setParent(None)
                else:
                    # Handle spacers or other layout items
                    self.layout().removeItem(item)
        self.setup_ui()

class StatusEditDialog(QDialog):
    def __init__(self, name, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Edit Status: {name}")
        self.setFixedSize(400, 300)
        self.data = data.copy()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Color selection
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Color:"))
        
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(60, 30)
        current_color = self.data.get('color', '#cccccc')
        self.color_btn.setStyleSheet(f"background-color: {current_color}; border: 1px solid #999;")
        self.color_btn.clicked.connect(self.choose_color)
        color_layout.addWidget(self.color_btn)
        color_layout.addStretch()
        
        layout.addLayout(color_layout)
        
        # Description
        layout.addWidget(QLabel("Description:"))
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        self.description_edit.setPlainText(self.data.get('description', ''))
        layout.addWidget(self.description_edit)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def choose_color(self):
        current_color = QColor(self.data.get('color', '#cccccc'))
        color = QColorDialog.getColor(current_color, self)
        if color.isValid():
            self.data['color'] = color.name()
            self.color_btn.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #999;")
    
    def get_data(self):
        self.data['description'] = self.description_edit.toPlainText()
        return self.data

class MaterialEditDialog(QDialog):
    def __init__(self, name, data, parent=None, master_list_data=None):
        super().__init__(parent)
        self.setWindowTitle(f"Edit Material: {name}")
        self.setFixedSize(600, 500)
        self.data = data.copy()
        self.master_list_data = master_list_data or {}
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Description
        layout.addWidget(QLabel("Description:"))
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlainText(self.data.get('description', ''))
        layout.addWidget(self.description_edit)
        
        # Defects selection from master list
        layout.addWidget(QLabel("Select Associated Defects from Master List:"))
        
        # Create tree widget for defect selection
        self.defects_tree = QTreeWidget()
        self.defects_tree.setHeaderLabel("Available Defects")
        self.defects_tree.setMaximumHeight(200)
        
        # Populate with master list defects
        master_defects = self.master_list_data.get('defects', {})
        current_defects = self.data.get('defects', [])
        
        for defect_name, defect_data in master_defects.items():
            item = QTreeWidgetItem([defect_name])
            
            # Add severity and description as sub-items
            severity = defect_data.get('severity', 'Medium')
            description = defect_data.get('description', 'No description')
            
            severity_item = QTreeWidgetItem([f"Severity: {severity}"])
            severity_item.setFlags(severity_item.flags() & ~Qt.ItemIsUserCheckable)
            item.addChild(severity_item)
            
            if description:
                desc_item = QTreeWidgetItem([f"Description: {description}"])
                desc_item.setFlags(desc_item.flags() & ~Qt.ItemIsUserCheckable)
                item.addChild(desc_item)
            
            # Make the main item checkable
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            
            # Check if this defect is already associated
            if defect_name in current_defects:
                item.setCheckState(0, Qt.Checked)
            else:
                item.setCheckState(0, Qt.Unchecked)
            
            self.defects_tree.addTopLevelItem(item)
        
        # Expand all items to show details
        self.defects_tree.expandAll()
        layout.addWidget(self.defects_tree)
        
        # Info label
        info_label = QLabel("✓ Check defects to associate them with this material")
        info_label.setStyleSheet("color: #666; font-size: 10px; font-style: italic;")
        layout.addWidget(info_label)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_data(self):
        self.data['description'] = self.description_edit.toPlainText()
        
        # Get selected defects from tree
        defects = []
        for i in range(self.defects_tree.topLevelItemCount()):
            item = self.defects_tree.topLevelItem(i)
            if item.checkState(0) == Qt.Checked:
                defects.append(item.text(0))
        
        self.data['defects'] = defects
        return self.data

class DefectEditDialog(QDialog):
    def __init__(self, name, data, parent=None):
        super().__init__(parent)
        self.defect_name = name
        self.setWindowTitle(f"{'Edit' if name else 'Add'} Defect{': ' + name if name else ''}")
        self.setFixedSize(400, 350)
        self.data = data.copy()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Name field (for new defects)
        if not self.defect_name:
            layout.addWidget(QLabel("Defect Name:"))
            self.name_edit = QLineEdit()
            self.name_edit.setPlaceholderText("Enter defect name...")
            layout.addWidget(self.name_edit)
        
        # Severity
        layout.addWidget(QLabel("Severity:"))
        self.severity_combo = QComboBox()
        self.severity_combo.addItems(["Low", "Medium", "High", "Critical"])
        current_severity = self.data.get('severity', 'Medium')
        index = self.severity_combo.findText(current_severity)
        if index >= 0:
            self.severity_combo.setCurrentIndex(index)
        layout.addWidget(self.severity_combo)
        
        # Description
        layout.addWidget(QLabel("Description:"))
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        self.description_edit.setPlaceholderText("Enter defect description...")
        self.description_edit.setPlainText(self.data.get('description', ''))
        layout.addWidget(self.description_edit)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_data(self):
        result = {
            'severity': self.severity_combo.currentText(),
            'description': self.description_edit.toPlainText()
        }
        
        # Add name for new defects
        if hasattr(self, 'name_edit'):
            result['name'] = self.name_edit.text().strip()
        else:
            result['name'] = self.defect_name
            
        return result

class MaterialAndDefectsDialog(QDialog):
    """Simple dialog for adding materials - similar to DefectEditDialog"""
    
    def __init__(self, master_list_data, parent=None):
        super().__init__(parent)
        self.master_list_data = master_list_data.copy()  # Work with a copy
        self.setWindowTitle("Add Material")
        self.setFixedSize(400, 300)  # Same size as DefectEditDialog
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Material name
        layout.addWidget(QLabel("Material Name:"))
        self.material_name_edit = QLineEdit()
        self.material_name_edit.setPlaceholderText("Enter material name (e.g., Brick, Concrete, Steel)")
        layout.addWidget(self.material_name_edit)
        
        # Description
        layout.addWidget(QLabel("Description:"))
        self.material_description_edit = QTextEdit()
        self.material_description_edit.setMaximumHeight(100)
        self.material_description_edit.setPlaceholderText("Enter material description...")
        layout.addWidget(self.material_description_edit)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_updated_data(self):
        """Get the updated master list data with new material"""
        material_name = self.material_name_edit.text().strip()
        if not material_name:
            return self.master_list_data
        
        # Create material data
        material_data = {
            'defects': [],  # Empty defects list - can be added later
            'description': self.material_description_edit.toPlainText()
        }
        
        # Update the master list copy
        if 'materials' not in self.master_list_data:
            self.master_list_data['materials'] = {}
        
        self.master_list_data['materials'][material_name] = material_data
        
        return self.master_list_data
    
    def accept(self):
        """Validate and accept the dialog"""
        material_name = self.material_name_edit.text().strip()
        if not material_name:
            QMessageBox.warning(self, "Validation Error", "Please enter a material name.")
            return
        
        # Check if material already exists
        if material_name in self.master_list_data.get('materials', {}):
            reply = QMessageBox.question(
                self, "Material Exists",
                f"Material '{material_name}' already exists. Do you want to update it?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        super().accept()

class MaterialDefectsEditDialog(QDialog):
    """Dialog for editing defects associated with a specific material"""
    
    def __init__(self, material_name, master_list_data, template_mode=False, selected_defects=None, parent=None):
        super().__init__(parent)
        self.material_name = material_name
        self.master_list_data = master_list_data or {}
        self.template_mode = template_mode
        self.selected_defects = selected_defects or []
        
        if template_mode:
            self.setWindowTitle(f"Select Defects for Template Material: {material_name}")
        else:
            self.setWindowTitle(f"Edit Defects for Material: {material_name}")
        
        self.setFixedSize(700, 600)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        if self.template_mode:
            title_label = QLabel(f"📋 Select Defects for Template Material: {self.material_name}")
            instructions = QLabel("Select which defects from the master list to include in this template:")
        else:
            title_label = QLabel(f"🏗️ {self.material_name} - Defects Management")
            instructions = QLabel("Check the defects that can occur with this material:")
        
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title_label)
        
        # Instructions
        instructions.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(instructions)
        
        # Add headers back
        headers_widget = QWidget()
        headers_layout = QHBoxLayout(headers_widget)
        headers_layout.setContentsMargins(10, 5, 10, 5)
        
        defect_header = QLabel("Defect")
        defect_header.setFont(QFont("Arial", 13, QFont.Bold))
        defect_header.setStyleSheet("background-color: #f8f9fa; padding: 8px; border: 1px solid #dee2e6;")
        headers_layout.addWidget(defect_header, 3)
        
        severity_header = QLabel("Severity")
        severity_header.setFont(QFont("Arial", 13, QFont.Bold))
        severity_header.setStyleSheet("background-color: #f8f9fa; padding: 8px; border: 1px solid #dee2e6;")
        headers_layout.addWidget(severity_header, 1)
        
        description_header = QLabel("Description")
        description_header.setFont(QFont("Arial", 13, QFont.Bold))
        description_header.setStyleSheet("background-color: #f8f9fa; padding: 8px; border: 1px solid #dee2e6;")
        headers_layout.addWidget(description_header, 2)
        
        layout.addWidget(headers_widget)
        
        # Create list widget for defect management
        self.defects_list = QListWidget()
        
        # Set larger font for better readability
        font = QFont("Arial", 12)
        self.defects_list.setFont(font)
        
        # Disable selection highlighting and set item height
        self.defects_list.setStyleSheet("""
            QListWidget {
                outline: 0;
                background-color: white;
            }
            QListWidget::item {
                height: 40px;
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
                background-color: white;
            }
            QListWidget::item:selected {
                background-color: white;
                color: black;
            }
            QListWidget::item:hover {
                background-color: white;
            }
        """)
        
        # Disable selection to prevent color changes
        self.defects_list.setSelectionMode(QAbstractItemView.NoSelection)
        
        # Populate with defects from master list that are associated with this material
        master_materials = self.master_list_data.get('materials', {})
        material_defects = master_materials.get(self.material_name, {}).get('defects', [])
        
        # Store checkbox widgets for easy access
        self.checkbox_widgets = {}
        
        for defect_name in material_defects:
            # Create custom widget for each defect row
            defect_widget = self.create_defect_row_widget(defect_name)
            
            # Create list item
            item = QListWidgetItem()
            item.setSizeHint(defect_widget.sizeHint())
            self.defects_list.addItem(item)
            self.defects_list.setItemWidget(item, defect_widget)
        
        layout.addWidget(self.defects_list)
        
        # Add/Edit defect buttons (only in master list mode)
        if not self.template_mode:
            buttons_layout = QHBoxLayout()
            
            add_defect_btn = QPushButton("+ Add New Defect")
            add_defect_btn.clicked.connect(self.add_defect)
            buttons_layout.addWidget(add_defect_btn)
            
            edit_defect_btn = QPushButton("Edit Selected Defect")
            edit_defect_btn.clicked.connect(self.edit_defect)
            buttons_layout.addWidget(edit_defect_btn)
            
            delete_defect_btn = QPushButton("Delete Selected Defect")
            delete_defect_btn.clicked.connect(self.delete_defect)
            buttons_layout.addWidget(delete_defect_btn)
            
            buttons_layout.addStretch()
            
            # Multi-selection buttons
            edit_checked_btn = QPushButton("Edit Checked")
            edit_checked_btn.clicked.connect(self.edit_selected_defects)
            buttons_layout.addWidget(edit_checked_btn)
            
            delete_checked_btn = QPushButton("Delete Checked")
            delete_checked_btn.clicked.connect(self.delete_selected_defects)
            buttons_layout.addWidget(delete_checked_btn)
            
            layout.addLayout(buttons_layout)
        else:
            # Add select/clear all buttons for template mode
            buttons_layout = QHBoxLayout()
            
            select_all_btn = QPushButton("Select All")
            select_all_btn.clicked.connect(self.select_all_defects)
            buttons_layout.addWidget(select_all_btn)
            
            clear_all_btn = QPushButton("Clear All")
            clear_all_btn.clicked.connect(self.clear_all_defects)
            buttons_layout.addWidget(clear_all_btn)
            
            buttons_layout.addStretch()
            layout.addLayout(buttons_layout)
        
        # Info label
        if self.template_mode:
            info_label = QLabel("✓ Check defects to include them in this template material.")
        else:
            info_label = QLabel("✓ Check defects to associate them with this material. You can add new defects specific to this material.")
        
        info_label.setStyleSheet("color: #666; font-size: 10px; font-style: italic; margin-top: 10px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Dialog buttons
        dialog_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        dialog_buttons.accepted.connect(self.accept)
        dialog_buttons.rejected.connect(self.reject)
        layout.addWidget(dialog_buttons)
    
    def create_defect_row_widget(self, defect_name):
        """Create a custom widget for each defect row with checkbox and labels"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Checkbox
        checkbox = QCheckBox()
        checkbox.setFixedSize(20, 20)
        if defect_name in self.selected_defects:
            checkbox.setChecked(True)
        
        # Store checkbox reference
        self.checkbox_widgets[defect_name] = checkbox
        layout.addWidget(checkbox)
        
        # Defect name label
        defect_label = QLabel(defect_name)
        defect_label.setFont(QFont("Arial", 11))
        layout.addWidget(defect_label, 3)
        
        # Severity label
        severity_label = QLabel("Medium" if not self.template_mode else "")
        severity_label.setFont(QFont("Arial", 11))
        severity_label.setStyleSheet("color: #666;")
        layout.addWidget(severity_label, 1)
        
        # Description label
        description_label = QLabel("No description" if not self.template_mode else "")
        description_label.setFont(QFont("Arial", 11))
        description_label.setStyleSheet("color: #666;")
        layout.addWidget(description_label, 2)
        
        widget.setFixedHeight(40)
        return widget
    

    
    def add_defect(self):
        """Add a new defect specific to this material"""
        text, ok = QInputDialog.getText(self, "Add Defect", f"Enter new defect name for {self.material_name}:")
        
        if ok and text.strip():
            defect_name = text.strip()
            
            # Check if defect already exists for this material
            master_materials = self.master_list_data.get('materials', {})
            if self.material_name in master_materials:
                existing_defects = master_materials[self.material_name].get('defects', [])
                if defect_name in existing_defects:
                    QMessageBox.warning(self, "Duplicate", f"Defect '{defect_name}' already exists for this material.")
                    return
                
                # Add to this material's defects list
                existing_defects.append(defect_name)
                master_materials[self.material_name]['defects'] = existing_defects
            else:
                # Create new material entry
                self.master_list_data['materials'][self.material_name] = {
                    'defects': [defect_name],
                    'description': ''
                }
            
            # Refresh the list
            self.refresh_list()
    
    def edit_defect(self):
        """Edit the selected defect"""
        # For now, just use the bulk edit functionality or select the first defect
        if not self.checkbox_widgets:
            QMessageBox.information(self, "No Defects", "No defects available to edit.")
            return
        
        # Get first defect name for editing (you can enhance this to show a selection dialog)
        first_defect = list(self.checkbox_widgets.keys())[0]
        old_defect_name = first_defect
        text, ok = QInputDialog.getText(self, "Edit Defect", f"Edit defect name:", text=old_defect_name)
        
        if ok and text.strip():
            new_defect_name = text.strip()
            
            if new_defect_name != old_defect_name:
                # Update the defect name in the material's defects list
                master_materials = self.master_list_data.get('materials', {})
                if self.material_name in master_materials:
                    defects_list = master_materials[self.material_name].get('defects', [])
                    if old_defect_name in defects_list:
                        # Replace old name with new name
                        index = defects_list.index(old_defect_name)
                        defects_list[index] = new_defect_name
                        master_materials[self.material_name]['defects'] = defects_list
                
                # Refresh the list
                self.refresh_list()
    
    def delete_defect(self):
        """Delete the selected defect"""
        # For now, just use the bulk delete functionality or select the first defect
        if not self.checkbox_widgets:
            QMessageBox.information(self, "No Defects", "No defects available to delete.")
            return
        
        # Get first defect name for deletion (you can enhance this to show a selection dialog)
        first_defect = list(self.checkbox_widgets.keys())[0]
        defect_name = first_defect
        
        reply = QMessageBox.question(
            self, "Delete Defect",
            f"Are you sure you want to delete defect '{defect_name}' from {self.material_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove from this material's defects list
            master_materials = self.master_list_data.get('materials', {})
            if self.material_name in master_materials:
                defects_list = master_materials[self.material_name].get('defects', [])
                if defect_name in defects_list:
                    defects_list.remove(defect_name)
                    master_materials[self.material_name]['defects'] = defects_list
            
            # Refresh the list
            self.refresh_list()
    
    def refresh_list(self):
        """Refresh the defects list"""
        # Save current selections
        selected_defects = []
        for defect_name, checkbox in self.checkbox_widgets.items():
            if checkbox.isChecked():
                selected_defects.append(defect_name)
        
        # Clear and repopulate
        self.defects_list.clear()
        self.checkbox_widgets.clear()
        
        # Get updated data
        master_materials = self.master_list_data.get('materials', {})
        material_defects = master_materials.get(self.material_name, {}).get('defects', [])
        
        for defect_name in material_defects:
            # Create custom widget for each defect row
            defect_widget = self.create_defect_row_widget(defect_name)
            
            # Restore selection
            if defect_name in selected_defects:
                self.checkbox_widgets[defect_name].setChecked(True)
            
            # Create list item
            item = QListWidgetItem()
            item.setSizeHint(defect_widget.sizeHint())
            self.defects_list.addItem(item)
            self.defects_list.setItemWidget(item, defect_widget)
    
    def select_all_defects(self):
        """Select all defects (template mode only)"""
        for checkbox in self.checkbox_widgets.values():
            checkbox.setChecked(True)
    
    def clear_all_defects(self):
        """Clear all defect selections (template mode only)"""
        for checkbox in self.checkbox_widgets.values():
            checkbox.setChecked(False)
    
    def get_selected_defects(self):
        """Get list of selected defects (template mode)"""
        selected_defects = []
        for defect_name, checkbox in self.checkbox_widgets.items():
            if checkbox.isChecked():
                selected_defects.append(defect_name)
        return selected_defects
    
    def get_data(self):
        """Get the updated material data with all defects"""
        if self.template_mode:
            return self.get_selected_defects()
        
        # For master list mode, return all defects that exist for this material
        # The checkboxes are for selecting items to edit/delete, not for filtering which defects to keep
        master_materials = self.master_list_data.get('materials', {})
        if self.material_name in master_materials:
            material_data = master_materials[self.material_name].copy()
            # Return the complete material data - defects list should remain intact
            return material_data
        
        # If material doesn't exist, return basic structure
        return {'defects': [], 'description': ''}
    

    
    def edit_selected_defects(self):
        """Edit all checked defects"""
        checked_defects = []
        for defect_name, checkbox in self.checkbox_widgets.items():
            if checkbox.isChecked():
                checked_defects.append(defect_name)
        
        if not checked_defects:
            QMessageBox.information(self, "No Selection", "Please check some defects to edit.")
            return
        
        # For now, just show which defects are selected
        defect_list = "\n".join(checked_defects)
        QMessageBox.information(self, "Edit Multiple Defects", 
                              f"You have selected {len(checked_defects)} defects:\n\n{defect_list}\n\nEdit functionality coming soon!")
    
    def delete_selected_defects(self):
        """Delete all checked defects"""
        checked_defects = []
        for defect_name, checkbox in self.checkbox_widgets.items():
            if checkbox.isChecked():
                checked_defects.append(defect_name)
        
        if not checked_defects:
            QMessageBox.information(self, "No Selection", "Please check some defects to delete.")
            return
        
        defect_list = "\n".join(checked_defects)
        reply = QMessageBox.question(
            self, "Delete Multiple Defects",
            f"Are you sure you want to delete these {len(checked_defects)} defects from {self.material_name}?\n\n{defect_list}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove checked defects from master list
            master_materials = self.master_list_data.get('materials', {})
            if self.material_name in master_materials:
                defects_list = master_materials[self.material_name].get('defects', [])
                for defect_name in checked_defects:
                    if defect_name in defects_list:
                        defects_list.remove(defect_name)
                master_materials[self.material_name]['defects'] = defects_list
            
            # Refresh the list
            self.refresh_list()

class TemplateCard(QFrame):
    """Card widget for displaying and managing templates - similar to ProjectCard"""
    template_selected = Signal(str)  # Signal when template is selected
    template_deleted = Signal(str)   # Signal when template is deleted
    template_clicked = Signal(str, dict)  # Signal when template card is clicked for overview
    
    def __init__(self, template_name, template_data=None, parent=None):
        super().__init__(parent)
        self.template_name = template_name
        self.template_data = template_data or {}
        
        # Set fixed size similar to ProjectCard
        self.setFixedSize(260, 200)
        self.setStyleSheet("""
            QFrame {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
                margin: 4px;
                cursor: pointer;
            }
            QFrame:hover {
                border-color: #2196F3;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                background-color: #f8f9fa;
            }
        """)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        # Header with template name
        name_label = QLabel(self.template_name)
        name_label.setFont(QFont("Arial", 14, QFont.Bold))
        name_label.setStyleSheet("color: #333; margin-bottom: 8px;")
        name_label.setWordWrap(True)
        layout.addWidget(name_label)
        
        # Template stats with icons
        statuses_count = len(self.template_data.get('statuses', {}))
        materials_count = len(self.template_data.get('materials', {}))
        defects_count = len(self.template_data.get('defects', {}))
        
        # Stats container
        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(4)
        
        # Status count
        status_label = QLabel(f"📊 {statuses_count} Statuses")
        status_label.setStyleSheet("color: #666; font-size: 12px;")
        stats_layout.addWidget(status_label)
        
        # Materials count
        materials_label = QLabel(f"🏗️ {materials_count} Materials")
        materials_label.setStyleSheet("color: #666; font-size: 12px;")
        stats_layout.addWidget(materials_label)
        
        # Defects count
        defects_label = QLabel(f"⚠️ {defects_count} Defects")
        defects_label.setStyleSheet("color: #666; font-size: 12px;")
        stats_layout.addWidget(defects_label)
        
        layout.addWidget(stats_widget)
        layout.addStretch()
        
        # Bottom action buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)
        
        # Select button (primary action)
        select_btn = QPushButton("Select")
        select_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """)
        select_btn.clicked.connect(lambda: self.template_selected.emit(self.template_name))
        buttons_layout.addWidget(select_btn)
        
        # Delete button (secondary action)
        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:pressed {
                background-color: #c62828;
            }
        """)
        delete_btn.clicked.connect(self.delete_template)
        buttons_layout.addWidget(delete_btn)
        
        layout.addLayout(buttons_layout)
    
    def mousePressEvent(self, event):
        """Handle click on template card"""
        if event.button() == Qt.LeftButton:
            # Check if click was on a button
            widget_at_pos = self.childAt(event.pos())
            if widget_at_pos and isinstance(widget_at_pos, QPushButton):
                # Let the button handle it
                super().mousePressEvent(event)
            else:
                # Click on card itself - open template overview
                self.template_clicked.emit(self.template_name, self.template_data)
        super().mousePressEvent(event)
    
    def delete_template(self):
        reply = QMessageBox.question(
            self, "Delete Template", 
            f"Are you sure you want to delete template '{self.template_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.template_deleted.emit(self.template_name)

class TemplatesPage(QWidget):
    back_to_home = Signal()
    open_template_overview = Signal(str, dict)  # template_name, template_data
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.templates_dir = os.path.abspath(os.path.join(
            os.path.dirname(__file__), '..', '..', 'templates'
        ))
        os.makedirs(self.templates_dir, exist_ok=True)
        
        self.setup_ui()
        self.load_master_list()
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        back_btn = QPushButton("← Back to Home")
        back_btn.clicked.connect(self.back_to_home.emit)
        header_layout.addWidget(back_btn)
        
        header_layout.addStretch()
        
        title_label = QLabel("Templates Management")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Only keep Save Template button
        save_template_btn = QPushButton("💾 Save Template")
        save_template_btn.clicked.connect(self.save_current_template)
        header_layout.addWidget(save_template_btn)
        
        main_layout.addLayout(header_layout)
        
        # Main tabs for Templates vs Master List
        self.main_tab_widget = QTabWidget()
        
        # Templates tab (existing functionality)
        self.templates_tab = self.create_templates_tab()
        self.main_tab_widget.addTab(self.templates_tab, "Templates")
        
        # Master List tab (new functionality)
        self.master_list_tab = self.create_master_list_tab()
        self.main_tab_widget.addTab(self.master_list_tab, "Master List")
        
        main_layout.addWidget(self.main_tab_widget)
    

    

    

    
    def refresh_template_cards_display(self):
        """Refresh the template cards display in grid layout"""
        # Clear existing cards
        while self.templates_grid_layout.count():
            item = self.templates_grid_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        # Similar to homepage grid calculation
        grid_width = self.templates_grid_layout.geometry().width() or 800  # Default width
        card_width = 260 + 24  # Card width plus spacing
        columns = max(1, (grid_width // card_width))
        
        # Start with index 0
        idx = 0
        
        # Add "New Template" card first
        new_card = NewTemplateCard()
        new_card.create_template.connect(self.create_new_template)
        row = idx // columns
        col = idx % columns
        self.templates_grid_layout.addWidget(new_card, row, col)
        idx += 1
        
        # Add existing template cards
        available_templates = self.get_available_templates()
        for template_name in available_templates:
            template_file = os.path.join(self.templates_dir, f"{template_name}.json")
            template_data = {}
            if os.path.exists(template_file):
                try:
                    with open(template_file, 'r') as f:
                        template_data = json.load(f)
                except:
                    pass
            
            card = TemplateCard(template_name, template_data)
            card.template_selected.connect(self.select_template)
            card.template_deleted.connect(self.delete_template)
            card.template_clicked.connect(self.open_template_overview_page)
            
            row = idx // columns
            col = idx % columns
            self.templates_grid_layout.addWidget(card, row, col)
            idx += 1
    
    def get_available_templates(self):
        """Get list of available templates"""
        templates = []
        if os.path.exists(self.templates_dir):
            for filename in os.listdir(self.templates_dir):
                if filename.endswith('.json') and filename != 'master_list.json':
                    templates.append(filename[:-5])  # Remove .json extension
        return templates
    

    
    def delete_template(self, template_name):
        """Delete a template"""
        template_file = os.path.join(self.templates_dir, f"{template_name}.json")
        if os.path.exists(template_file):
            try:
                os.remove(template_file)
                self.refresh_template_cards_display()
                QMessageBox.information(self, "Success", f"Template '{template_name}' deleted successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete template: {e}")
    
    def showEvent(self, event):
        """Refresh displays when page is shown"""
        super().showEvent(event)
        # Reload master list to get latest updates
        self.load_master_list()
        if hasattr(self, 'templates_grid_layout'):
            self.refresh_template_cards_display()
        if hasattr(self, 'master_list_data'):
            self.refresh_all_master_displays()
    
    def resizeEvent(self, event):
        """Refresh grid when window is resized"""
        super().resizeEvent(event)
        if hasattr(self, 'templates_grid_layout'):
            self.refresh_template_cards_display()
    

    
    def save_current_template(self):
        if not hasattr(self, 'master_list_data') or not self.master_list_data:
            QMessageBox.warning(self, "Warning", "No master list data to save.")
            return
        
        master_list_file = os.path.join(self.templates_dir, "master_list.json")
        
        try:
            with open(master_list_file, 'w') as f:
                json.dump(self.master_list_data, f, indent=2)
            
            QMessageBox.information(self, "Success", "Master list saved successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save master list: {e}")
    
    def create_new_template(self):
        """Create a new template"""
        name, ok = QInputDialog.getText(self, "New Template", "Template name:")
        if ok and name:
            # Create empty template structure
            template_data = {
                'statuses': {},
                'materials': {},
                'defects': {}
            }
            
            # Save the new template
            template_file = os.path.join(self.templates_dir, f"{name}.json")
            try:
                with open(template_file, 'w') as f:
                    json.dump(template_data, f, indent=2)
                
                QMessageBox.information(self, "Success", f"Template '{name}' created successfully!")
                
                # Refresh the template cards display
                self.refresh_template_cards_display()
                
                # Open the new template for editing  
                self.open_template_overview.emit(name, template_data)
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create template: {e}")
    
    def select_template(self, template_name):
        """Select and activate a template"""
        QMessageBox.information(self, "Template Selected", f"Template '{template_name}' selected!")
        # You can add additional logic here if needed, such as:
        # - Setting it as the active template for new projects
        # - Loading its data into the current editing context
        # - etc.
    
    def create_templates_tab(self):
        """Create the templates management tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Search box (for future enhancement)
        controls_layout = QHBoxLayout()
        controls_layout.addStretch()
        
        search_box = QLineEdit()
        search_box.setPlaceholderText("Search templates")
        search_box.setMaximumWidth(200)
        controls_layout.addWidget(search_box)
        
        layout.addLayout(controls_layout)
        
        # Template grid area with margins (similar to homepage)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        grid_outer = QWidget()
        grid_outer_layout = QHBoxLayout(grid_outer)
        grid_outer_layout.setContentsMargins(40, 0, 40, 0)  # 40px margin left/right
        
        grid_container = QWidget()
        self.templates_grid_layout = QGridLayout(grid_container)
        self.templates_grid_layout.setSpacing(24)
        self.templates_grid_layout.setContentsMargins(0, 0, 0, 0)
        self.templates_grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        grid_container.setLayout(self.templates_grid_layout)
        
        grid_outer_layout.addWidget(grid_container)
        scroll.setWidget(grid_outer)
        
        layout.addWidget(scroll, 1)
        
        return tab
    
    def create_master_list_tab(self):
        """Create the master list management tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Sub-tabs for different categories in master list
        self.master_tab_widget = QTabWidget()
        
        # Statuses master list
        self.master_statuses_tab = self.create_master_category_tab('status')
        self.master_tab_widget.addTab(self.master_statuses_tab, "Statuses")
        
        # Materials master list (defects are managed through materials)
        self.master_materials_tab = self.create_master_category_tab('material')
        self.master_tab_widget.addTab(self.master_materials_tab, "Materials")
        
        layout.addWidget(self.master_tab_widget)
        return tab
    
    def create_master_category_tab(self, category_type):
        """Create a master list tab for a specific category"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Add button
        add_btn = QPushButton(f"+ Add {category_type.title()}")
        add_btn.clicked.connect(lambda: self.add_master_item(category_type))
        layout.addWidget(add_btn)
        
        # Scroll area for master items
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        scroll_widget = QWidget()
        grid_layout = QGridLayout(scroll_widget)
        grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Store references
        setattr(tab, 'grid_layout', grid_layout)
        setattr(tab, 'scroll_widget', scroll_widget)
        
        return tab
    
    def load_master_list(self):
        """Load the master list of all items"""
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
            self.save_master_list()  # Create default file
    
    def save_master_list(self):
        """Save the master list to file"""
        master_file = os.path.join(self.templates_dir, 'master_list.json')
        try:
            with open(master_file, 'w', encoding='utf-8') as f:
                json.dump(self.master_list_data, f, indent=2)
        except Exception as e:
            print(f"[ERROR] Failed to save master list: {e}")
    
    def add_master_item(self, item_type):
        """Add a new item to the master list"""
        if item_type == 'material':
            # For materials, use the specialized dialog to manage defects
            self.add_material_with_defects()
        elif item_type == 'status':
            # For statuses, use simple text input
            name, ok = QInputDialog.getText(self, "Add Status", "Status name:")
            if ok and name:
                default_data = {'color': '#cccccc', 'description': ''}
                self.master_list_data['statuses'][name] = default_data
                self.save_master_list()
                self.refresh_master_category_display('status')
    
    def add_material_with_defects(self):
        """Add a new material - simple dialog like defects"""
        dialog = MaterialAndDefectsDialog(self.master_list_data, self)
        if dialog.exec():
            # Get the updated data
            updated_data = dialog.get_updated_data()
            
            # Update master list with new material and any new defects
            self.master_list_data.update(updated_data)
            
            # Save the master list
            self.save_master_list()
            
            # Refresh both displays since we might have added defects too
            self.refresh_master_category_display('material')
            
            QMessageBox.information(self, "Success", "Material and defects added successfully!")
    
    def refresh_master_category_display(self, category_type):
        """Refresh the display for a master category"""
        # Get the appropriate tab
        if category_type == 'status':
            tab = self.master_statuses_tab
            data_key = 'statuses'
        elif category_type == 'material':
            tab = self.master_materials_tab
            data_key = 'materials'
        else:
            return  # Only handle status and material categories
        
        # Clear existing cards
        grid_layout = tab.grid_layout
        while grid_layout.count():
            item = grid_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        # Add cards for master list data
        items = self.master_list_data.get(data_key, {})
        
        row, col = 0, 0
        max_cols = 3
        
        for item_name, item_data in items.items():
            card = EditableItemCard(category_type, item_name, item_data)
            card.item_updated.connect(lambda name, data, key=data_key: self.update_master_item(key, name, data))
            card.item_deleted.connect(lambda name, key=data_key: self.delete_master_item(key, name))
            
            grid_layout.addWidget(card, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    def update_master_item(self, data_key, item_name, item_data):
        """Update an item in the master list"""
        self.master_list_data[data_key][item_name] = item_data
        self.save_master_list()
    
    def delete_master_item(self, data_key, item_name):
        """Delete an item from the master list"""
        self.master_list_data[data_key].pop(item_name, None)
        self.save_master_list()
        # Refresh the display for the affected category
        category_type = data_key[:-1] if data_key.endswith('s') else data_key
        if category_type == 'statuse':  # Fix for 'statuses'
            category_type = 'status'
        
        # Only refresh if it's a category we still display
        if category_type in ['status', 'material']:
            self.refresh_master_category_display(category_type)
    
    def refresh_all_master_displays(self):
        """Refresh all master list displays"""
        self.refresh_master_category_display('status')
        self.refresh_master_category_display('material')
    
    def open_template_overview_page(self, template_name, template_data):
        """Open the template overview page"""
        self.open_template_overview.emit(template_name, template_data)