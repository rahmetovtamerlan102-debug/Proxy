import os
import requests
import telebot
import random
import time
import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request

# ----- КОНФИГУРАЦИЯ -----
TOKEN = os.environ.get("TOKEN")
SUPPORT_USERNAME = os.environ.get("SUPPORT", "@ytvqi")
PORT = int(os.environ.get("PORT", 8080))

if not TOKEN:
    raise ValueError("❌ Токен не найден! Установи переменную окружения TOKEN")

bot = telebot.TeleBot(TOKEN)
working_proxies = []

# Flask приложение
app = Flask(__name__)

@app.route('/')
def index():
    return "Бот работает!", 200

# 16 источников прокси
SOURCES = [
    "https://raw.githubusercontent.com/SoliSpirit/mtproto/master/all_proxies.txt",
    "https://raw.githubusercontent.com/kort0881/telegram-proxy-collector/main/proxy_all.txt",
    "https://raw.githubusercontent.com/me2roid/mtproxy-collector/main/mtproto_proxies.txt",
    "https://raw.githubusercontent.com/ALIILAPRO/MTProto-Proxies/main/proxies.txt",
    "https://raw.githubusercontent.com/abbas0x0/MTProto-Proxies/main/proxies.txt",
    "https://raw.githubusercontent.com/iamshnoo/mtproto-proxy-list/main/proxies.txt",
    "https://raw.githubusercontent.com/ravener/telegram-proxy-list/main/proxies.txt",
    "https://raw.githubusercontent.com/Argh94/Proxy-List/main/MTProto.txt",
    "https://raw.githubusercontent.com/ProxyFreeList/mtproto/main/mtproto.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/mtproto.txt",
    "https://raw.githubusercontent.com/UserR3X/proxy-list/main/mtproto.txt",
    "https://raw.githubusercontent.com/ProxBro/socks-proxy-list/main/proxies.txt",
    "https://raw.githubusercontent.com/hukenovv/mtproto-proxy/main/proxy.txt",
    "https://raw.githubusercontent.com/kort0881/telegram-proxy-collector/main/proxy_ru.txt",
    "https://raw.githubusercontent.com/ALIILAPRO/MTProto-Proxies/main/proxies_ru.txt",
    "https://raw.githubusercontent.com/me2roid/mtproxy-collector/main/mtproto_proxies_ru.txt"
]

def fetch_proxies_from_sources():
    """Загружает прокси из всех источников"""
    all_proxies = []
    for url in SOURCES:
        try:
            name = url.split('/')[-1]
            print(f"📡 Загрузка: {name}")
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                proxies = [line.strip() for line in response.text.splitlines() if line.strip()]
                proxies = [p for p in proxies if p.startswith("tg://proxy")]
                print(f"  ✅ Найдено: {len(proxies)}")
                all_proxies.extend(proxies)
            else:
                print(f"  ❌ Ошибка {response.status_code}")
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
    return list(set(all_proxies))

def refresh_proxies():
    """Обновляет глобальный список прокси"""
    global working_proxies
    print("\n🔄 ОБНОВЛЕНИЕ СПИСКА ПРОКСИ")
    raw_proxies = fetch_proxies_from_sources()
    if not raw_proxies:
        print("⚠️ Не удалось получить прокси, сохраняю старый список")
        return
    working_proxies = raw_proxies
    print(f"🎉 Загружено {len(working_proxies)} прокси")

def refresh_loop():
    """Фоновый поток для обновления прокси раз в час"""
    while True:
        refresh_proxies()
        print("⏳ Ожидание 1 час до следующего обновления...")
        time.sleep(3600)

def self_ping():
    """Пинг самого себя чтобы Render не усыпил"""
    url = f"http://localhost:{PORT}/"
    while True:
        try:
            requests.get(url, timeout=10)
            print("🏓 Self-ping отправлен")
        except:
            pass
        time.sleep(300)

# ----- Команды бота -----
@bot.message_handler(commands=['start'])
def send_welcome(message):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🔁 ПОЛУЧИТЬ ПРОКСИ", callback_data="get_proxy"),
        InlineKeyboardButton("📡 СТАТУС", callback_data="status"),
        InlineKeyboardButton("📖 ИНСТРУКЦИЯ", callback_data="instruction"),
        InlineKeyboardButton("🆘 ПОДДЕРЖКА", callback_data="support")
    )
    bot.send_message(message.chat.id,
        "🛡️ *MTProto прокси для Telegram*\n👇 *Нажми на кнопку* 👇",
        parse_mode="Markdown", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "get_proxy")
def callback_get_proxy(call):
    if not working_proxies:
        bot.edit_message_text("❌ Нет прокси. Попробуйте позже.",
                              call.message.chat.id, call.message.message_id)
        return
    proxy = random.choice(working_proxies)
    bot.edit_message_text(
        f"✅ *Ваш прокси*\n\n`{proxy}`\n\n👉 *Нажми на ссылку*",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "status")
def callback_status(call):
    bot.edit_message_text(
        f"📡 *СТАТУС*\n\n🟢 Бот работает\n📡 Прокси в базе: {len(working_proxies)}\n🔄 Обновление каждый час",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "instruction")
def callback_instruction(call):
    bot.edit_message_text(
        "📖 *ИНСТРУКЦИЯ*\n\n"
        "1️⃣ Нажми 'ПОЛУЧИТЬ ПРОКСИ'\n"
        "2️⃣ Нажми на полученную ссылку\n"
        "3️⃣ Telegram сам добавит прокси\n"
        "4️⃣ Включи его в настройках\n\n"
        "🔄 Если прокси перестал работать — нажми кнопку ещё раз",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "support")
def callback_support(call):
    bot.edit_message_text(
        f"🆘 *ПОДДЕРЖКА*\n\n{SUPPORT_USERNAME}",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown")

# ----- Запуск -----
def run_flask():
    app.run(host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    print("🤖 Запуск бота...")
    
    # Принудительная загрузка прокси
    refresh_proxies()
    
    # Запуск фонового обновления
    threading.Thread(target=refresh_loop, daemon=True).start()
    
    # Запуск Flask (веб-сервер)
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Запуск self-ping
    threading.Thread(target=self_ping, daemon=True).start()
    
    print("✅ Бот готов!")
    bot.infinity_polling()
