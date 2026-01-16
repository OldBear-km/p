from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class GoalsView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Goals (скоро)"))
        layout.addStretch(1)
        self.setLayout(layout)
