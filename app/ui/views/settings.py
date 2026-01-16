from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class SettingsView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Settings (скоро)"))
        layout.addStretch(1)
        self.setLayout(layout)
