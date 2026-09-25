import re
import sys
import webbrowser
from datetime import datetime

from PySide6.QtCore import QThread, Signal, Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDoubleSpinBox, QFormLayout, QFrame,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton,
    QScrollArea, QVBoxLayout, QWidget,
)

from .database import Database
from .models import Listing
from .parsing import METRO_CITIES, location_is_approximate, maps_query
from .search import SearchFilters, run_search
from .updater import GitHubUpdater, UpdateError, is_newer, update_check_due
from .version import __version__


def value(text, fallback="Não informado"):
    return str(text).strip() if text not in (None, "") else fallback


def money(amount):
    if amount is None:
        return "Preço não informado"
    return f"R$ {amount:,.0f}".replace(",", ".")


class SearchWorker(QThread):
    done = Signal(object)

    def __init__(self, db, filters):
        super().__init__()
        self.db = db
        self.filters = filters

    def run(self):
        self.done.emit(run_search(self.db, self.filters))


class UpdateWorker(QThread):
    done = Signal(object, object)

    def run(self):
        try:
            self.done.emit(GitHubUpdater().latest(), None)
        except Exception as exc:
            self.done.emit(None, exc)


class SearchFilterDialog(QDialog):
    def __init__(self, previous=None, parent=None):
        super().__init__(parent)
        previous = SearchFilters.from_dict(previous)
        self.setWindowTitle("Filtros da busca")
        self.resize(560, 500)
        form = QFormLayout(self)

        self.city = QComboBox()
        self.city.addItem("Belo Horizonte e Região Metropolitana", "")
        for city in METRO_CITIES:
            self.city.addItem(city, city)
        if previous.city:
            index = self.city.findData(previous.city)
            if index >= 0:
                self.city.setCurrentIndex(index)

        self.neighborhoods = QLineEdit(", ".join(previous.neighborhoods))
        self.neighborhoods.setPlaceholderText(
            "Ex.: Nacional, Xangri-lá. Vazio = qualquer bairro da região"
        )

        self.min_price = QDoubleSpinBox()
        self.max_price = QDoubleSpinBox()
        self.min_area = QDoubleSpinBox()
        self.max_area = QDoubleSpinBox()
        for widget, maximum, suffix in (
            (self.min_price, 100_000_000, " R$"),
            (self.max_price, 100_000_000, " R$"),
            (self.min_area, 1_000_000, " m²"),
            (self.max_area, 1_000_000, " m²"),
        ):
            widget.setRange(0, maximum)
            widget.setDecimals(0)
            widget.setSpecialValueText("Sem limite")
            widget.setSuffix(suffix)

        self.min_price.setValue(previous.min_price or 0)
        self.max_price.setValue(previous.max_price or 0)
        self.min_area.setValue(previous.min_area or 0)
        self.max_area.setValue(previous.max_area or 0)

        self.dimensions = QLineEdit(previous.dimensions)
        self.dimensions.setPlaceholderText("Ex.: 12 x 30")

        self.topography = QComboBox()
        self.topography.addItems(["Qualquer", "Plano", "Aclive", "Declive"])
        if previous.topography:
            self.topography.setCurrentText(previous.topography)

        self.walled = QComboBox()
        self.walled.addItems(["Qualquer", "Sim", "Não"])
        if previous.walled:
            self.walled.setCurrentText(previous.walled)

        self.require_price = QCheckBox("Mostrar somente anúncios com preço informado")
        self.require_price.setChecked(previous.require_price)

        form.addRow("Região / cidade", self.city)
        form.addRow("Bairros", self.neighborhoods)
        form.addRow("Preço mínimo", self.min_price)
        form.addRow("Preço máximo", self.max_price)
        form.addRow("Área mínima", self.min_area)
        form.addRow("Área máxima", self.max_area)
        form.addRow("Dimensões", self.dimensions)
        form.addRow("Topografia", self.topography)
        form.addRow("Murado", self.walled)
        form.addRow("", self.require_price)

        hint = QLabel(
            "A busca fica sempre limitada a Belo Horizonte e Região Metropolitana. "
            "O Radar tenta guardar somente anúncios individuais de lotes, não páginas de pesquisa. "
            "Por padrão, anúncios sem preço informado são ignorados."
        )
        hint.setWordWrap(True)
        hint.setObjectName("muted")
        form.addRow(hint)

        actions = QHBoxLayout()
        cancel = QPushButton("CANCELAR")
        cancel.clicked.connect(self.reject)
        search = QPushButton("BUSCAR LOTES")
        search.setObjectName("primary")
        search.clicked.connect(self.accept)
        actions.addWidget(cancel)
        actions.addWidget(search)
        form.addRow(actions)

    def filters(self):
        neighborhoods = tuple(
            part.strip() for part in self.neighborhoods.text().split(",") if part.strip()
        )
        return SearchFilters(
            city=str(self.city.currentData() or ""),
            neighborhoods=neighborhoods,
            min_price=self.min_price.value() or None,
            max_price=self.max_price.value() or None,
            min_area=self.min_area.value() or None,
            max_area=self.max_area.value() or None,
            dimensions=self.dimensions.text().strip(),
            topography="" if self.topography.currentText() == "Qualquer" else self.topography.currentText(),
            walled="" if self.walled.currentText() == "Qualquer" else self.walled.currentText(),
            require_price=self.require_price.isChecked(),
        )

