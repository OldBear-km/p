from __future__ import annotations

from datetime import date, timedelta

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QComboBox, QLineEdit, QMessageBox, QDateEdit
)

from app.ui.app_context import AppContext
from app.application.money import format_rub
from app.domain.enums import TransactionType, CategoryKind

from app.infrastructure.repositories.budgets import BudgetsRepo
from app.infrastructure.repositories.categories import CategoriesRepo
from app.infrastructure.repositories.transactions import TransactionsRepo
from app.application.services.budgets import upsert_budget


def parse_rub_to_cents(text: str) -> int | None:
    s = text.strip().replace("₽", "").replace(" ", "").replace(",", ".")
    if not s:
        return None
    if s.count(".") > 1:
        return None
    try:
        if "." in s:
            rub_str, kop_str = s.split(".", 1)
            rub = int(rub_str) if rub_str else 0
            kop_str = (kop_str + "00")[:2]
            kop = int(kop_str)
        else:
            rub = int(s)
            kop = 0
        if rub < 0 or kop < 0:
            return None
        return rub * 100 + kop
    except ValueError:
        return None


def month_start(d: date) -> date:
    return date(d.year, d.month, 1)


def month_end(d: date) -> date:
    # последний день месяца
    if d.month == 12:
        next_m = date(d.year + 1, 1, 1)
    else:
        next_m = date(d.year, d.month + 1, 1)
    return next_m - timedelta(days=1)


class BudgetDialog(QDialog):
    def __init__(self, ctx: AppContext, parent: QWidget | None = None):
        super().__init__(parent)
        self.ctx = ctx
        self.setWindowTitle("Бюджет на месяц")
        self.setMinimumWidth(480)

        self.month_edit = QDateEdit()
        self.month_edit.setCalendarPopup(True)
        today = date.today()
        self.month_edit.setDate(QDate(today.year, today.month, 1))

        self.kind_box = QComboBox()
        self.kind_box.addItem("Расход", CategoryKind.EXPENSE.value)
        self.kind_box.addItem("Накопления", CategoryKind.SAVINGS.value)

        self.category_box = QComboBox()

        self.limit_inp = QLineEdit()
        self.limit_inp.setPlaceholderText("Напр.: 25000,00")

        form = QFormLayout()
        form.addRow("Месяц:", self.month_edit)
        form.addRow("Тип:", self.kind_box)
        form.addRow("Категория:", self.category_box)
        form.addRow("Лимит (₽):", self.limit_inp)

        self.btn_ok = QPushButton("Сохранить")
        self.btn_cancel = QPushButton("Отмена")
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

        btns = QHBoxLayout()
        btns.addStretch(1)
        btns.addWidget(self.btn_cancel)
        btns.addWidget(self.btn_ok)

        root = QVBoxLayout()
        root.addLayout(form)
        root.addLayout(btns)
        self.setLayout(root)

        self.kind_box.currentIndexChanged.connect(self._reload_categories)
        self._reload_categories()

    def _reload_categories(self):
        want_kind = self.kind_box.currentData()
        with self.ctx.open_session() as session:
            repo = CategoriesRepo(session)
            cats = [c for c in repo.list_all() if c.kind == want_kind]

        self.category_box.clear()
        for c in cats:
            self.category_box.addItem(c.name, c.id)

        if self.category_box.count() == 0:
            self.category_box.addItem("— Нет категорий этого типа —", -1)

    def get_data(self):
        m = self.month_edit.date().toPython()
        m = month_start(m)
        cat_id = int(self.category_box.currentData()) if self.category_box.currentData() is not None else -1
        limit_cents = parse_rub_to_cents(self.limit_inp.text())
        return m, cat_id, limit_cents


