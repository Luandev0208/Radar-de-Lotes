import webbrowser
import re
import sys
from datetime import datetime

from PySide6.QtCore import QThread, Signal, Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDialog, QDoubleSpinBox, QFormLayout, QFrame,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton,
    QScrollArea, QStackedWidget, QVBoxLayout, QWidget,
)

from .database import Database
from .models import Listing
from .parsing import location_is_approximate, maps_query
from .scheduling import search_is_overdue
from .search import run_search
from .credentials import CredentialError, load_token, save_token
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
    def __init__(self, db):
        super().__init__(); self.db = db
    def run(self):
        self.done.emit(run_search(self.db))


class UpdateWorker(QThread):
    done = Signal(object, object)
    def run(self):
        try:
            self.done.emit(GitHubUpdater().latest(), None)
        except Exception as exc:
            self.done.emit(None, exc)


class UpdateDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent); self.db = db
        self.setWindowTitle("Configurações — Atualizações"); self.resize(520, 260)
        box = QVBoxLayout(self)
        box.addWidget(QLabel(f"Versão instalada: {__version__}"))
        configured = False
        if sys.platform == "win32":
            try: configured = bool(load_token())
            except CredentialError: pass
        self.status = QLabel("Credencial GitHub: " + ("Configurada" if configured else "Não configurada"))
        box.addWidget(self.status)
        explanation = QLabel(
            "Use uma credencial de acesso refinado, limitada somente a este repositório e com "
            "permissão Contents: Read. O valor será protegido pelo Gerenciador de Credenciais do Windows."
        ); explanation.setWordWrap(True); box.addWidget(explanation)
        self.token = QLineEdit(); self.token.setEchoMode(QLineEdit.Password)
        self.token.setPlaceholderText("Cole a credencial uma única vez"); box.addWidget(self.token)
        actions = QHBoxLayout()
        save = QPushButton("SALVAR E VALIDAR"); save.clicked.connect(self.save)
        check = QPushButton("VERIFICAR ATUALIZAÇÕES"); check.clicked.connect(self.check)
        actions.addWidget(save); actions.addWidget(check); box.addLayout(actions)
        close = QPushButton("FECHAR"); close.clicked.connect(self.accept); box.addWidget(close)

    def save(self):
        try:
            save_token(self.token.text())
            GitHubUpdater().verify_credential()
            self.token.clear(); self.status.setText("Credencial GitHub: Configurada")
            QMessageBox.information(self, "Credencial configurada", "Acesso de leitura validado e salvo com segurança.")
        except (CredentialError, UpdateError) as exc:
            QMessageBox.warning(self, "Não foi possível configurar", str(exc))

    def check(self):
        try:
            release = GitHubUpdater().latest()
            self.db.set_state("last_update_check", datetime.now().isoformat(timespec="seconds"))
            if is_newer(release.version):
                self.install(release)
            else:
                QMessageBox.information(self, "Radar atualizado", "Você já está usando a versão mais recente.")
        except (CredentialError, UpdateError) as exc:
            QMessageBox.warning(self, "Atualização indisponível", str(exc))

    def install(self, release):
        answer = QMessageBox.question(
            self, "Atualização disponível",
            f"A versão {release.version} está disponível.\n\n{release.notes[:800]}\n\nBaixar e instalar agora?"
        )
        if answer != QMessageBox.Yes: return
        try:
            updater = GitHubUpdater(); installer = updater.download_verified(release)
            updater.launch_installer(installer)
            QApplication.quit()
        except (CredentialError, UpdateError, OSError) as exc:
            QMessageBox.warning(self, "Falha na atualização", str(exc))


class AddDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cadastrar lote")
        form = QFormLayout(self)
        self.fields = {name: QLineEdit() for name in (
            "title", "neighborhood", "city", "dimensions", "topography", "walled",
            "cab", "address", "phone", "whatsapp", "email", "agency", "broker", "url", "notes"
        )}
        self.fields["city"].setText("Contagem")
        labels = {"title":"Título", "neighborhood":"Bairro *", "city":"Cidade",
                  "dimensions":"Dimensões", "topography":"Topografia", "walled":"Murado?",
                  "cab":"CAB", "address":"Endereço", "phone":"Telefone", "whatsapp":"WhatsApp",
                  "email":"E-mail", "agency":"Imobiliária", "broker":"Corretor",
                  "url":"Link", "notes":"Observação"}
        self.price, self.area = QDoubleSpinBox(), QDoubleSpinBox()
        self.price.setRange(0, 100_000_000); self.price.setPrefix("R$ "); self.price.setDecimals(2)
        self.area.setRange(0, 1_000_000); self.area.setSuffix(" m²"); self.area.setDecimals(2)
        for key, field in self.fields.items(): form.addRow(labels[key], field)
        form.insertRow(3, "Preço", self.price); form.insertRow(4, "Área", self.area)
        save = QPushButton("SALVAR LOTE"); save.clicked.connect(self.accept); form.addRow(save)

    def listing(self):
        data = {k: v.text().strip() for k, v in self.fields.items()}
        data["title"] = data["title"] or f"Terreno em {data['neighborhood']}"
        data["price"] = self.price.value() or None; data["area"] = self.area.value() or None
        return Listing(**data)