class UpdateDialog(QDialog):
    def __init__(self, db, release, parent=None):
        super().__init__(parent)
        self.db = db
        self.release = release
        self.setWindowTitle("Atualização disponível")
        self.resize(500, 240)
        box = QVBoxLayout(self)
        title = QLabel(f"Radar de Lotes v{release.version} está disponível")
        title.setObjectName("cardTitle")
        box.addWidget(title)
        notes = QLabel((release.notes or "Nova versão disponível.")[:1000])
        notes.setWordWrap(True)
        box.addWidget(notes)
        info = QLabel("O download é validado por SHA-256 antes da instalação.")
        info.setObjectName("muted")
        box.addWidget(info)
        actions = QHBoxLayout()
        later = QPushButton("DEPOIS")
        later.clicked.connect(self.reject)
        update = QPushButton("ATUALIZAR AGORA")
        update.setObjectName("primary")
        update.clicked.connect(self.install)
        actions.addWidget(later)
        actions.addWidget(update)
        box.addLayout(actions)

    def install(self):
        try:
            installer = GitHubUpdater().download_verified(self.release)
            GitHubUpdater.launch_installer(installer)
            self.accept()
            QApplication.quit()
        except (UpdateError, OSError) as exc:
            QMessageBox.warning(self, "Falha na atualização", str(exc))


class AddDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cadastrar lote")
        form = QFormLayout(self)
        self.fields = {
            name: QLineEdit() for name in (
                "title", "neighborhood", "city", "dimensions", "topography",
                "walled", "cab", "address", "phone", "whatsapp", "email",
                "agency", "broker", "url", "notes"
            )
        }
        self.fields["city"].setText("Contagem")
        labels = {
            "title": "Título", "neighborhood": "Bairro *", "city": "Cidade",
            "dimensions": "Dimensões", "topography": "Topografia", "walled": "Murado?",
            "cab": "CAB", "address": "Endereço", "phone": "Telefone",
            "whatsapp": "WhatsApp", "email": "E-mail", "agency": "Imobiliária",
            "broker": "Corretor", "url": "Link", "notes": "Observação",
        }
        self.price, self.area = QDoubleSpinBox(), QDoubleSpinBox()
        self.price.setRange(0, 100_000_000)
        self.price.setPrefix("R$ ")
        self.price.setDecimals(2)
        self.area.setRange(0, 1_000_000)
        self.area.setSuffix(" m²")
        self.area.setDecimals(2)
        for key, field in self.fields.items():
            form.addRow(labels[key], field)
        form.insertRow(3, "Preço", self.price)
        form.insertRow(4, "Área", self.area)
        save = QPushButton("SALVAR LOTE")
        save.clicked.connect(self.accept)
        form.addRow(save)

    def listing(self):
        data = {key: field.text().strip() for key, field in self.fields.items()}
        data["title"] = data["title"] or f"Terreno em {data['neighborhood']}"
        data["price"] = self.price.value() or None
        data["area"] = self.area.value() or None
        return Listing(**data)


