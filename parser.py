import sys
import os
import asyncio
import json
from telethon.sync import TelegramClient
from telethon.errors import ApiIdInvalidError, AuthKeyUnregisteredError
from tabulate import tabulate
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QFile, QTextStream, QThread, Signal, Slot
from PySide6.QtUiTools import QUiLoader
from telethon.tl.types import PeerChannel
import re

users_data = []
CONFIG_FILE = "config.json"
SESSION_FILE = "telegram_session.session"


class Worker(QThread):
    finished = Signal()
    log_signal = Signal(str)
    error_signal = Signal(str)

    def _clean_text(self, text):

        return re.sub(r"[\u200e\u200f\u202a-\u202e\u2060-\u206f]+", "", text)

    def __init__(self, api_id, api_hash, phone, chat_id):
        super().__init__()
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.chat_id = chat_id

    def run(self):
        try:
            asyncio.run(self._scrape_users())
        except Exception as e:
            self.error_signal.emit(f"Ошибка: {str(e)}")

    async def _scrape_users(self):
        self.log_signal.emit(
            "Начинаем парсинг...(При первом запуске авторизируйтесь в консоли)"
        )
        async with TelegramClient(
            SESSION_FILE,
            int(self.api_id),
            self.api_hash,
            device_model="Python Script",
            system_version="Windows",
        ) as client:
            try:
                if not await client.is_user_authorized():
                    self.log_signal.emit("Требуется авторизация...")
                    await client.start(phone=self.phone)
                    self.log_signal.emit("Успешный вход в аккаунт!")
                else:
                    self.log_signal.emit("Используется существующая сессия")
                me = await client.get_me()
                self.log_signal.emit(f"Авторизованы как: {me.phone}")
                chat_ids = [x.strip() for x in self.chat_id.split(",") if x.strip()]
                for chat_id in chat_ids:
                    try:
                        if chat_id.startswith("-100"):
                            entity = PeerChannel(int(chat_id[4:]))
                        elif chat_id.lstrip("-").isdigit():
                            entity = PeerChannel(int(chat_id))
                        else:
                            entity = chat_id
                        chat = await client.get_entity(entity)
                        self.log_signal.emit(
                            f"\nНайден чат: {getattr(chat, 'title', chat_id)}"
                        )

                        async for user in client.iter_participants(chat):
                            if user.bot:
                                continue
                            first_name = self._clean_text(
                                user.first_name or "Без имени"
                            )
                            username = user.username or None
                            if username:
                                user_info = f"{first_name}\t@{username}"
                            else:
                                user_info = f"{first_name}\tНет ссылки"
                            users_data.append(user_info)

                    except Exception as e:
                        self.error_signal.emit(f"Ошибка с чатом {chat_id}: {str(e)}")

                self._save_results()
                self.log_signal.emit("Парсинг завершен успешно!")

            except ApiIdInvalidError:
                self.error_signal.emit("Ошибка: Неверный API_ID или API_HASH!")
            except AuthKeyUnregisteredError:
                self.error_signal.emit("Ошибка: Ключ авторизации недействителен!")
                if os.path.exists(SESSION_FILE):
                    os.remove(SESSION_FILE)
            except Exception as e:
                self.error_signal.emit(f"Ошибка: {str(e)}")

    def _save_results(self):
        try:
            headers = ["Имя", "Ссылка"]
            table_data = [user_info.split("\t") for user_info in users_data]
            table = tabulate(table_data, headers=headers, tablefmt="grid")
            with open("users.txt", "w", encoding="utf-8") as f:
                f.write(table + "\n")
            self.log_signal.emit("Все данные сохраненны в users.txt")
        except Exception as e:
            self.error_signal.emit(f"Ошибка сохранения результатов: {str(e)}")


class TelegramParser:
    def __init__(self, ui):
        self.ui = ui
        self.worker = None
        self.load_config()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.ui.lineApi.setText(config.get("api_id", ""))
                    self.ui.lineHash.setText(config.get("api_hash", ""))
                    self.ui.linePhone.setText(config.get("phone", ""))
                    self.ui.lineChat.setText(config.get("chat_id", ""))
                    self.log_message("кфг загружен ")
            except Exception as e:
                self.log_message(f"Ошибка загрузки кфг: {str(e)}")

    def save_config(self):
        config = {
            "api_id": self.ui.lineApi.text().strip(),
            "api_hash": self.ui.lineHash.text().strip(),
            "phone": self.ui.linePhone.text().strip(),
            "chat_id": self.ui.lineChat.text().strip(),
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
            self.log_message("Настройки сохранены в config.json")
            QMessageBox.information(self.ui, "Успех", "Настройки сохранены!")
        except Exception as e:
            self.log_message(f"Ошибка сохранения конфига: {str(e)}")
            QMessageBox.critical(
                self.ui, "Ошибка", f"Не удалось сохранить ваш кфг: {str(e)}"
            )

    def clear_fields(self):
        self.ui.lineApi.clear()
        self.ui.lineHash.clear()
        self.ui.linePhone.clear()
        self.ui.lineChat.clear()
        self.log_message("Все поля отчищены")

    def log_message(self, message):
        if "успешно" in message.lower():
            html = f'<span style="color: #03FF4E;">{message}</span>'
        elif "ошибка" in message.lower():
            html = f'<span style="color: red;">{message}</span>'
        else:
            html = message
        self.ui.plainTextEdit.appendHtml(html)
        self.ui.plainTextEdit.ensureCursorVisible()

    def start_parsing(self):
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self.ui, "Внимание", "Парсинг уже выполняется!")
            return
        api_id = self.ui.lineApi.text().strip()
        api_hash = self.ui.lineHash.text().strip()
        phone = self.ui.linePhone.text().strip()
        chat_id = self.ui.lineChat.text().strip()

        if not all([api_id, api_hash, phone, chat_id]):
            self.log_message("Ошибка: Все поля должны быть заполнены!")
            QMessageBox.critical(self.ui, "Ошибка", "Все поля должны быть заполнены!")
            return
        global users_data
        users_data = []
        self.ui.plainTextEdit.clear()
        self.worker = Worker(api_id, api_hash, phone, chat_id)
        self.worker.log_signal.connect(self.log_message)
        self.worker.error_signal.connect(self.show_error)
        self.worker.start()

    def show_error(self, message):
        self.log_message(message)
        QMessageBox.critical(self.ui, "Ошибка", message)


def run_gui():
    app = QApplication(sys.argv)
    loader = QUiLoader()
    ui_file = QFile("gui.ui")
    if not ui_file.open(QFile.ReadOnly):
        print(f"Ошибка гуишки {ui_file.fileName()}: {ui_file.errorString()}")
        sys.exit(-1)
    main_window = loader.load(ui_file)
    ui_file.close()
    parser = TelegramParser(main_window)
    main_window.btnStart.clicked.connect(
        lambda: main_window.stackedWidget.setCurrentWidget(main_window.pageStart)
    )
    main_window.btnSettings.clicked.connect(
        lambda: main_window.stackedWidget.setCurrentWidget(main_window.pageSettings)
    )
    main_window.btnSave.clicked.connect(parser.save_config)
    main_window.btnClear.clicked.connect(parser.clear_fields)
    main_window.btnStart_2.clicked.connect(parser.start_parsing)
    main_window.setFixedSize(805, 560)
    main_window.plainTextEdit.clear()

    main_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_gui()
