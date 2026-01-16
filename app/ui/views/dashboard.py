from __future__ import annotations

from datetime import date
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QFormLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
)

from app.ui.app_context import AppContext
from app.application.money import format_rub


class DashboardView(QWidget):
    def __init__(self, ctx: AppContext):
        super().__init__()
        self.ctx = ctx

        self.title = QLabel("Dashboard")
        self.subtitle = QLabel("Сводка и балансы (данные из SQLite)")

        self.refresh_btn = QPushButton("Обновить")

        # Summary box
        self.summary_box = QGroupBox("Сводка за месяц")
        self.summary_form = QFormLayout()
        self.lbl_income = QLabel("-")
        self.lbl_expense = QLabel("-")
        self.lbl_net = QLabel("-")
        self.summary_form.addRow("Доходы:", self.lbl_income)
        self.summary_form.addRow("Расходы:", self.lbl_expense)
        self.summary_form.addRow("Итог:", self.lbl_net)
        self.summary_box.setLayout(self.summary_form)

        # Balances table
        self.balances_box = QGroupBox("Балансы по счетам")
        self.balances_table = QTableWidget(0, 2)
        self.balances_table.setHorizontalHeaderLabels(["Счёт", "Баланс"])
        self.balances_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.balances_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        vb = QVBoxLayout()
        vb.addWidget(self.balances_table)
        self.balances_box.setLayout(vb)

        # Top categories
        self.top_box = QGroupBox("Топ категорий расходов за месяц")
        self.top_table = QTableWidget(0, 2)
        self.top_table.setHorizontalHeaderLabels(["Категория", "Сумма"])
        self.top_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.top_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        vb2 = QVBoxLayout()
        vb2.addWidget(self.top_table)
        self.top_box.setLayout(vb2)

        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addWidget(self.subtitle)
        layout.addWidget(self.refresh_btn)
        layout.addWidget(self.summary_box)
        layout.addWidget(self.balances_box)
        layout.addWidget(self.top_box)
        layout.addStretch(1)
        self.setLayout(layout)

        self.refresh_btn.clicked.connect(self.refresh)
        self.ctx.signals.ui_data_changed.connect(self.refresh)


        # первый рендер
        self.refresh()

    def refresh(self):
        try:
            today = date.today()
            start = date(today.year, today.month, 1)
            end = today

            with self.ctx.open_session() as session:
                rep = self.ctx.reports_repo(session)

                summary = rep.period_summary(start, end)
                self.lbl_income.setText(format_rub(summary.income_cents))
                self.lbl_expense.setText(format_rub(summary.expense_cents))
                self.lbl_net.setText(format_rub(summary.net_cents))

                balances = rep.account_balances()
                self._fill_table(self.balances_table, [(b.account_name, format_rub(b.balance_cents)) for b in balances])

                top = rep.top_expense_categories(start, end, limit=10)
                self._fill_table(self.top_table, [(c.category_name, format_rub(c.total_cents)) for c in top])
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при обновлении данных: {e}")

    @staticmethod
    def _fill_table(table: QTableWidget, rows: list[tuple[str, str]]):
        table.setRowCount(0)
        for r, (c1, c2) in enumerate(rows):
            table.insertRow(r)
            table.setItem(r, 0, QTableWidgetItem(c1))
            table.setItem(r, 1, QTableWidgetItem(c2))
        table.setSortingEnabled(False)