def open_phone(phone):
    webbrowser.open("tel:" + re.sub(r"[^0-9+]", "", phone))


def open_whatsapp(phone):
    digits = re.sub(r"\D", "", phone)
    if len(digits) in (10, 11):
        digits = "55" + digits
    webbrowser.open("https://wa.me/" + digits)


class DetailsDialog(QDialog):
    def __init__(self, row, db, contact_only=False, parent=None):
        super().__init__(parent)
        self.row = row
        self.setWindowTitle("Contato" if contact_only else "Detalhes do lote")
        self.resize(650, 560)
        box = QVBoxLayout(self)
        if not contact_only:
            title = QLabel(f"{value(row['neighborhood']).upper()} — {money(row['price'])}")
            title.setObjectName("cardTitle")
            box.addWidget(title)
            address = value(row["address"], value(row["neighborhood"]))
            approximate = (
                "\nLocalização aproximada — o anúncio não informa endereço completo."
                if location_is_approximate(row["address"], row["latitude"], row["longitude"]) else ""
            )
            details = QLabel(
                f"Área: {value(f'{row['area']:g} m²' if row['area'] else '')}\n"
                f"Dimensões: {value(row['dimensions'])}\n"
                f"Topografia: {value(row['topography'])}\n"
                f"Murado: {value(row['walled'])}\n"
                f"CAB: {value(row['cab'], 'Precisa confirmar')}\n"
                f"CAM: {value(row['cam'], 'Precisa confirmar')}\n"
                f"Localização: {address}{approximate}\n"
                f"Encontrado em: {row['found_at'].replace('T', ' ')}"
            )
            details.setWordWrap(True)
            box.addWidget(details)
            if row["description"]:
                description = QLabel("Descrição\n" + row["description"])
                description.setWordWrap(True)
                box.addWidget(description)
            if row["image_url"]:
                photo = QPushButton("ABRIR FOTO")
                photo.clicked.connect(lambda: webbrowser.open(row["image_url"]))
                box.addWidget(photo)

        contact_lines = []
        for label, key in (
            ("Telefone", "phone"), ("WhatsApp", "whatsapp"), ("E-mail", "email"),
            ("Imobiliária", "agency"), ("Corretor", "broker"),
        ):
            if row[key]:
                contact_lines.append(f"{label}: {row[key]}")
        contact = QLabel(
            "CONTATO\n" + ("\n".join(contact_lines) if contact_lines else
                           "Contato disponível somente no anúncio original")
        )
        contact.setWordWrap(True)
        box.addWidget(contact)

        contact_actions = QHBoxLayout()
        if row["phone"]:
            btn = QPushButton("LIGAR")
            btn.clicked.connect(lambda: open_phone(row["phone"]))
            contact_actions.addWidget(btn)
        if row["whatsapp"]:
            btn = QPushButton("ABRIR WHATSAPP")
            btn.clicked.connect(lambda: open_whatsapp(row["whatsapp"]))
            contact_actions.addWidget(btn)
        if row["email"]:
            btn = QPushButton("ENVIAR E-MAIL")
            btn.clicked.connect(lambda: webbrowser.open("mailto:" + row["email"]))
            contact_actions.addWidget(btn)
        box.addLayout(contact_actions)

        if not contact_only:
            history = db.price_history(row["id"])
            if history:
                lines = [
                    f"{money(h['price'])} — {h['recorded_at'].replace('T', ' ')}"
                    for h in history
                ]
                box.addWidget(QLabel("HISTÓRICO DE PREÇO\n" + "\n".join(lines)))

        links = QHBoxLayout()
        sources = db.sources(row["id"])
        if sources:
            box.addWidget(QLabel(
                "ENCONTRADO EM\n" + "\n".join(f"• {source['source']}" for source in sources)
            ))
            for source in sources:
                if source["url"]:
                    btn = QPushButton(f"ABRIR {source['source'].upper()}")
                    btn.clicked.connect(lambda _, url=source["url"]: webbrowser.open(url))
                    links.addWidget(btn)
        elif row["url"]:
            btn = QPushButton("VER ANÚNCIO")
            btn.clicked.connect(lambda: webbrowser.open(row["url"]))
            links.addWidget(btn)

        map_url = maps_query(row["address"], row["neighborhood"], row["city"], "MG", row["latitude"], row["longitude"])
        if map_url:
            label = "GOOGLE MAPS"
            if location_is_approximate(row["address"], row["latitude"], row["longitude"]):
                label += " (APROX.)"
            btn = QPushButton(label)
            btn.clicked.connect(lambda: webbrowser.open(map_url))
            links.addWidget(btn)
        box.addLayout(links)

        close = QPushButton("FECHAR")
        close.clicked.connect(self.accept)
        box.addWidget(close)


