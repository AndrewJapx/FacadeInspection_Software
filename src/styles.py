FINDING_CARD_STYLE = """
background: #fff;
border: 1px solid #ddd;
border-radius: 6px;
padding: 8px;
"""

FINDING_CARD_TITLE_STYLE = """
font-weight: bold;
font-size: 15px;
"""

FINDING_CARD_META_STYLE = """
color: #888;
font-size: 12px;
"""
SIDEBAR_STYLE = """
background-color: #fff;
border-right: 2px solid #0d47a1;
"""

HEADER_STYLE = """
font-size: 15px;
font-weight: bold;
background: #fff;
border: 1px solid #bbb;
border-radius: 4px;
padding: 4px 12px;
max-width: 350px;
"""

ADD_ELEVATION_BTN_STYLE = """
border: 1px solid #bbb;
background: #fff;
padding: 6px 0;
"""

ELEVATION_CARD_STYLE = """
background: #fff;
border: 1.5px solid #222;
border-radius: 0px;
"""

ADD_ELEVATION_CARD_STYLE = """
border: 2px dotted #bbb;
background: #fafbfc;
border-radius: 8px;
"""

DEFECT_LIST_STYLE = """
background: #fffde7;
border: 2px solid #fbc02d;
border-radius: 4px;
"""

LOGIN_WINDOW_STYLESHEET = """
QWidget {
    background: #f7f7f7;
}
QLabel#PhotoLabel {
    border-radius: 40px;
    background: #cccccc;
    min-width: 80px;
    min-height: 80px;
    max-width: 80px;
    max-height: 80px;
}
QLineEdit {
    padding: 6px;
    border: 1px solid #bbb;
    border-radius: 4px;
    background: #fff;
}
QPushButton {
    background: #1976d2;
    color: #fff;
    border-radius: 4px;
    padding: 8px 0;
    font-weight: bold;
}
QPushButton:hover {
    background: #1565c0;
}
"""

PROJECT_CARD_STYLE = """
QFrame#ProjectCard {
    background: #f3f4f6;
    border: 2px solid #b0b3b8;
    border-radius: 10px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
QLabel#ProjectTitle {
    font-weight: bold;
    font-size: 16px;
}
QLabel#ProjectSubtitle {
    color: #888;
    font-size: 13px;
}
QLabel#ProjectMembers {
    font-size: 12px;
    color: #888;
}
"""

FOLDER_CONTAINER_STYLE = """
    border: none;
    border-radius: 6px;
    background: #fff;
"""

# Findings Widget Styles
FINDINGS_COLUMN_CONTAINER_STYLE = """
QWidget {
    background-color: #f8f9fa;
    border-radius: 8px;
    margin: 4px;
}
"""

def get_findings_column_header_style(status_color):
    """Get the column header style with the specified status color"""
    return f"""
font-weight: bold; 
font-size: 15px; 
color: white;
padding: 8px;
background-color: {status_color};
border-radius: 4px;
margin-bottom: 8px;
"""

FINDINGS_SCROLL_AREA_STYLE = """
QScrollArea { 
    border: none; 
    background-color: transparent; 
}
"""

FINDINGS_NEW_TASK_BTN_STYLE = """
QPushButton {
    color: #888; 
    background: none; 
    border: 2px dashed #ccc; 
    border-radius: 4px;
    font-size: 14px;
    padding: 8px;
    margin-top: 8px;
}
QPushButton:hover {
    border-color: #999;
    color: #666;
}
"""

def get_findings_card_style(status_color):
    """Get the findings card style with the specified status color"""
    return f"""
QFrame {{
    background-color: white;
    border: 1px solid #dee2e6;
    border-left: 4px solid {status_color};
    border-radius: 6px;
    padding: 4px;
    margin: 2px;
}}
QFrame:hover {{
    border-color: {status_color};
    border-left: 4px solid {status_color};
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}}
"""

def get_findings_status_label_style(status_color):
    """Get the status label style with the specified status color"""
    return f"""
background-color: {status_color};
color: white;
padding: 2px 6px;
border-radius: 3px;
font-size: 10px;
font-weight: bold;
margin-bottom: 4px;
"""

# Template Management Styles
DEFECTS_TREE_STYLE = """
QTreeWidget {
    font-size: 12px;
    font-family: Arial;
    outline: 0;
}
QTreeWidget::item {
    height: 35px;
    padding: 8px;
    border-bottom: 1px solid #f0f0f0;
}
QTreeWidget::item:hover {
    background-color: #f5f5f5;
}
QTreeWidget::branch {
    background: transparent;
}
QHeaderView::section {
    background-color: #f8f9fa;
    padding: 8px;
    border: 1px solid #dee2e6;
    font-weight: bold;
    font-size: 13px;
    height: 35px;
}
"""

# Editable Item Card Styles
EDITABLE_ITEM_CARD_STYLE = """
QFrame {
    border: 1px solid #ddd;
    border-radius: 8px;
    background-color: white;
    margin: 4px;
}
QFrame:hover {
    border-color: #2196F3;
    background-color: #f8f9fa;
}
"""

EDIT_DEFECTS_BUTTON_STYLE = """
QPushButton {
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 10px;
    font-weight: bold;
    min-height: 25px;
    max-height: 30px;
}
QPushButton:hover {
    background-color: #45a049;
}
"""

MATERIAL_DESCRIPTION_STYLE = """
color: #666; 
font-size: 10px;
"""

DEFECTS_COUNT_STYLE = """
color: #2196F3; 
font-size: 10px; 
font-weight: bold;
"""

