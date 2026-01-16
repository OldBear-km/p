from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QLineEdit, QComboBox, QMessageBox
)

from app.ui.app_context import AppContext
from app.infrastructure.repositories.accounts import AccountsRepo
from app.application.services.accounts import create_account
from app.domain.enums import AccountType


class AddAccountDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Добавить счёт")
        self.setMinimumWidth(380)

        self.name_inp = QLineEdit()
        self.type_box = QComboBox()
        self.type_box.addItem("Карта", AccountType.BANK.value)
        self.type_box.addItem("Наличные", AccountType.CASH.value)
        self.type_box.addItem("Сбережения", AccountType.SAVINGS.value)

        form = QFormLayout()
        form.addRow("Название:", self.name_inp)
        form.addRow("Тип:", self.type_box)

        self.btn_ok = QPushButton("Добавить")
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

    def get_data(self) -> tuple[str, str]:
        name = self.name_inp.text().strip()
        acc_type = self.type_box.currentData()
        return name, acc_type


class AccountsView(QWidget):
    def __init__(self, ctx: AppContext):
        super().__init__()
        self.ctx = ctx

        self.title = QLabel("Счета")

        self.btn_add = QPushButton("Добавить")
        self.btn_deactivate = QPushButton("Деактивировать")

        header = QHBoxLayout()
        header.addWidget(self.title)
        header.addStretch(1)
        header.addWidget(self.btn_add)
        header.addWidget(self.btn_deactivate)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["ID", "Название", "Тип"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(self.table.EditTrigger.NoEditTriggers)

        layout = QVBoxLayout()
        layout.addLayout(header)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.btn_add.clicked.connect(self.add_account)
        self.btn_deactivate.clicked.connect(self.deactivate_selected)

        self.refresh()

    def refresh(self):
        with self.ctx.open_session() as session:
            repo = AccountsRepo(session)
            items = repo.list_active()

        self.table.setRowCount(0)
        for r, acc in enumerate(items):
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(acc.id)))
            self.table.setItem(r, 1, QTableWidgetItem(acc.name))
            self.table.setItem(r, 2, QTableWidgetItem(acc.type))

    def add_account(self):
        dlg = AddAccountDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        name, acc_type = dlg.get_data()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Название счета не может быть пустым.")
            return

        with self.ctx.open_session() as session:
            repo = AccountsRepo(session)
            create_account(repo, name=name, account_type=acc_type)

        self.refresh()
        self.ctx.signals.ui_data_changed.emit()


    def deactivate_selected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Выбор", "Выбери строку со счетом.")
            return

        acc_id = int(self.table.item(row, 0).text())
        name = self.table.item(row, 1).text()

        if QMessageBox.question(self, "Подтверждение", f"Деактивировать счёт «{name}»?") != QMessageBox.StandardButton.Yes:
            return

        with self.ctx.open_session() as session:
            repo = AccountsRepo(session)
            ok = repo.deactivate(acc_id)

        if not ok:
            QMessageBox.warning(self, "Ошибка", "Счёт не найден.")
        self.refresh()
        self.ctx.signals.ui_data_changed.emit()