class ListingCard(QFrame):
    changed = Signal()

    def __init__(self, row, db):
        super().__init__()
        self.row, self.db = row, db
        self.setObjectName("card")
        box = QVBoxLayout(self)
        badge = QLabel(value(row["classification"], "Encontrado").upper())
        badge.setObjectName("badge")
        title = QLabel(value(row["neighborhood"], value(row["title"])))
        title.setObjectName("cardTitle")
        price = QLabel(money(row["price"]))
        price.setObjectName("price")
        price_status = QLabel("✅ Preço informado no anúncio" if row["price"] is not None else "❓ Preço não informado")
        price_status.setObjectName("muted")
        address = value(row["address"], value(row["neighborhood"]))
        approximate = " (aprox.)" if location_is_approximate(row["address"], row["latitude"], row["longitude"]) else ""
        facts = QLabel(
            f"{value(f'{row['area']:g} m²' if row['area'] else '')} • {value(row['dimensions'])}\n"
            f"{'✅' if row['topography'] else '❓'} Topografia: {value(row['topography'])}   "
            f"{'✅' if row['walled'] else '❓'} Murado: {value(row['walled'])}\n"
            f"{'✅' if row['cab'] else '❓'} CAB: {value(row['cab'], 'Precisa confirmar')}   "
            f"{'✅' if row['cam'] else '❓'} CAM: {value(row['cam'], 'Precisa confirmar')}\n"
            f"📍 {address}{approximate}   •   Fonte: {value(row['source'])}"
        )
        facts.setWordWrap(True)

        actions = QHBoxLayout()
        if row["url"]:
            btn = QPushButton("VER ANÚNCIO")
            btn.clicked.connect(lambda: webbrowser.open(row["url"]))
            actions.addWidget(btn)
        map_url = maps_query(row["address"], row["neighborhood"], row["city"], "MG", row["latitude"], row["longitude"])
        if map_url:
            btn = QPushButton("GOOGLE MAPS" + (" (APROX.)" if approximate else ""))
            btn.clicked.connect(lambda: webbrowser.open(map_url))
            actions.addWidget(btn)
        contact_btn = QPushButton("CONTATO")
        contact_btn.clicked.connect(lambda: DetailsDialog(row, db, True, self).exec())
        actions.addWidget(contact_btn)
        detail_btn = QPushButton("DETALHES")
        detail_btn.clicked.connect(lambda: DetailsDialog(row, db, False, self).exec())
        actions.addWidget(detail_btn)
        if row["status"] != "interesting":
            fav = QPushButton("INTERESSA")
            fav.setObjectName("primary")
            fav.clicked.connect(lambda: self.move("interesting"))
            actions.addWidget(fav)
        if row["status"] != "discarded":
            discard = QPushButton("DESCARTAR")
            discard.clicked.connect(lambda: self.move("discarded"))
            actions.addWidget(discard)
        if row["status"] != "new":
            restore = QPushButton("VOLTAR PARA NOVOS")
            restore.clicked.connect(lambda: self.move("new"))
            actions.addWidget(restore)

        for widget in (badge, title, price, price_status, facts):
            box.addWidget(widget)
        box.addLayout(actions)

    def move(self, status):
        self.db.set_status(self.row["id"], status)
        self.changed.emit()


