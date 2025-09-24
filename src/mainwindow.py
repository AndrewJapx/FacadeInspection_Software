from PySide6.QtWidgets import QApplication, QMainWindow
from login.login import LoginWindow
from HomePageFolder.homepage import HomePage
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

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()  # <-- This line is required!
    sys.exit(app.exec())

if __name__ == "__main__":
    main()