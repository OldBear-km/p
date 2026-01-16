from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from app.ui.app_context import AppContext

class GoalsView(QWidget):
    def __init__(self, ctx: AppContext):
        super().__init__()
        self.ctx = ctx
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Goals (скоро)"))
        layout.addStretch(1)
        self.setLayout(layout)