def open_phone(phone):
    webbrowser.open("tel:" + re.sub(r"[^0-9+]", "", phone))


def open_whatsapp(phone):
    digits = re.sub(r"\D", "", phone)
    if len(digits) in (10, 11): digits = "55" + digits
    webbrowser.open("https://wa.me/" + digits)


class DetailsDialog(QDialog):
    def __init__(self, row, db, contact_only=False, parent=None):
        super().__init__(parent); self.row = row
        self.setWindowTitle("Contato" if contact_only else "Detalhes do lote"); self.resize(650, 560)
        box = QVBoxLayout(self)
        if not contact_only:
            title = QLabel(f"{value(row['neighborhood']).upper()} — {money(row['price'])}"); title.setObjectName("cardTitle"); box.addWidget(title)
            address = value(row["address"], value(row["neighborhood"]))
            approximate = "\nLocalização aproximada — o anúncio não informa número." if location_is_approximate(row["address"]) else ""
            details = QLabel(
                f"Área: {value(f'{row['area']:g} m²' if row['area'] else '')}\n"
                f"Dimensões: {value(row['dimensions'])}\nTopografia: {value(row['topography'])}\n"
                f"Murado: {value(row['walled'])}\nCAB: {value(row['cab'], 'Precisa confirmar')}\n"
                f"Localização: {address}{approximate}\nEncontrado em: {row['found_at'].replace('T', ' ')}"
            ); details.setWordWrap(True); box.addWidget(details)
            if row["description"]:
                description = QLabel("Descrição\n" + row["description"]); description.setWordWrap(True); box.addWidget(description)
            if row["image_url"]:
                photo = QPushButton("ABRIR FOTO"); photo.clicked.connect(lambda: webbrowser.open(row["image_url"])); box.addWidget(photo)
        contact_lines = []
        for label, key in (("Telefone", "phone"), ("WhatsApp", "whatsapp"), ("E-mail", "email"), ("Imobiliária", "agency"), ("Corretor", "broker")):
            if row[key]: contact_lines.append(f"{label}: {row[key]}")
        contact = QLabel("CONTATO\n" + ("\n".join(contact_lines) if contact_lines else "Contato disponível somente no anúncio original"))
        contact.setWordWrap(True); box.addWidget(contact)
        contact_actions = QHBoxLayout()
        if row["phone"]:
            btn = QPushButton("LIGAR"); btn.clicked.connect(lambda: open_phone(row["phone"])); contact_actions.addWidget(btn)
        if row["whatsapp"]:
            btn = QPushButton("ABRIR WHATSAPP"); btn.clicked.connect(lambda: open_whatsapp(row["whatsapp"])); contact_actions.addWidget(btn)
        if row["email"]:
            btn = QPushButton("ENVIAR E-MAIL"); btn.clicked.connect(lambda: webbrowser.open("mailto:" + row["email"])); contact_actions.addWidget(btn)
        box.addLayout(contact_actions)
        if not contact_only:
            history = db.price_history(row["id"])
            if history:
                lines = [f"{money(h['price'])} — {h['recorded_at'].replace('T', ' ')}" for h in history]
                history_label = QLabel("HISTÓRICO DE PREÇO\n" + "\n".join(lines)); box.addWidget(history_label)
        links = QHBoxLayout()
        sources = db.sources(row["id"])
        if sources:
            source_names = QLabel("ENCONTRADO EM\n" + "\n".join(f"• {source['source']}" for source in sources))
            box.addWidget(source_names)
            for index, source in enumerate(sources, 1):
                if source["url"]:
                    btn = QPushButton(f"ABRIR {source['source'].upper()}")
                    btn.clicked.connect(lambda _, url=source["url"]: webbrowser.open(url)); links.addWidget(btn)
        elif row["url"]:
            btn = QPushButton("VER ANÚNCIO"); btn.clicked.connect(lambda: webbrowser.open(row["url"])); links.addWidget(btn)
        map_url = maps_query(row["address"], row["neighborhood"], row["city"])
        if map_url:
            btn = QPushButton("GOOGLE MAPS"); btn.clicked.connect(lambda: webbrowser.open(map_url)); links.addWidget(btn)
        box.addLayout(links); close = QPushButton("FECHAR"); close.clicked.connect(self.accept); box.addWidget(close)


