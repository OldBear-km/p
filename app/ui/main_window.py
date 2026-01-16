from __future__ import annotations

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QStackedWidget,
    QLabel,
)

from app.ui.app_context import AppContext
from app.ui.views.dashboard import DashboardView

# Заглушки/остальные экраны
from app.ui.views.transactions import TransactionsView
from app.ui.views.budgets import BudgetsView
from app.ui.views.goals import GoalsView
from app.ui.views.settings import SettingsView

# ✅ Новые экраны
from app.ui.views.categories import CategoriesView
from app.ui.views.accounts import AccountsView


class MainWindow(QMainWindow):
    def __init__(self, ctx: AppContext):
        super().__init__()
        self.ctx = ctx

        self.setWindowTitle("Finance Tracker")
        self.resize(1100, 700)

        root = QWidget()
        root_layout = QHBoxLayout()
        root.setLayout(root_layout)
        self.setCentralWidget(root)

        # ===== Sidebar =====
        sidebar = QWidget()
        sb = QVBoxLayout()
        sidebar.setLayout(sb)

        sb.addWidget(QLabel("Навигация"))

        # ✅ Кнопки навигации
        self.btn_dashboard = QPushButton("Dashboard")
        self.btn_categories = QPushButton("Категории")
        self.btn_accounts = QPushButton("Счета")
        self.btn_tx = QPushButton("Операции")
        self.btn_budgets = QPushButton("Бюджеты")
        self.btn_goals = QPushButton("Цели")
        self.btn_settings = QPushButton("Настройки")

        for b in (
            self.btn_dashboard,
            self.btn_categories,
            self.btn_accounts,
            self.btn_tx,
            self.btn_budgets,
            self.btn_goals,
            self.btn_settings,
        ):
            b.setMinimumHeight(40)
            sb.addWidget(b)

        sb.addStretch(1)

        # ===== Content (Stack) =====
        self.stack = QStackedWidget()

        # ✅ Виджеты экранов
        self.view_dashboard = DashboardView(ctx)
        self.view_categories = CategoriesView(ctx)
        self.view_accounts = AccountsView(ctx)
        self.view_tx = TransactionsView(ctx)
        self.view_budgets = BudgetsView(ctx)
        self.view_goals = GoalsView(ctx)
        self.view_settings = SettingsView(ctx)

        # ✅ Порядок добавления в stack
        self.stack.addWidget(self.view_dashboard)
        self.stack.addWidget(self.view_categories)
        self.stack.addWidget(self.view_accounts)
        self.stack.addWidget(self.view_tx)
        self.stack.addWidget(self.view_budgets)
        self.stack.addWidget(self.view_goals)
        self.stack.addWidget(self.view_settings)

        root_layout.addWidget(sidebar, 1)
        root_layout.addWidget(self.stack, 4)

        # ===== Routing =====
        self.btn_dashboard.clicked.connect(lambda: self.stack.setCurrentWidget(self.view_dashboard))
        self.btn_categories.clicked.connect(lambda: self.stack.setCurrentWidget(self.view_categories))
        self.btn_accounts.clicked.connect(lambda: self.stack.setCurrentWidget(self.view_accounts))
        self.btn_tx.clicked.connect(lambda: self.stack.setCurrentWidget(self.view_tx))
        self.btn_budgets.clicked.connect(lambda: self.stack.setCurrentWidget(self.view_budgets))
        self.btn_goals.clicked.connect(lambda: self.stack.setCurrentWidget(self.view_goals))
        self.btn_settings.clicked.connect(lambda: self.stack.setCurrentWidget(self.view_settings))
