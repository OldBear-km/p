from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate, Qt, QTimer
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QLineEdit, QComboBox, QMessageBox, QDateEdit, QGroupBox
)

from app.ui.app_context import AppContext
from app.application.money import format_rub
from app.infrastructure.repositories.accounts import AccountsRepo
from app.infrastructure.repositories.categories import CategoriesRepo
from app.infrastructure.repositories.transactions import TransactionsRepo
from app.application.services.transactions import add_expense, add_income, add_transfer
from app.domain.enums import TransactionType, CategoryKind


def parse_rub_to_cents(text: str) -> int | None:
    s = text.strip().replace("₽", "").replace(" ", "")
    if not s:
        return None
    s = s.replace(",", ".")
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


def cents_to_rub_str(amount_cents: int) -> str:
    rub = abs(amount_cents) // 100
    kop = abs(amount_cents) % 100
    return f"{rub},{kop:02d}"


class TxDialog(QDialog):
    def __init__(self, ctx: AppContext, parent: QWidget | None = None, edit_tx_id: int | None = None):
        super().__init__(parent)
        self.ctx = ctx
        self.edit_tx_id = edit_tx_id

        self.setWindowTitle("Редактировать операцию" if edit_tx_id else "Добавить операцию")
        self.setMinimumWidth(520)

        self.type_box = QComboBox()
        self.type_box.addItem("Расход", TransactionType.EXPENSE.value)
        self.type_box.addItem("Доход", TransactionType.INCOME.value)
        self.type_box.addItem("Накопления (перевод в копилку)", "savings_flow")

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())

        self.account_from = QComboBox()
        self.account_to = QComboBox()
        self.category_box = QComboBox()

        self.amount_inp = QLineEdit()
        self.amount_inp.setPlaceholderText("Например: 1250,00")

        self.note_inp = QLineEdit()
        self.note_inp.setPlaceholderText("Комментарий (необязательно)")

        form = QFormLayout()
        form.addRow("Тип:", self.type_box)
        form.addRow("Дата:", self.date_edit)
        form.addRow("Счёт:", self.account_from)
        form.addRow("Категория:", self.category_box)
        form.addRow("Копилка (счёт):", self.account_to)
        form.addRow("Сумма (₽):", self.amount_inp)
        form.addRow("Заметка:", self.note_inp)

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

        self.type_box.currentIndexChanged.connect(self._apply_rules)

        self._load_data()

        if self.edit_tx_id:
            self._prefill_from_db(self.edit_tx_id)

        self._apply_rules()

    def _load_data(self):
        with self.ctx.open_session() as session:
            acc_repo = AccountsRepo(session)
            cat_repo = CategoriesRepo(session)
            accounts = acc_repo.list_active()
            cats = cat_repo.list_all()

        self.account_from.clear()
        self.account_to.clear()
        for a in accounts:
            self.account_from.addItem(a.name, a.id)
            self.account_to.addItem(a.name, a.id)

        self._all_categories = cats

    def _apply_rules(self):
        mode = self.type_box.currentData()
        is_savings = (mode == "savings_flow")
        self.account_to.setEnabled(is_savings)

        if mode == TransactionType.EXPENSE.value:
            want_kind = CategoryKind.EXPENSE.value
        elif mode == TransactionType.INCOME.value:
            want_kind = CategoryKind.INCOME.value
        else:
            want_kind = CategoryKind.SAVINGS.value

        current_id = self.category_box.currentData()
        self.category_box.clear()

        for c in self._all_categories:
            if c.kind != want_kind:
                continue
            self.category_box.addItem(c.name, c.id)

        if self.category_box.count() == 0:
            self.category_box.addItem("— Нет подходящих категорий —", -1)

        if current_id is not None:
            idx = self.category_box.findData(current_id)
            if idx >= 0:
                self.category_box.setCurrentIndex(idx)

    def _prefill_from_db(self, tx_id: int):
        with self.ctx.open_session() as session:
            tx_repo = TransactionsRepo(session)
            tx = tx_repo.get_by_id(tx_id)

        if not tx:
            return

        self.date_edit.setDate(QDate(tx.occurred_at.year, tx.occurred_at.month, tx.occurred_at.day))
        self.amount_inp.setText(cents_to_rub_str(tx.amount_cents))
        self.note_inp.setText(tx.note or "")

        if tx.type == TransactionType.TRANSFER.value and tx.category_id is not None:
            self.type_box.setCurrentIndex(self.type_box.findData("savings_flow"))
        else:
            self.type_box.setCurrentIndex(self.type_box.findData(tx.type))

        if tx.type == TransactionType.TRANSFER.value:
            if tx.from_account_id:
                i = self.account_from.findData(tx.from_account_id)
                if i >= 0:
                    self.account_from.setCurrentIndex(i)
            if tx.to_account_id:
                i = self.account_to.findData(tx.to_account_id)
                if i >= 0:
                    self.account_to.setCurrentIndex(i)
        else:
            if tx.account_id:
                i = self.account_from.findData(tx.account_id)
                if i >= 0:
                    self.account_from.setCurrentIndex(i)

        if tx.category_id:
            self._apply_rules()
            i = self.category_box.findData(tx.category_id)
            if i >= 0:
                self.category_box.setCurrentIndex(i)

    def get_payload(self):
        mode = self.type_box.currentData()
        occurred = self.date_edit.date().toPython()

        from_acc = self.account_from.currentData()
        to_acc = self.account_to.currentData()
        cat_id = self.category_box.currentData()

        amount_cents = parse_rub_to_cents(self.amount_inp.text())
        note = self.note_inp.text().strip() or None

        return {
            "mode": mode,
            "occurred_at": occurred,
            "from_account_id": int(from_acc) if from_acc is not None else None,
            "to_account_id": int(to_acc) if to_acc is not None else None,
            "category_id": int(cat_id) if cat_id is not None else -1,
            "amount_cents": amount_cents,
            "note": note,
        }


