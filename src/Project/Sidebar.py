from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from Project.NavBar.project_navbar import ProjectNavBar
from Project.master_findings import master_findings
from collections import Counter

class SidebarNav(QWidget):
    def __init__(self, findings=None, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 16, 16, 16)
        self.layout.setSpacing(12)

        header = QLabel("Facade Inspection")
        header.setStyleSheet("font-weight: bold; font-size: 16px; min-height: 32px; max-height: 36px;")
        self.layout.addWidget(header)

        self.nav_bar = ProjectNavBar()
        self.layout.addWidget(self.nav_bar)

        # Finding List inside sidebar
        from styles import DEFECT_LIST_STYLE
        self.defect_list = QWidget()
        self.defect_list.setStyleSheet(DEFECT_LIST_STYLE)
        self.defect_layout = QVBoxLayout(self.defect_list)
        self.defect_layout.setContentsMargins(8, 8, 8, 8)
        self.defect_label = QLabel("Finding List")
        self.defect_label.setStyleSheet("font-weight: bold;")
        self.defect_layout.addWidget(self.defect_label)

        self.layout.addWidget(self.defect_list)
        self.refresh()

    def refresh(self):
        # Remove all widgets except the label
        while self.defect_layout.count() > 1:
            item = self.defect_layout.takeAt(1)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        from Project.master_findings import master_findings
        from collections import Counter
        findings = master_findings
        pair_counts = Counter()
        for f in findings:
            mat = f.get('material', '')
            defect = f.get('defect', '')
            if mat and defect:
                pair_counts[(mat, defect)] += 1
        if not pair_counts:
            empty_label = QLabel("No findings with material and defect.")
            self.defect_layout.addWidget(empty_label)
        else:
            for (mat, defect), count in pair_counts.items():
                label = f"{mat}: {defect}"
                if count > 1:
                    label += f" ({count})"
                defect_item = QLabel(label)
                self.defect_layout.addWidget(defect_item)

# Usage: connect ElevationOverviewWidget.finding_added to SidebarNav.refresh
# Example:
# elevation_overview.finding_added.connect(sidebar_nav.refresh)