class MainWindow(QMainWindow):
    def __init__(self, db=None):
        super().__init__()
        self.db = db or Database()
        self.status = "new"
        self.worker = None
        self.update_worker = None
        self.pending_release = None
        self.setWindowTitle(f"Radar de Lotes {__version__}")
        self.resize(1000, 740)

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(28, 22, 28, 22)
        header = QHBoxLayout()
        heading = QVBoxLayout()
        name = QLabel("RADAR DE LOTES")
        name.setObjectName("appTitle")
        self.last = QLabel()
        self.last.setObjectName("muted")
        heading.addWidget(name)
        heading.addWidget(self.last)
        header.addLayout(heading)
        header.addStretch()

        self.update_notice = QPushButton("")
        self.update_notice.setObjectName("updateNotice")
        self.update_notice.setVisible(False)
        self.update_notice.clicked.connect(self.open_pending_update)
        header.addWidget(self.update_notice)

        add_btn = QPushButton("+ CADASTRAR LOTE")
        add_btn.clicked.connect(self.add_listing)
        backup_btn = QPushButton("FAZER BACKUP")
        backup_btn.clicked.connect(self.backup)
        self.search_btn = QPushButton("BUSCAR AGORA")
        self.search_btn.setObjectName("primary")
        self.search_btn.clicked.connect(self.search)

        header.addWidget(add_btn)
        header.addWidget(backup_btn)
        header.addWidget(self.search_btn)
        layout.addLayout(header)

        tabs = QHBoxLayout()
        self.tab_buttons = {}
        for key, label in (
            ("new", "NOVOS"), ("interesting", "INTERESSANTES"), ("discarded", "DESCARTADOS")
        ):
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, status=key: self.show_status(status))
            tabs.addWidget(btn)
            self.tab_buttons[key] = btn
        tabs.addStretch()
        layout.addLayout(tabs)

        self.summary = QLabel()
        self.summary.setObjectName("summary")
        layout.addWidget(self.summary)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        layout.addWidget(self.scroll)
        self.setCentralWidget(root)
        self.setStyleSheet(STYLE)
        self.refresh()

        QTimer.singleShot(1800, self.check_updates_silently)
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.check_updates_silently)
        self.update_timer.start(60 * 60 * 1000)

    def show_status(self, status):
        self.status = status
        self.refresh()

    def refresh(self):
        rows = self.db.all(self.status)
        labels = {
            "new": "novos lotes", "interesting": "lotes interessantes",
            "discarded": "lotes descartados",
        }
        self.summary.setText(f"{len(rows)} {labels[self.status]}")
        last = self.db.get_state("last_search")
        self.last.setText(
            "Última busca: " + (last.replace("T", " às ") if last else "ainda não realizada")
        )
        for key, btn in self.tab_buttons.items():
            btn.setProperty("active", key == self.status)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        page = QWidget()
        box = QVBoxLayout(page)
        box.setAlignment(Qt.AlignTop)
        box.setSpacing(14)
        if not rows:
            empty = QLabel("Nenhum lote aqui ainda.")
            empty.setAlignment(Qt.AlignCenter)
            empty.setObjectName("empty")
            box.addWidget(empty)
        for row in rows:
            card = ListingCard(row, self.db)
            card.changed.connect(self.refresh)
            box.addWidget(card)
        self.scroll.setWidget(page)

    def add_listing(self):
        dialog = AddDialog(self)
        if dialog.exec():
            item = dialog.listing()
            if not item.neighborhood:
                QMessageBox.warning(self, "Campo obrigatório", "Informe o bairro.")
                return
            _, action = self.db.upsert(item)
            self.status = "new"
            self.refresh()
            QMessageBox.information(
                self, "Lote salvo",
                "Lote cadastrado com sucesso." if action == "new"
                else "O lote já existia e foi atualizado.",
            )

    def search(self):
        if self.worker and self.worker.isRunning():
            return
        dialog = SearchFilterDialog(self.db.get_state("search_filters", {}), self)
        if not dialog.exec():
            return
        filters = dialog.filters()
        if (
            filters.min_price is not None and filters.max_price is not None
            and filters.min_price > filters.max_price
        ) or (
            filters.min_area is not None and filters.max_area is not None
            and filters.min_area > filters.max_area
        ):
            QMessageBox.warning(
                self, "Filtros inválidos",
                "O valor mínimo não pode ser maior que o máximo.",
            )
            return
        self.db.set_state("search_filters", filters.to_dict())
        self.search_btn.setEnabled(False)
        self.search_btn.setText("PROCURANDO...")
        self.worker = SearchWorker(self.db, filters)
        self.worker.done.connect(self.search_done)
        self.worker.start()

    def search_done(self, result):
        self.search_btn.setEnabled(True)
        self.search_btn.setText("BUSCAR AGORA")
        self.refresh()
        QMessageBox.information(
            self, "Busca concluída",
            f"{result.new} novos lotes.\n{result.updated} atualizados.\n"
            f"{result.rejected} ignorados pelos filtros/regras.\n"
            f"{result.missing_price} sem preço informado.\n{result.errors} fontes com erro.",
        )

    def backup(self):
        self.db.backup()
        QMessageBox.information(self, "Backup concluído", "Uma cópia segura dos dados foi criada.")

    def check_updates_silently(self):
        if self.update_worker and self.update_worker.isRunning():
            return
        if not update_check_due(self.db.get_state("last_update_check")):
            return
        self.update_worker = UpdateWorker()
        self.update_worker.done.connect(self.update_checked)
        self.update_worker.start()

    def update_checked(self, release, error):
        self.db.set_state("last_update_check", datetime.now().isoformat(timespec="seconds"))
        if not error and release and is_newer(release.version):
            self.pending_release = release
            self.update_notice.setText(f"Nova versão {release.version} disponível — clique para atualizar")
            self.update_notice.setVisible(True)
        elif not error:
            self.pending_release = None
            self.update_notice.setVisible(False)

    def open_pending_update(self):
        if self.pending_release:
            UpdateDialog(self.db, self.pending_release, self).exec()


