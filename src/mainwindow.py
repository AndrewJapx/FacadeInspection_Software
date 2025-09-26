from PySide6.QtWidgets import QApplication, QMainWindow
from login.login import LoginWindow
from HomePageFolder.homepage import HomePage
from Templates.templates_page import TemplatesPage
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Facade Inspection Software")

        self.login_widget = LoginWindow(self)
        self.setCentralWidget(self.login_widget)

        # Connect login button to switch to homepage
        self.login_widget.login_button.clicked.connect(self.show_homepage)

    def show_homepage(self):
        self.homepage = HomePage(self)
        self.setCentralWidget(self.homepage)
    
    def show_templates(self):
        self.templates_page = TemplatesPage(self)
        self.templates_page.back_to_home.connect(self.show_homepage)
        self.templates_page.open_template_overview.connect(self.show_template_overview)
        self.setCentralWidget(self.templates_page)
    
    def show_template_overview(self, template_name, template_data):
        from Templates.template_overview_page import TemplateOverviewPage
        templates_dir = self.templates_page.templates_dir
        self.template_overview_page = TemplateOverviewPage(template_name, template_data, templates_dir, self)
        self.template_overview_page.back_to_templates.connect(self.show_templates)
        self.setCentralWidget(self.template_overview_page)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()  # <-- This line is required!
    sys.exit(app.exec())

if __name__ == "__main__":
    main()