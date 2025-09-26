from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from Project.NavBar.project_navbar import ProjectNavBar
from Project.master_findings import master_findings
from collections import Counter

class SidebarNav(QWidget):
    def __init__(self, findings=None, parent=None, project_name=None):
        super().__init__(parent)
        self.project_name = project_name  # Store current project name
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 16, 16, 16)
        self.layout.setSpacing(12)

        header = QLabel("Facade Inspection")
        header.setStyleSheet("font-weight: bold; font-size: 16px; min-height: 32px; max-height: 36px;")
        self.layout.addWidget(header)

        self.nav_bar = ProjectNavBar()
        self.layout.addWidget(self.nav_bar)

        # Finding List inside sidebar (now project-specific)
        from styles import DEFECT_LIST_STYLE
        self.defect_list = QWidget()
        self.defect_list.setStyleSheet(DEFECT_LIST_STYLE)
        self.defect_layout = QVBoxLayout(self.defect_list)
        self.defect_layout.setContentsMargins(8, 8, 8, 8)
        self.defect_label = QLabel("Project Finding List")
        self.defect_label.setStyleSheet("font-weight: bold;")
        self.defect_layout.addWidget(self.defect_label)

        self.layout.addWidget(self.defect_list)
        self.refresh()

    def refresh(self, project_name=None):
        """Refresh the sidebar with project-specific findings"""
        # Update project name if provided
        if project_name:
            self.project_name = project_name
        
        if not self.project_name:
            # No project selected, show empty state
            self._show_empty_state("No project selected")
            return
        
        # Remove all widgets except the label
        while self.defect_layout.count() > 1:
            item = self.defect_layout.takeAt(1)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        try:
            # Use project-specific findings instead of global master_findings
            from Project.project_findings import get_material_defect_summary
            pair_counts = get_material_defect_summary(self.project_name)
            
            print(f"[DEBUG] Sidebar refresh for {self.project_name}: found {len(pair_counts)} material/defect pairs")
            
            if not pair_counts:
                empty_label = QLabel("No findings with material and defect.")
                empty_label.setStyleSheet("color: #666; font-style: italic;")
                self.defect_layout.addWidget(empty_label)
            else:
                # Sort by count (descending) then by material/defect name
                sorted_pairs = sorted(pair_counts.items(), key=lambda x: (-x[1], x[0][0], x[0][1]))
                
                for (mat, defect), count in sorted_pairs:
                    label = f"{mat}: {defect}"
                    if count > 1:
                        label += f" ({count})"
                    defect_item = QLabel(label)
                    defect_item.setStyleSheet("padding: 4px 2px; margin: 1px; border-left: 3px solid #007bff;")
                    defect_item.setWordWrap(True)
                    self.defect_layout.addWidget(defect_item)
        
        except Exception as e:
            print(f"[ERROR] Failed to refresh sidebar for project {self.project_name}: {e}")
            import traceback
            traceback.print_exc()
            self._show_empty_state("Error loading findings")
    
    def _show_empty_state(self, message):
        """Show empty state message"""
        while self.defect_layout.count() > 1:
            item = self.defect_layout.takeAt(1)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        empty_label = QLabel(message)
        empty_label.setStyleSheet("color: #666; font-style: italic;")
        self.defect_layout.addWidget(empty_label)
    
    def set_project(self, project_name):
        """Set the current project and refresh"""
        self.project_name = project_name
        self.refresh()

# Usage: connect ElevationOverviewWidget.finding_added to SidebarNav.refresh
# Example:
# elevation_overview.finding_added.connect(sidebar_nav.refresh)