STYLE = """
QWidget { background:#f4f7fb; color:#172033; font-family:'Segoe UI'; font-size:14px; }
#appTitle { font-size:27px; font-weight:800; color:#102a43; }
#muted { color:#68778d; }
#summary { font-size:18px; font-weight:700; margin:8px 2px; }
#card { background:white; border:1px solid #dfe7f1; border-radius:14px; padding:14px; }
#badge { color:#0a6c57; font-weight:700; font-size:11px; }
#cardTitle { font-size:21px; font-weight:750; color:#102a43; }
#price { font-size:24px; font-weight:800; color:#0a6c57; }
#empty { color:#68778d; font-size:17px; padding:80px; }
#updateNotice { color:#0b7d68; background:transparent; border:0; text-decoration:underline; padding:6px; }
#updateNotice:hover { color:#085f50; background:#eaf8f4; }
QPushButton { background:white; border:1px solid #cad6e4; border-radius:9px; padding:10px 14px; font-weight:650; }
QPushButton:hover { border-color:#117c67; background:#f1fbf8; }
QPushButton#primary { color:white; background:#0b7d68; border-color:#0b7d68; }
QPushButton[active="true"] { color:#0b7d68; border:2px solid #0b7d68; }
QLineEdit,QDoubleSpinBox,QComboBox { background:white; border:1px solid #cad6e4; border-radius:7px; padding:8px; }
QCheckBox { padding:6px 2px; }
"""


def run_app(updated=False):
    app = QApplication([])
    app.setFont(QFont("Segoe UI", 10))
    window = MainWindow()
    window.show()
    if updated:
        QTimer.singleShot(
            1200,
            lambda: QMessageBox.information(
                window, "Atualização concluída",
                f"Atualização concluída com sucesso — v{__version__}",
            ),
        )
    app.exec()
