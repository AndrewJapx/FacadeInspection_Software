
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel, QFrame
from ..Elevations.finding_card import FindingCard
from ..master_findings import master_findings
from config.status import STATUS_OPTIONS


class FindingsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        from PySide6.QtWidgets import QHBoxLayout, QPushButton

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Scroll area for the kanban board
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        board = QWidget()
        board_layout = QHBoxLayout(board)
        board_layout.setSpacing(24)
        board_layout.setContentsMargins(0, 0, 0, 0)

        # Group findings by status, with an 'Other' column for unmatched statuses
        findings_by_status = {status: [] for status in STATUS_OPTIONS}
        findings_by_status['Other'] = []
        for finding in master_findings:
            status = finding.get('status', STATUS_OPTIONS[0]) or STATUS_OPTIONS[0]
            if status in findings_by_status:
                findings_by_status[status].append(finding)
            else:
                findings_by_status['Other'].append(finding)

        # Create a column for each status (plus 'Other' if needed)
        for status in list(STATUS_OPTIONS) + ['Other']:
            # Only show 'Other' if it has findings
            if status == 'Other' and not findings_by_status['Other']:
                continue
            col_widget = QWidget()
            col_layout = QVBoxLayout(col_widget)
            col_layout.setSpacing(8)
            col_layout.setContentsMargins(0, 0, 0, 0)

            # Header with status and count
            count = len(findings_by_status[status])
            header = QLabel(f"{status} ({count})")
            header.setStyleSheet("font-weight: bold; font-size: 15px; margin-bottom: 4px;")
            col_layout.addWidget(header)

            # Add cards for each finding in this status
            for finding in findings_by_status[status]:
                card = FindingCard(
                    title=finding.get('title', 'Untitled Finding'),
                    status=finding.get('status', None),
                    material=finding.get('material', ''),
                    defect=finding.get('defect', '')
                )
                col_layout.addWidget(card)

            # '+ New task' button
            new_task_btn = QPushButton("+ New task")
            new_task_btn.setStyleSheet("color: #888; background: none; border: none; font-size: 14px;")
            col_layout.addWidget(new_task_btn)
            col_layout.addStretch(1)

            board_layout.addWidget(col_widget, stretch=1)

        board_layout.addStretch(1)
        scroll.setWidget(board)
        main_layout.addWidget(scroll)
