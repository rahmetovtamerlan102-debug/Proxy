import os
import requests
import telebot
import random
import time
import threading
import socket
import re
from concurrent.futures import ThreadPoolExecutor
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask

TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    raise ValueError("❌ TOKEN не задан")

bot = telebot.TeleBot(TOKEN)
working_proxies = []

app = Flask(__name__)
@app.route('/')
def home():
    return "Бот работает"

SOURCES = [
    "https://raw.githubusercontent.com/SoliSpirit/mtproto/master/all_proxies.txt",
    "https://raw.githubusercontent.com/kort0881/telegram-proxy-collector/main/proxy_all.txt",
    "https://raw.githubusercontent.com/me2roid/mtproxy-collector/main/mtproto_proxies.txt",
    "https://raw.githubusercontent.com/ALIILAPRO/MTProto-Proxies/main/proxies.txt",
    "https://raw.githubusercontent.com/abbas0x0/MTProto-Proxies/main/proxies.txt",
    "https://raw.githubusercontent.com/iamshnoo/mtproto-proxy-list/main/proxies.txt",
    "https://raw.githubusercontent.com/ravener/telegram-proxy-list/main/proxies.txt",
]

def fetch():
    all_proxies = []
    for url in SOURCES:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                proxies = [line.strip() for line in r.text.splitlines() if line.strip().startswith("tg://proxy")]
                all_proxies.extend(proxies)
        except:
            pass
    return list(set(all_proxies))

def tcp_check(proxy):
    try:
        m = re.search(r"server=([^&]+)", proxy)
        if not m:
            return False
        ip = m.group(1)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        sock.connect_ex((ip, 443))
        sock.close()
        return True
    except:
        return False

def refresh():
    global working_proxies
    print("🔄 Загрузка прокси...")
    raw = fetch()
    if not raw:
        return
    alive = []
    with ThreadPoolExecutor(max_workers=50) as ex:
        results = ex.map(tcp_check, raw)
        for proxy, ok in zip(raw, results):
            if ok:
                alive.append(proxy)
    working_proxies = alive
    print(f"✅ Загружено {len(working_proxies)} живых прокси")

def refresh_loop():
    while True:
        refresh()
        time.sleep(1800)  # 30 минут

def keep_alive():
    while True:
        try:
            requests.get("http://localhost:8080", timeout=5)
        except:
            pass
        time.sleep(300)

@bot.message_handler(commands=['start'])
def start(m):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔁 ПОЛУЧИТЬ ПРОКСИ", callback_data="get"))
    bot.send_message(m.chat.id, "🛡️ MTProto прокси\n👇 Нажми кнопку", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == "get")
def send(c):
    if not working_proxies:
        bot.edit_message_text("❌ Нет прокси", c.message.chat.id, c.message.message_id)
        return
    proxy = random.choice(working_proxies)
    bot.edit_message_text(f"✅ Ваш прокси\n`{proxy}`\n👉 Нажми на ссылку", c.message.chat.id, c.message.message_id, parse_mode="Markdown")

if __name__ == "__main__":
    print("🤖 Запуск...")
    refresh()
    threading.Thread(target=refresh_loop, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8080), daemon=True).start()
    bot.infinity_polling()