class TransactionsView(QWidget):
    def __init__(self, ctx: AppContext):
        super().__init__()
        self.ctx = ctx

        # ===== Header buttons =====
        self.title = QLabel("Операции")
        self.btn_add = QPushButton("Добавить")
        self.btn_edit = QPushButton("Редактировать")
        self.btn_delete = QPushButton("Удалить")

        header = QHBoxLayout()
        header.addWidget(self.title)
        header.addStretch(1)
        header.addWidget(self.btn_add)
        header.addWidget(self.btn_edit)
        header.addWidget(self.btn_delete)

        # ===== Filters =====
        self.filters_box = QGroupBox("Фильтры")
        fb = QHBoxLayout()

        self.f_date_from = QDateEdit()
        self.f_date_from.setCalendarPopup(True)
        self.f_date_to = QDateEdit()
        self.f_date_to.setCalendarPopup(True)

        today = date.today()
        month_start = date(today.year, today.month, 1)
        self.f_date_from.setDate(QDate(month_start.year, month_start.month, month_start.day))
        self.f_date_to.setDate(QDate(today.year, today.month, today.day))

        self.f_type = QComboBox()
        self.f_type.addItem("Все типы", None)
        self.f_type.addItem("Расход", TransactionType.EXPENSE.value)
        self.f_type.addItem("Доход", TransactionType.INCOME.value)
        self.f_type.addItem("Перевод", TransactionType.TRANSFER.value)

        self.f_account = QComboBox()
        self.f_category = QComboBox()

        # ✅ быстрый поиск
        self.f_search = QLineEdit()
        self.f_search.setPlaceholderText("Поиск: заметка / категория / счет / тип…")

        self.btn_reset = QPushButton("Сброс")

        fb.addWidget(QLabel("С:"))
        fb.addWidget(self.f_date_from)
        fb.addWidget(QLabel("По:"))
        fb.addWidget(self.f_date_to)
        fb.addWidget(QLabel("Тип:"))
        fb.addWidget(self.f_type)
        fb.addWidget(QLabel("Счёт:"))
        fb.addWidget(self.f_account)
        fb.addWidget(QLabel("Категория:"))
        fb.addWidget(self.f_category)
        fb.addWidget(self.f_search)
        fb.addWidget(self.btn_reset)

        self.filters_box.setLayout(fb)

        # ===== Table =====
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["ID", "Дата", "Тип", "Счёт/Откуда", "Куда", "Категория", "Сумма"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(self.table.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.setColumnHidden(0, True)

        # ✅ сортировка по колонкам
        self.table.setSortingEnabled(True)

        # ===== Root layout =====
        layout = QVBoxLayout()
        layout.addLayout(header)
        layout.addWidget(self.filters_box)
        layout.addWidget(self.table)
        self.setLayout(layout)

        # debounce таймер на поиск
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(250)
        self._search_timer.timeout.connect(self.refresh)

        # Signals
        self.btn_add.clicked.connect(self.add_tx)
        self.btn_edit.clicked.connect(self.edit_tx)
        self.btn_delete.clicked.connect(self.delete_tx)

        self.btn_reset.clicked.connect(self.reset_filters)

        # ✅ double click = edit
        self.table.cellDoubleClicked.connect(lambda *_: self.edit_tx())

        # ✅ автоприменение фильтров
        self.f_date_from.dateChanged.connect(lambda *_: self.refresh())
        self.f_date_to.dateChanged.connect(lambda *_: self.refresh())
        self.f_type.currentIndexChanged.connect(lambda *_: self.refresh())
        self.f_account.currentIndexChanged.connect(lambda *_: self.refresh())
        self.f_category.currentIndexChanged.connect(lambda *_: self.refresh())

        # ✅ поиск с debounce
        self.f_search.textChanged.connect(lambda *_: self._search_timer.start())

        self._load_filter_lists()
        self.refresh()

    def _load_filter_lists(self):
        with self.ctx.open_session() as session:
            acc_repo = AccountsRepo(session)
            cat_repo = CategoriesRepo(session)
            accounts = acc_repo.list_active()
            cats = cat_repo.list_all()

        self.f_account.clear()
        self.f_account.addItem("Все счета", None)
        for a in accounts:
            self.f_account.addItem(a.name, a.id)

        self.f_category.clear()
        self.f_category.addItem("Все категории", None)
        for c in cats:
            self.f_category.addItem(c.name, c.id)

    def reset_filters(self):
        today = date.today()
        month_start = date(today.year, today.month, 1)
        self.f_date_from.setDate(QDate(month_start.year, month_start.month, month_start.day))
        self.f_date_to.setDate(QDate(today.year, today.month, today.day))
        self.f_type.setCurrentIndex(0)
        self.f_account.setCurrentIndex(0)
        self.f_category.setCurrentIndex(0)
        self.f_search.setText("")
        self.refresh()

    def _selected_tx_id(self) -> int | None:
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
        start = self.f_date_from.date().toPython()
        end = self.f_date_to.date().toPython()
        tx_type = self.f_type.currentData()
        acc_id = self.f_account.currentData()
        cat_id = self.f_category.currentData()
        needle = (self.f_search.text() or "").strip().lower()

        with self.ctx.open_session() as session:
            tx_repo = TransactionsRepo(session)
            txs = tx_repo.list_filtered(
                start=start,
                end=end,
                tx_type=tx_type,
                account_id=int(acc_id) if acc_id is not None else None,
                category_id=int(cat_id) if cat_id is not None else None,
                limit=2000,
            )

            acc_repo = AccountsRepo(session)
            cat_repo = CategoriesRepo(session)
            accounts = {a.id: a.name for a in acc_repo.list_active()}
            cats = {c.id: c.name for c in cat_repo.list_all()}

        def acc_name(acc_id_: int | None) -> str:
            if not acc_id_:
                return ""
            return accounts.get(acc_id_, f"#{acc_id_}")

        def cat_name(cat_id_: int | None) -> str:
            if not cat_id_ or cat_id_ < 0:
                return ""
            return cats.get(cat_id_, f"#{cat_id_}")

        # ✅ быстрый поиск по отображаемым строкам (MVP)
        if needle:
            filtered = []
            for t in txs:
                t_type = t.type or ""
                a1 = acc_name(t.account_id or t.from_account_id)
                a2 = acc_name(t.to_account_id)
                c1 = cat_name(t.category_id)
                note = (t.note or "")
                blob = f"{t_type} {a1} {a2} {c1} {note}".lower()
                if needle in blob:
                    filtered.append(t)
            txs = filtered

        self.table.setRowCount(0)
        for r, t in enumerate(txs):
            self.table.insertRow(r)

            type_label = {
                TransactionType.EXPENSE.value: "Расход",
                TransactionType.INCOME.value: "Доход",
                TransactionType.TRANSFER.value: "Перевод",
            }.get(t.type, t.type)

            self.table.setItem(r, 0, QTableWidgetItem(str(t.id)))
            self.table.setItem(r, 1, QTableWidgetItem(str(t.occurred_at)))
            self.table.setItem(r, 2, QTableWidgetItem(type_label))

            if t.type == TransactionType.TRANSFER.value:
                self.table.setItem(r, 3, QTableWidgetItem(acc_name(t.from_account_id)))
                self.table.setItem(r, 4, QTableWidgetItem(acc_name(t.to_account_id)))
            else:
                self.table.setItem(r, 3, QTableWidgetItem(acc_name(t.account_id)))
                self.table.setItem(r, 4, QTableWidgetItem(""))

            self.table.setItem(r, 5, QTableWidgetItem(cat_name(t.category_id)))
            self.table.setItem(r, 6, QTableWidgetItem(format_rub(t.amount_cents)))

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Delete:
            self.delete_tx()
            return
        super().keyPressEvent(event)

    def add_tx(self):
        dlg = TxDialog(self.ctx, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        payload = dlg.get_payload()

        if payload["amount_cents"] is None or payload["amount_cents"] <= 0:
            QMessageBox.warning(self, "Ошибка", "Сумма должна быть числом больше 0.")
            return
        if payload["from_account_id"] is None:
            QMessageBox.warning(self, "Ошибка", "Выбери счёт.")
            return
        if payload["category_id"] is None or payload["category_id"] < 0:
            QMessageBox.warning(self, "Ошибка", "Выбери категорию (или создай её в разделе Категории).")
            return

        mode = payload["mode"]
        with self.ctx.open_session() as session:
            tx_repo = TransactionsRepo(session)

            if mode == TransactionType.EXPENSE.value:
                add_expense(tx_repo, payload["occurred_at"], payload["from_account_id"], payload["category_id"], payload["amount_cents"], payload["note"])
            elif mode == TransactionType.INCOME.value:
                add_income(tx_repo, payload["occurred_at"], payload["from_account_id"], payload["category_id"], payload["amount_cents"], payload["note"])
            elif mode == "savings_flow":
                if payload["to_account_id"] is None:
                    QMessageBox.warning(self, "Ошибка", "Выбери счёт-копилку (куда переводим).")
                    return
                if payload["to_account_id"] == payload["from_account_id"]:
                    QMessageBox.warning(self, "Ошибка", "Счёт списания и копилка не могут совпадать.")
                    return
                add_transfer(tx_repo, payload["occurred_at"], payload["from_account_id"], payload["to_account_id"], payload["amount_cents"], payload["note"] or "Накопления", category_id=payload["category_id"])
            else:
                QMessageBox.warning(self, "Ошибка", f"Неизвестный режим: {mode}")
                return

        self.refresh()
        self.ctx.signals.ui_data_changed.emit()

    def edit_tx(self):
        tx_id = self._selected_tx_id()
        if not tx_id:
            QMessageBox.information(self, "Выбор", "Выбери операцию в таблице.")
            return

        dlg = TxDialog(self.ctx, self, edit_tx_id=tx_id)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        payload = dlg.get_payload()
        if payload["amount_cents"] is None or payload["amount_cents"] <= 0:
            QMessageBox.warning(self, "Ошибка", "Сумма должна быть числом больше 0.")
            return
        if payload["from_account_id"] is None:
            QMessageBox.warning(self, "Ошибка", "Выбери счёт.")
            return
        if payload["category_id"] is None or payload["category_id"] < 0:
            QMessageBox.warning(self, "Ошибка", "Выбери категорию.")
            return

        mode = payload["mode"]

        with self.ctx.open_session() as session:
            tx_repo = TransactionsRepo(session)
            tx = tx_repo.get_by_id(tx_id)
            if not tx:
                QMessageBox.warning(self, "Ошибка", "Операция не найдена.")
                return

            tx.occurred_at = payload["occurred_at"]
            tx.amount_cents = payload["amount_cents"]
            tx.note = payload["note"]

            if mode == TransactionType.EXPENSE.value:
                tx.type = TransactionType.EXPENSE.value
                tx.account_id = payload["from_account_id"]
                tx.category_id = payload["category_id"]
                tx.from_account_id = None
                tx.to_account_id = None

            elif mode == TransactionType.INCOME.value:
                tx.type = TransactionType.INCOME.value
                tx.account_id = payload["from_account_id"]
                tx.category_id = payload["category_id"]
                tx.from_account_id = None
                tx.to_account_id = None

            elif mode == "savings_flow":
                if payload["to_account_id"] is None:
                    QMessageBox.warning(self, "Ошибка", "Выбери счёт-копилку (куда переводим).")
                    return
                if payload["to_account_id"] == payload["from_account_id"]:
                    QMessageBox.warning(self, "Ошибка", "Счёт списания и копилка не могут совпадать.")
                    return
                tx.type = TransactionType.TRANSFER.value
                tx.account_id = None
                tx.from_account_id = payload["from_account_id"]
                tx.to_account_id = payload["to_account_id"]
                tx.category_id = payload["category_id"]

            else:
                QMessageBox.warning(self, "Ошибка", f"Неизвестный режим: {mode}")
                return

            tx_repo.commit()

        self.refresh()
        self.ctx.signals.ui_data_changed.emit()

    def delete_tx(self):
        tx_id = self._selected_tx_id()
        if not tx_id:
            QMessageBox.information(self, "Выбор", "Выбери операцию в таблице.")
            return

        if QMessageBox.question(self, "Подтверждение", "Удалить выбранную операцию?") != QMessageBox.StandardButton.Yes:
            return

        with self.ctx.open_session() as session:
            tx_repo = TransactionsRepo(session)
            ok = tx_repo.delete(tx_id)

        if not ok:
            QMessageBox.warning(self, "Ошибка", "Операция не найдена.")
            return

        self.refresh()
        self.ctx.signals.ui_data_changed.emit()
