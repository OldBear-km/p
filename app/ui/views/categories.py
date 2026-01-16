from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QLineEdit, QComboBox, QMessageBox
)

from app.ui.app_context import AppContext
from app.infrastructure.repositories.categories import CategoriesRepo
from app.application.services.categories import create_category
from app.domain.enums import CategoryKind


class AddCategoryDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Добавить категорию")
        self.setMinimumWidth(420)

        self.kind_box = QComboBox()
        self.kind_box.addItem("Расход", CategoryKind.EXPENSE.value)
        self.kind_box.addItem("Доход", CategoryKind.INCOME.value)
        self.kind_box.addItem("Накопления", CategoryKind.SAVINGS.value)  # ✅ новое

        self.name_inp = QLineEdit()

        form = QFormLayout()
        form.addRow("Тип:", self.kind_box)
        form.addRow("Название:", self.name_inp)

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
        kind = self.kind_box.currentData()
        name = self.name_inp.text().strip()
        return kind, name


class CategoriesView(QWidget):
    def __init__(self, ctx: AppContext):
        super().__init__()
        self.ctx = ctx

        self.title = QLabel("Категории")
        self.btn_add = QPushButton("Добавить")

        header = QHBoxLayout()
        header.addWidget(self.title)
        header.addStretch(1)
        header.addWidget(self.btn_add)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Тип", "Название", "Slug"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(self.table.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)

        layout = QVBoxLayout()
        layout.addLayout(header)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.btn_add.clicked.connect(self.add_category)

        self.refresh()

    def refresh(self):
        try:
            with self.ctx.open_session() as session:
                repo = CategoriesRepo(session)
                items = repo.list_all()

            kind_label_map = {
                CategoryKind.EXPENSE.value: "Расход",
                CategoryKind.INCOME.value: "Доход",
                CategoryKind.SAVINGS.value: "Накопления",
            }

            self.table.setRowCount(0)
            for r, cat in enumerate(items):
                self.table.insertRow(r)
                self.table.setItem(r, 0, QTableWidgetItem(str(cat.id)))
                self.table.setItem(r, 1, QTableWidgetItem(kind_label_map.get(cat.kind, cat.kind)))
                self.table.setItem(r, 2, QTableWidgetItem(cat.name))
                self.table.setItem(r, 3, QTableWidgetItem(cat.slug))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при обновлении категорий: {e}")

    def add_category(self):
        dlg = AddCategoryDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        kind, name = dlg.get_data()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Название категории не может быть пустым.")
            return

        try:
            with self.ctx.open_session() as session:
                repo = CategoriesRepo(session)
                create_category(repo, kind=kind, name=name)

            self.refresh()
            self.ctx.signals.ui_data_changed.emit()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить категорию: {e}")
