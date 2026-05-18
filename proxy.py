import os
import requests
import telebot
import random
import time
import threading
import socket
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request

# ----- КОНФИГУРАЦИЯ -----
TOKEN = os.environ.get("TOKEN")
SUPPORT_USERNAME = os.environ.get("SUPPORT", "@ytvqi")
PORT = int(os.environ.get("PORT", 8080))
FILTER_BY_COUNTRY = False   # Для максимального количества отключаем фильтрацию
MAX_WORKERS = 100           # Количество параллельных проверок
TIMEOUT = 3                 # Таймаут TCP-соединения

if not TOKEN:
    raise ValueError("❌ Токен не найден! Установи переменную окружения TOKEN")

bot = telebot.TeleBot(TOKEN)
working_proxies = []

app = Flask(__name__)
@app.route('/')
def index():
    return "Бот работает!", 200

# 🔥 35+ источников прокси (максимальный сбор)
SOURCES = [
    # Основные репозитории
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
    "https://raw.githubusercontent.com/me2roid/mtproxy-collector/main/mtproto_proxies_ru.txt",
    # Дополнительные (новые)
    "https://raw.githubusercontent.com/1337r0b0t/MTProto-Proxy-List/main/proxies.txt",
    "https://raw.githubusercontent.com/AliaksandrShemet/MTProtoProxy/master/proxy.txt",
    "https://raw.githubusercontent.com/zhkk/mtproto-proxy-list/main/list.txt",
    "https://raw.githubusercontent.com/FadeMind/mtproxy-collector/master/mtproto.txt",
    "https://raw.githubusercontent.com/jonaski/mtproto-proxy-list/master/list.txt",
    "https://raw.githubusercontent.com/MIMBCD-UI/mtproto-proxy-list/main/list.txt",
    "https://raw.githubusercontent.com/novitae/proxy_list/main/MTProto.txt",
    "https://raw.githubusercontent.com/reklatsmasters/proxy-list/main/mtproto.txt",
    "https://raw.githubusercontent.com/SpEcHiDe/MTProtoProxyList/master/list.txt",
    "https://raw.githubusercontent.com/tg12/telegram_proxy_list/main/mtproto.txt",
    "https://raw.githubusercontent.com/XTREME-CYBER-TEAM/MTProto-Proxies/main/proxies.txt",
    "https://raw.githubusercontent.com/Yukii-Dev/MTProto-Proxies/main/proxies.txt",
    "https://raw.githubusercontent.com/Zalexanninev15/MTProto-Proxy-List/main/proxy.txt",
    "https://raw.githubusercontent.com/ZazaP/MTPROTO_proxy/master/proxies.txt",
    "https://raw.githubusercontent.com/AlphaParl/proxy-list/main/MTProto.txt",
    "https://raw.githubusercontent.com/BadWolf-0xff/mtproto-proxy-list/main/proxies.txt",
    "https://raw.githubusercontent.com/BlackJack-Network/mtproto-proxy-list/main/proxies.txt",
    "https://raw.githubusercontent.com/Blasium/MTProto-Proxy-List/main/proxies.txt",
    "https://raw.githubusercontent.com/BlastTeck/MTProto-Proxies/main/proxies.txt",
    "https://raw.githubusercontent.com/BS-Info/mtproto-proxy-list/main/proxies.txt",
    "https://raw.githubusercontent.com/CakeCrusher/mtproto-proxy-list/main/proxies.txt",
]

def fetch_proxies_from_sources():
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

def check_proxy_tcp(proxy_url):
    """Проверка через TCP-соединение к порту 443"""
    try:
        match = re.search(r"server=([^&]+)", proxy_url)
        if not match:
            return False
        server = match.group(1)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        result = sock.connect_ex((server, 443))
        sock.close()
        return result == 0
    except:
        return False

def refresh_proxies():
    global working_proxies
    print("\n🔄 ОБНОВЛЕНИЕ СПИСКА ПРОКСИ (максимальный сбор)")
    raw = fetch_proxies_from_sources()
    if not raw:
        print("⚠️ Не удалось получить прокси, сохраняю старый")
        return

    alive = []
    print(f"🧪 Проверяю {len(raw)} прокси через TCP-соединение...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_proxy = {executor.submit(check_proxy_tcp, proxy): proxy for proxy in raw}
        for future in as_completed(future_to_proxy):
            proxy = future_to_proxy[future]
            if future.result():
                alive.append(proxy)
                if len(alive) % 50 == 0:
                    print(f"✅ Найдено живых: {len(alive)}")

    if alive:
        working_proxies = alive
        print(f"🎉 Загружено {len(working_proxies)} живых прокси")
    else:
        print("⚠️ Живых прокси нет, сохраняю старый список")

def refresh_loop():
    while True:
        refresh_proxies()
        print("⏳ Ожидание 15 минут до следующего обновления...")
        time.sleep(900)

def self_ping():
    url = f"http://localhost:{PORT}/"
    while True:
        try:
            requests.get(url, timeout=10)
            print("🏓 Self-ping")
        except:
            pass
        time.sleep(300)

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
        bot.edit_message_text("❌ Нет живых прокси. Попробуйте позже.",
                              call.message.chat.id, call.message.message_id)
        return
    proxy = random.choice(working_proxies)
    bot.edit_message_text(
        f"✅ *Ваш прокси (проверен)*\n\n`{proxy}`\n\n👉 *Нажми на ссылку*",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "status")
def callback_status(call):
    bot.edit_message_text(
        f"📡 *СТАТУС*\n\n🟢 Бот работает\n📡 Живых прокси: {len(working_proxies)}\n🔄 Обновление каждые 15 мин",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "instruction")
def callback_instruction(call):
    bot.edit_message_text(
        "📖 *ИНСТРУКЦИЯ*\n\n"
        "1️⃣ Нажми 'ПОЛУЧИТЬ ПРОКСИ'\n"
        "2️⃣ Нажми на полученную ссылку\n"
        "3️⃣ Telegram сам добавит прокси\n"
        "4️⃣ Включи в настройках\n\n"
        "🔄 Если не работает — нажми кнопку ещё раз",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "support")
def callback_support(call):
    bot.edit_message_text(
        f"🆘 *ПОДДЕРЖКА*\n\n{SUPPORT_USERNAME}",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(commands=['force_update'])
def force_update(message):
    refresh_proxies()
    bot.reply_to(message, f"🔄 Список прокси обновлён! Живых прокси: {len(working_proxies)}")

def run_flask():
    app.run(host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    print("🤖 Запуск бота...")
    refresh_proxies()
    threading.Thread(target=refresh_loop, daemon=True).start()
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=self_ping, daemon=True).start()
    print("✅ Бот готов!")
    bot.infinity_polling()