# Material and Defects Dialog Styles
MATERIAL_DIALOG_TITLE_STYLE = """
QLabel {
    color: #2c3e50;
    font-size: 18px;
    font-weight: bold;
    margin: 10px 0;
    padding: 10px;
    background-color: #ecf0f1;
    border-radius: 8px;
    border-left: 4px solid #3498db;
}
"""

MATERIAL_INFO_SECTION_STYLE = """
QFrame {
    border: 2px solid #3498db;
    border-radius: 8px;
    padding: 15px;
    margin: 5px;
    background-color: #fbfcfd;
}
"""

MATERIAL_INFO_HEADER_STYLE = """
QLabel {
    color: #2980b9;
    font-size: 14px;
    font-weight: bold;
    border: none;
    margin-bottom: 10px;
    padding: 5px 0;
}
"""

MATERIAL_INFO_INPUT_STYLE = """
QLineEdit, QTextEdit {
    border: 2px solid #bdc3c7;
    border-radius: 6px;
    padding: 12px 15px;
    font-size: 14px;
    background-color: white;
    margin: 5px 0 15px 0;
    min-height: 25px;
}
QLineEdit:focus, QTextEdit:focus {
    border-color: #3498db;
    background-color: #f8fbff;
}
QLineEdit::placeholder, QTextEdit::placeholder {
    color: #95a5a6;
    font-style: italic;
}
"""

MATERIAL_INFO_LABEL_STYLE = """
QLabel {
    color: #34495e;
    font-size: 14px;
    font-weight: 600;
    margin: 15px 0 8px 0;
    border: none;
}
"""

DEFECTS_SECTION_STYLE = """
QFrame {
    border: 2px solid #f39c12;
    border-radius: 8px;
    padding: 15px;
    margin: 5px;
    background-color: #fffbf0;
}
"""

DEFECTS_HEADER_STYLE = """
QLabel {
    color: #e67e22;
    font-size: 14px;
    font-weight: bold;
    border: none;
    margin-bottom: 10px;
    padding: 5px 0;
}
"""

DEFECTS_LIST_WIDGET_STYLE = """
QListWidget {
    border: 2px solid #f1c40f;
    border-radius: 8px;
    background-color: white;
    padding: 8px;
    font-size: 13px;
    min-height: 120px;
    max-height: 160px;
}
QListWidget::item {
    padding: 8px 12px;
    border-bottom: 1px solid #ecf0f1;
    border-radius: 4px;
    margin: 2px;
    min-height: 20px;
}
QListWidget::item:hover {
    background-color: #fff3cd;
}
QListWidget::item:selected {
    background-color: #ffeaa7;
    color: #2d3436;
}
"""

DEFECTS_INSTRUCTIONS_STYLE = """
QLabel {
    color: #7f8c8d;
    font-size: 12px;
    font-style: italic;
    border: none;
    margin: 8px 0 15px 0;
    padding: 10px;
    background-color: #fef9e7;
    border-radius: 4px;
    border-left: 3px solid #f1c40f;
}
"""

ADD_DEFECT_BUTTON_STYLE = """
QPushButton {
    background-color: #27ae60;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 12px 20px;
    font-weight: bold;
    font-size: 13px;
    min-height: 40px;
    margin: 8px 5px;
}
QPushButton:hover {
    background-color: #229954;
    transform: translateY(-1px);
}
QPushButton:pressed {
    background-color: #1e8449;
    transform: translateY(0px);
}
"""

REMOVE_DEFECT_BUTTON_STYLE = """
QPushButton {
    background-color: #e74c3c;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 12px 20px;
    font-weight: bold;
    font-size: 13px;
    min-height: 40px;
    margin: 8px 5px;
}
QPushButton:hover {
    background-color: #c0392b;
    transform: translateY(-1px);
}
QPushButton:pressed {
    background-color: #a93226;
    transform: translateY(0px);
}
"""

EXISTING_DEFECTS_SECTION_STYLE = """
QFrame {
    border: 2px solid #8e44ad;
    border-radius: 12px;
    padding: 20px;
    margin: 8px;
    background-color: #fdf2ff;
    min-height: 180px;
}
"""

EXISTING_DEFECTS_HEADER_STYLE = """
QLabel {
    color: #7d3c98;
    font-size: 14px;
    font-weight: bold;
    border: none;
    margin-bottom: 10px;
    padding: 5px 0;
}
"""

EXISTING_DEFECTS_SCROLL_STYLE = """
QScrollArea {
    border: 2px solid #d2b4de;
    border-radius: 8px;
    background-color: white;
    min-height: 100px;
    max-height: 140px;
}
QScrollArea > QWidget > QWidget {
    background-color: white;
}
"""

EXISTING_DEFECTS_CHECKBOX_STYLE = """
QCheckBox {
    font-size: 13px;
    color: #2c3e50;
    padding: 6px 10px;
    margin: 3px;
    min-height: 18px;
}
QCheckBox:hover {
    background-color: #f4ecf7;
    border-radius: 4px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #8e44ad;
    border-radius: 3px;
    background-color: white;
}
QCheckBox::indicator:checked {
    background-color: #8e44ad;
    border-color: #7d3c98;
}
QCheckBox::indicator:checked:hover {
    background-color: #9b59b6;
}
"""

EXISTING_DEFECTS_INSTRUCTIONS_STYLE = """
QLabel {
    color: #7f8c8d;
    font-size: 12px;
    font-style: italic;
    border: none;
    margin: 8px 0 15px 0;
    padding: 10px;
    background-color: #f8f3ff;
    border-radius: 4px;
    border-left: 3px solid #8e44ad;
}
"""