class ListingCard(QFrame):
    changed = Signal()
    def __init__(self, row, db):
        super().__init__(); self.row, self.db = row, db
        self.setObjectName("card")
        box = QVBoxLayout(self)
        badge = QLabel(row["classification"].upper()); badge.setObjectName("badge")
        title = QLabel(value(row["neighborhood"])); title.setObjectName("cardTitle")
        price = QLabel(money(row["price"])); price.setObjectName("price")
        facts = QLabel(
            f"{value(f'{row['area']:g} m²' if row['area'] else '')} • {value(row['dimensions'])}\n"
            f"{'✅' if row['topography'] else '❓'} Topografia: {value(row['topography'])}   "
            f"{'✅' if row['walled'] else '❓'} Murado: {value(row['walled'])}\n"
            f"❓ CAB: {value(row['cab'], 'Precisa confirmar')}\n"
            f"📍 {value(row['address'], value(row['neighborhood']))}   •   Fonte: {value(row['source'])}"
        )
        facts.setWordWrap(True)
        actions = QHBoxLayout()
        if row["url"]:
            open_btn = QPushButton("VER ANÚNCIO"); open_btn.clicked.connect(lambda: webbrowser.open(row["url"])); actions.addWidget(open_btn)
        map_url = maps_query(row["address"], row["neighborhood"], row["city"])
        if map_url:
            map_btn = QPushButton("GOOGLE MAPS"); map_btn.clicked.connect(lambda: webbrowser.open(map_url)); actions.addWidget(map_btn)
        contact_btn = QPushButton("CONTATO"); contact_btn.clicked.connect(lambda: DetailsDialog(row, db, True, self).exec()); actions.addWidget(contact_btn)
        detail_btn = QPushButton("DETALHES"); detail_btn.clicked.connect(lambda: DetailsDialog(row, db, False, self).exec()); actions.addWidget(detail_btn)
        if row["status"] != "interesting":
            fav = QPushButton("INTERESSA"); fav.setObjectName("primary"); fav.clicked.connect(lambda: self.move("interesting")); actions.addWidget(fav)
        if row["status"] != "discarded":
            discard = QPushButton("DESCARTAR"); discard.clicked.connect(lambda: self.move("discarded")); actions.addWidget(discard)
        if row["status"] != "new":
            restore = QPushButton("VOLTAR PARA NOVOS"); restore.clicked.connect(lambda: self.move("new")); actions.addWidget(restore)
        for widget in (badge, title, price, facts): box.addWidget(widget)
        box.addLayout(actions)

    def move(self, status):
        self.db.set_status(self.row["id"], status); self.changed.emit()