class BudgetsView(QWidget):
    def __init__(self, ctx: AppContext):
        super().__init__()
        self.ctx = ctx

        self.title = QLabel("Бюджеты")

        self.month_pick = QDateEdit()
        self.month_pick.setCalendarPopup(True)
        today = date.today()
        self.month_pick.setDate(QDate(today.year, today.month, 1))

        self.btn_add = QPushButton("Добавить/обновить")
        self.btn_delete = QPushButton("Удалить")

        header = QHBoxLayout()
        header.addWidget(self.title)
        header.addStretch(1)
        header.addWidget(QLabel("Месяц:"))
        header.addWidget(self.month_pick)
        header.addWidget(self.btn_add)
        header.addWidget(self.btn_delete)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["ID", "Категория", "Тип", "Лимит", "Факт", "Остаток", "%"])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(self.table.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)

        layout = QVBoxLayout()
        layout.addLayout(header)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.btn_add.clicked.connect(self.add_or_update_budget)
        self.btn_delete.clicked.connect(self.delete_selected)

        self.month_pick.dateChanged.connect(lambda *_: self.refresh())
        self.ctx.signals.ui_data_changed.connect(self.refresh)

        self.refresh()

    def _selected_budget_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if not item:
            return None
        try:
            return int(item.text())
        except ValueError:
            return None

    def refresh(self):
        m = month_start(self.month_pick.date().toPython())
        end = month_end(m)

        with self.ctx.open_session() as session:
            b_repo = BudgetsRepo(session)
            t_repo = TransactionsRepo(session)
            c_repo = CategoriesRepo(session)

            budgets = b_repo.list_by_month(m)
            cats = {c.id: c for c in c_repo.list_all()}

            txs = t_repo.list_filtered(start=m, end=end, limit=10000)

        # считаем факт по категориям
        fact_by_cat: dict[int, int] = {}
        for t in txs:
            if not t.category_id:
                continue
            cat = cats.get(t.category_id)
            if not cat:
                continue

            if cat.kind == CategoryKind.EXPENSE.value and t.type == TransactionType.EXPENSE.value:
                fact_by_cat[t.category_id] = fact_by_cat.get(t.category_id, 0) + t.amount_cents

            if cat.kind == CategoryKind.SAVINGS.value and t.type == TransactionType.TRANSFER.value:
                # накопления — это transfer с category_id (мы так делаем "savings_flow")
                fact_by_cat[t.category_id] = fact_by_cat.get(t.category_id, 0) + t.amount_cents

        self.table.setRowCount(0)
        for r, b in enumerate(budgets):
            cat = cats.get(b.category_id)
            cat_name = cat.name if cat else f"#{b.category_id}"
            kind = cat.kind if cat else "?"

            kind_label = {
                CategoryKind.EXPENSE.value: "Расход",
                CategoryKind.SAVINGS.value: "Накопления",
                CategoryKind.INCOME.value: "Доход",
            }.get(kind, kind)

            fact = fact_by_cat.get(b.category_id, 0)
            remain = b.limit_cents - fact
            pct = int((fact / b.limit_cents) * 100) if b.limit_cents > 0 else 0

            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(b.id)))
            self.table.setItem(r, 1, QTableWidgetItem(cat_name))
            self.table.setItem(r, 2, QTableWidgetItem(kind_label))
            self.table.setItem(r, 3, QTableWidgetItem(format_rub(b.limit_cents)))
            self.table.setItem(r, 4, QTableWidgetItem(format_rub(fact)))
            self.table.setItem(r, 5, QTableWidgetItem(format_rub(remain)))
            self.table.setItem(r, 6, QTableWidgetItem(f"{pct}%"))

    def add_or_update_budget(self):
        dlg = BudgetDialog(self.ctx, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        m, cat_id, limit_cents = dlg.get_data()

        if cat_id < 0:
            QMessageBox.warning(self, "Ошибка", "Нужна категория. Создай её в разделе Категории.")
            return
        if limit_cents is None or limit_cents <= 0:
            QMessageBox.warning(self, "Ошибка", "Лимит должен быть числом больше 0.")
            return

        with self.ctx.open_session() as session:
            repo = BudgetsRepo(session)
            upsert_budget(repo, month_start=m, category_id=cat_id, limit_cents=limit_cents)

        self.refresh()
        self.ctx.signals.ui_data_changed.emit()

    def delete_selected(self):
        b_id = self._selected_budget_id()
        if not b_id:
            QMessageBox.information(self, "Выбор", "Выбери бюджет в таблице.")
            return

        if QMessageBox.question(self, "Подтверждение", "Удалить выбранный бюджет?") != QMessageBox.StandardButton.Yes:
            return

        with self.ctx.open_session() as session:
            repo = BudgetsRepo(session)
            ok = repo.delete(b_id)

        if not ok:
            QMessageBox.warning(self, "Ошибка", "Бюджет не найден.")
            return

        self.refresh()
        self.ctx.signals.ui_data_changed.emit()
