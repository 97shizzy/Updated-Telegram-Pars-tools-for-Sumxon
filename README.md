# 🚀 Telegram User Parser

[![Python](https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-Qt-green?style=flat-square)](https://doc.qt.io/qtforpython/)
[![Telethon](https://img.shields.io/badge/Telethon-1.28.0-yellow?style=flat-square)](https://github.com/LonamiWebs/Telethon)

---

## 📖 Описание

**Telegram User Parser** — удобный графический инструмент на Python для парсинга участников из одного или нескольких Telegram-чатов и сохранения их в табличном формате.  
Поддерживает авторизацию через Telegram API, многократный ввод ID/username чатов, фильтрацию ботов и аккуратный экспорт данных.

---

## ✨ Основные возможности

- 🔑 Авторизация через Telegram API (`API_ID`, `API_HASH`, телефон)
- 📋 Поддержка парсинга нескольких чатов через запятую
- 🤖 Исключение ботов из списка участников
- 💾 Автоматическое сохранение результата в `users.txt` с таблицей
- 🧹 Очистка имён от невидимых Unicode-символов
- 🎨 Красивый GUI на PySide6 с логами и цветовым выделением
- 🟢 Зеленый текст успешных сообщений, 🔴 красный — ошибок

---

## 🛠️ Требования

- Python 3.8+
- Библиотеки:
  - `telethon`
  - `PySide6`
  - `tabulate`

---

## 🚀 Установка

```bash
git clone https://github.com/97shizzy/Updated-Telegram-Pars-tools-for-Sumxon.git
cd Updated-Telegram-Pars-tools-for-Sumxon-main
pip install telethon PySide6 tabulate