class MainWindow(QMainWindow):
    def __init__(self, db=None):
        super().__init__(); self.db = db or Database(); self.status = "new"; self.worker = None
        self.setWindowTitle(f"Radar de Lotes {__version__}"); self.resize(930, 720)
        root = QWidget(); layout = QVBoxLayout(root); layout.setContentsMargins(28, 22, 28, 22)
        header = QHBoxLayout()
        heading = QVBoxLayout(); name = QLabel("RADAR DE LOTES"); name.setObjectName("appTitle")
        self.last = QLabel(); self.last.setObjectName("muted"); heading.addWidget(name); heading.addWidget(self.last)
        header.addLayout(heading); header.addStretch()
        self.search_btn = QPushButton("BUSCAR AGORA"); self.search_btn.setObjectName("primary"); self.search_btn.clicked.connect(self.search)
        add_btn = QPushButton("+ CADASTRAR LOTE"); add_btn.clicked.connect(self.add_listing)
        backup_btn = QPushButton("FAZER BACKUP"); backup_btn.clicked.connect(self.backup)
        update_btn = QPushButton("ATUALIZAÇÕES"); update_btn.clicked.connect(self.updates)
        header.addWidget(add_btn); header.addWidget(backup_btn); header.addWidget(update_btn); header.addWidget(self.search_btn); layout.addLayout(header)
        tabs = QHBoxLayout(); self.tab_buttons = {}
        for key, label in (("new","NOVOS"),("interesting","INTERESSANTES"),("discarded","DESCARTADOS")):
            btn = QPushButton(label); btn.clicked.connect(lambda _, s=key: self.show_status(s)); tabs.addWidget(btn); self.tab_buttons[key] = btn
        tabs.addStretch(); layout.addLayout(tabs)
        self.summary = QLabel(); self.summary.setObjectName("summary"); layout.addWidget(self.summary)
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True); self.scroll.setFrameShape(QFrame.NoFrame); layout.addWidget(self.scroll)
        self.setCentralWidget(root); self.setStyleSheet(STYLE); self.refresh()
        if search_is_overdue(self.db.get_state("last_search")):
            QTimer.singleShot(1200, self.search)
        if sys.platform == "win32" and update_check_due(self.db.get_state("last_update_check")):
            QTimer.singleShot(2500, self.check_updates_silently)

    def show_status(self, status): self.status = status; self.refresh()

    def refresh(self):
        rows = self.db.all(self.status)
        labels = {"new":"novos lotes", "interesting":"lotes interessantes", "discarded":"lotes descartados"}
        self.summary.setText(f"{len(rows)} {labels[self.status]}")
        last = self.db.get_state("last_search")
        self.last.setText("Última busca: " + (last.replace("T", " às ") if last else "ainda não realizada"))
        for key, btn in self.tab_buttons.items(): btn.setProperty("active", key == self.status); btn.style().unpolish(btn); btn.style().polish(btn)
        page = QWidget(); box = QVBoxLayout(page); box.setAlignment(Qt.AlignTop); box.setSpacing(14)
        if not rows:
            empty = QLabel("Nenhum lote aqui ainda."); empty.setAlignment(Qt.AlignCenter); empty.setObjectName("empty"); box.addWidget(empty)
        for row in rows:
            card = ListingCard(row, self.db); card.changed.connect(self.refresh); box.addWidget(card)
        self.scroll.setWidget(page)

    def add_listing(self):
        dialog = AddDialog(self)
        if dialog.exec():
            item = dialog.listing()
            if not item.neighborhood:
                QMessageBox.warning(self, "Campo obrigatório", "Informe o bairro."); return
            _, action = self.db.upsert(item); self.status = "new"; self.refresh()
            QMessageBox.information(self, "Lote salvo", "Lote cadastrado com sucesso." if action == "new" else "O lote já existia e foi atualizado.")

    def search(self):
        if self.worker and self.worker.isRunning(): return
        self.search_btn.setEnabled(False); self.search_btn.setText("PROCURANDO...")
        self.worker = SearchWorker(self.db); self.worker.done.connect(self.search_done); self.worker.start()

    def search_done(self, result):
        self.search_btn.setEnabled(True); self.search_btn.setText("BUSCAR AGORA"); self.refresh()
        QMessageBox.information(self, "Busca concluída", f"{result.new} novos lotes.\n{result.updated} atualizados.\n{result.errors} fontes com erro.")

    def backup(self):
        self.db.backup(); QMessageBox.information(self, "Backup concluído", "Uma cópia segura dos dados foi criada.")

    def updates(self):
        UpdateDialog(self.db, self).exec()

    def check_updates_silently(self):
        try:
            if not load_token(): return
        except CredentialError:
            return
        self.update_worker = UpdateWorker(); self.update_worker.done.connect(self.update_checked)
        self.update_worker.start()

    def update_checked(self, release, error):
        self.db.set_state("last_update_check", datetime.now().isoformat(timespec="seconds"))
        if not error and release and is_newer(release.version):
            UpdateDialog(self.db, self).install(release)


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
QPushButton { background:white; border:1px solid #cad6e4; border-radius:9px; padding:10px 14px; font-weight:650; }
QPushButton:hover { border-color:#117c67; background:#f1fbf8; }
QPushButton#primary { color:white; background:#0b7d68; border-color:#0b7d68; }
QPushButton[active="true"] { color:#0b7d68; border:2px solid #0b7d68; }
QLineEdit,QDoubleSpinBox { background:white; border:1px solid #cad6e4; border-radius:7px; padding:8px; }
"""


def run_app(updated=False):
    app = QApplication([]); app.setFont(QFont("Segoe UI", 10)); window = MainWindow(); window.show()
    if updated:
        QTimer.singleShot(1200, lambda: QMessageBox.information(
            window, "Atualização concluída", f"Atualização concluída com sucesso — v{__version__}"
        ))
    app.exec()
