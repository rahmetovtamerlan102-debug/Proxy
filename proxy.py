import os
import requests
import telebot
import random
import time
import threading
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request

# ----- КОНФИГУРАЦИЯ -----
TOKEN = os.environ.get("TOKEN", "8893110778:AAFTwRXbdy2fWopb1DyipCXpY3m8-g-ovqk")
SUPPORT_USERNAME = os.environ.get("SUPPORT", "@ytvqi")
PORT = int(os.environ.get("PORT", 8080))
# -------------------------

bot = telebot.TeleBot(TOKEN)
working_proxies = []

# Flask для Render
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
