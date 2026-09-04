# -*- coding: utf-8 -*-
import sqlite3
import random
import datetime
import json
import asyncio
import logging
import os
import time
from dotenv import load_dotenv
from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = [6621617827]

GRAMADS_API_KEY = os.getenv('GRAMADS_API_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1ODM2MyIsImp0aSI6IjM4MWIyY2RmLThkNzYtNDkzMC1hNGZiLWYwOTAwZDdiYjlhYSIsIm5hbWUiOiJFYXJuU2F2ZWxpeSIsImJvdGlkIjoiMjI3NzEiLCJodHRwOi8vc2NoZW1hcy54bWxzb2FwLm9yZy93cy8yMDA1LzA1L2lkZW50aXR5L2NsYWltcy9uYW1laWRlbnRpZmllciI6IjU4MzYzIiwibmJmIjoxNzg4Mjg3MjQ3LCJleHAiOjE3ODg0OTYwNDcsImlzcyI6IlN0dWdub3YiLCJhdWQiOiJVc2VycyJ9.p_85j4_PQfJ6oO_eiJqkPHB6KQFxCfr4zm2yj9Gjbpk')

MIN_EARN = 2.3
MAX_EARN = 3.5
DAILY_CLICK_LIMIT = 50
WITHDRAW_MIN = 120
REFERRAL_BONUS = 3
REFERRAL_PERCENT = 10
DB_NAME = "earn_bot.db"
FAKE_TOP_FILE = "fake_top.json"

START_TIME = time.time()
ERROR_COUNT = 0

CHANNELS = [
    {'id': '@spookyscripts', 'name': 'Spooky Scripts', 'url': 'https://t.me/spookyscripts'},
    {'id': '-1003788328996', 'name': 'SPOOKY MOD', 'url': 'https://t.me/+GMHDq5Fij2M5MmFh'},
    {'id': '-1004356916182', 'name': 'OUTLOW SCRIPTS', 'url': 'https://t.me/+GIrw6Qj8tkZiMzhh'},
    {'id': '@EarnSaveliy', 'name': 'EarnSaveliy', 'url': 'https://t.me/EarnSaveliy'}
]

def init_fake_top():
    default_fake = [
        {"username": "@kotnavoine", "balance": 2610},
        {"username": "@mittsf2", "balance": 1704},
        {"username": "@demon666_597", "balance": 680},
        {"username": "@FGPIDORS", "balance": 676},
        {"username": "@thisgoodworld", "balance": 312},
        {"username": "⭐ СТАЛЬНОЙ ВОИН", "balance": 287.5},
        {"username": "🔥 ОГНЕННЫЙ ЛИС", "balance": 254.3},
        {"username": "💎 АЛМАЗНЫЙ БАРОН", "balance": 221.8},
        {"username": "👑 ТЁМНЫЙ ВЛАСТЕЛИН", "balance": 198.2},
        {"username": "🌙 ЛУННЫЙ СТРАЖ", "balance": 167.9}
    ]
    try:
        with open(FAKE_TOP_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not data:
                raise ValueError
            return data
    except:
        with open(FAKE_TOP_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_fake, f, ensure_ascii=False, indent=2)
        return default_fake

def init_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE,
        first_name TEXT,
        username TEXT,
        balance REAL DEFAULT 0,
        total_earned REAL DEFAULT 0,
        total_withdrawn REAL DEFAULT 0,
        clicks INTEGER DEFAULT 0,
        avg_earning REAL DEFAULT 0,
        last_click TEXT,
        clicks_today INTEGER DEFAULT 0,
        last_click_date TEXT,
        last_visit TEXT,
        referral_code TEXT UNIQUE,
        referrer_id INTEGER,
        referral_count INTEGER DEFAULT 0,
        referral_earned REAL DEFAULT 0,
        daily_bonus_date TEXT,
        is_banned INTEGER DEFAULT 0,
        created_at TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS withdrawals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        status TEXT DEFAULT 'pending',
        requested_at TEXT,
        completed_at TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS referrals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        referrer_id INTEGER,
        referred_id INTEGER,
        created_at TEXT
    )''')
    conn.commit()
    conn.close()

def get_db():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def get_user(tg_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE telegram_id = ?", (tg_id,))
    user = c.fetchone()
    conn.close()
    return user

def update_user(tg_id, **kwargs):
    conn = get_db()
    c = conn.cursor()
    for key, val in kwargs.items():
        c.execute(f"UPDATE users SET {key} = ? WHERE telegram_id = ?", (val, tg_id))
    conn.commit()
    conn.close()

def register_user(tg_id, first_name, username, ref_code=None):
    user = get_user(tg_id)
    if user:
        update_user(tg_id, first_name=first_name, username=username, last_visit=datetime.datetime.now().isoformat())
        return get_user(tg_id)
    code = f"ref_{tg_id}_{random.randint(1000,9999)}"
    referrer_id = None
    if ref_code:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE referral_code = ?", (ref_code,))
        r = c.fetchone()
        conn.close()
        if r:
            referrer_id = r[0]
    now = datetime.datetime.now().isoformat()
    conn = get_db()
    c = conn.cursor()
    c.execute('''INSERT INTO users (telegram_id, first_name, username, referral_code, referrer_id, created_at, last_visit)
                 VALUES (?,?,?,?,?,?,?)''', (tg_id, first_name, username, code, referrer_id, now, now))
    uid = c.lastrowid
    if referrer_id:
        c.execute("UPDATE users SET balance = balance + ?, referral_count = referral_count + 1 WHERE id = ?",
                  (REFERRAL_BONUS, referrer_id))
        c.execute("INSERT INTO referrals (referrer_id, referred_id, created_at) VALUES (?,?,?)",
                  (referrer_id, uid, now))
    conn.commit()
    conn.close()
    return get_user(tg_id)

def get_top_users(limit=10):
    fake_users = init_fake_top()
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT username, balance FROM users WHERE is_banned=0 ORDER BY balance DESC")
    real_users = c.fetchall()
    conn.close()
    all_users = []
    for u in fake_users:
        all_users.append({'username': u['username'], 'balance': u['balance'], 'is_fake': True})
    for u in real_users:
        all_users.append({'username': u[0] or 'Без имени', 'balance': u[1], 'is_fake': False})
    all_users.sort(key=lambda x: x['balance'], reverse=True)
    result = [(u['username'], u['balance']) for u in all_users[:limit]]
    return result

def get_user_rank(tg_id):
    fake_users = init_fake_top()
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT telegram_id, balance FROM users WHERE is_banned=0")
    real_users = c.fetchall()
    conn.close()
    all_balances = []
    user_balance = 0
    for u in fake_users:
        all_balances.append(u['balance'])
    for u in real_users:
        if u[0] == tg_id:
            user_balance = u[1]
        all_balances.append(u[1])
    rank = 1
    for bal in all_balances:
        if bal > user_balance:
            rank += 1
    return rank

def get_total_users():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE is_banned=0")
    real_count = c.fetchone()[0]
    conn.close()
    fake_users = init_fake_top()
    fake_count = len(fake_users)
    return real_count + fake_count

def get_active_users():
    conn = get_db()
    c = conn.cursor()
    day_ago = (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat()
    c.execute("SELECT COUNT(*) FROM users WHERE last_visit > ? AND is_banned=0", (day_ago,))
    count = c.fetchone()[0]
    conn.close()
    return count

def get_total_clicks():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT SUM(clicks) FROM users WHERE is_banned=0")
    total = c.fetchone()[0] or 0
    conn.close()
    return total

def earn_stars(tg_id):
    user = get_user(tg_id)
    if not user:
        return None, "Пользователь не найден"
    if user[18]:
        return None, "❌ Вы забанены!"
    today = datetime.date.today().isoformat()
    if user[11] == today and user[10] >= DAILY_CLICK_LIMIT:
        return None, f"⚠️ Лимит {DAILY_CLICK_LIMIT} кликов на сегодня!"
    amount = round(random.uniform(MIN_EARN, MAX_EARN), 1)
    new_balance = user[4] + amount
    new_total = user[5] + amount
    new_clicks = user[7] + 1
    new_avg = round(new_total / new_clicks, 2)
    now = datetime.datetime.now().isoformat()
    today_date = datetime.date.today().isoformat()
    new_today = user[10] + 1 if user[11] == today_date else 1
    update_user(tg_id, balance=new_balance, total_earned=new_total, clicks=new_clicks,
                avg_earning=new_avg, last_click=now, last_visit=now,
                clicks_today=new_today, last_click_date=today_date)
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT referrer_id FROM users WHERE telegram_id = ?", (tg_id,))
    ref = c.fetchone()
    if ref and ref[0]:
        bonus = round(amount * REFERRAL_PERCENT / 100, 2)
        c.execute("UPDATE users SET balance = balance + ?, referral_earned = referral_earned + ? WHERE id = ?",
                  (bonus, bonus, ref[0]))
        conn.commit()
    conn.close()
    return amount, None

def get_daily_bonus(tg_id):
    user = get_user(tg_id)
    if not user:
        return None, "Пользователь не найден"
    today = datetime.date.today().isoformat()
    if user[17] == today:
        return None, "⚠️ Бонус уже получен сегодня!"
    amount = random.randint(5, 15)
    update_user(tg_id, balance=user[4]+amount, total_earned=user[5]+amount,
                daily_bonus_date=today, last_visit=datetime.datetime.now().isoformat())
    return amount, None

def main_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("💰 Заработать", "👤 Профиль")
    kb.row("👥 Друзья", "💸 Вывод")
    kb.row("🏆 Топ", "🎁 Бонус")
    return kb

def admin_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📊 Статистика", "👥 Топ-50")
    kb.row("🔍 Поиск", "✉️ Рассылка")
    kb.row("💰 Начислить", "🚫 Бан")
    kb.row("◀️ В главное меню")
    return kb

bot = TeleBot(TOKEN)

def is_subscribed(user_id, channel_id):
    try:
        member = bot.get_chat_member(channel_id, user_id)
        return member.status not in ['left', 'kicked', 'banned']
    except:
        return True

def get_unsubscribed(user_id):
    result = []
    for ch in CHANNELS:
        if not is_subscribed(user_id, ch['id']):
            result.append(ch)
    return result

def sub_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    for ch in CHANNELS:
        kb.add(InlineKeyboardButton(f"📢 {ch['name']}", url=ch['url']))
    kb.add(InlineKeyboardButton("✅ Проверить", callback_data="check_sub"))
    return kb

@bot.message_handler(commands=['start'])
def start(msg):
    uid = msg.from_user.id
    name = msg.from_user.first_name
    uname = msg.from_user.username or "без username"
    ref = msg.text.split()[1] if len(msg.text.split()) > 1 else None
    register_user(uid, name, uname, ref)
    
    unsub = get_unsubscribed(uid)
    if unsub and uid not in ADMIN_IDS:
        channels_text = "\n".join([f"• {ch['name']}" for ch in unsub])
        bot.send_message(
            msg.chat.id,
            f"⚠️ Подпишитесь на каналы:\n\n{channels_text}\n\nЗатем нажмите «✅ Проверить»",
            reply_markup=sub_keyboard()
        )
        return
    
    user = get_user(uid)
    bonus_msg = ""
    today = datetime.date.today().isoformat()
    if user[17] != today:
        ba = random.randint(5, 15)
        update_user(uid, balance=user[4]+ba, total_earned=user[5]+ba, daily_bonus_date=today)
        bonus_msg = f"\n\n🎁 Бонус: +{ba} ⭐!"
    bot.send_message(msg.chat.id,
        f"⭐ Добро пожаловать, {name}!\n\n"
        f"💰 Баланс: {user[4]:.1f} ⭐\n"
        f"📈 Заработано: {user[5]:.1f} ⭐{bonus_msg}\n\n"
        f"Жми «💰 Заработать» и получай ⭐!",
        reply_markup=main_kb())

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub(call):
    uid = call.from_user.id
    unsub = get_unsubscribed(uid)
    
    if unsub:
        channels_text = "\n".join([f"• {ch['name']}" for ch in unsub])
        bot.answer_callback_query(call.id, "❌ Не подписан!", show_alert=True)
        try:
            bot.edit_message_text(
                f"⚠️ Остались каналы:\n\n{channels_text}\n\nНажмите «✅ Проверить» после подписки",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=sub_keyboard()
            )
        except:
            pass
    else:
        bot.answer_callback_query(call.id, "✅ Готово!", show_alert=True)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        user = get_user(uid)
        bot.send_message(call.message.chat.id,
            f"⭐ Добро пожаловать!\n\n💰 Баланс: {user[4]:.1f} ⭐\n\nЖми «💰 Заработать»!",
            reply_markup=main_kb())

@bot.message_handler(func=lambda m: m.text == "💰 Заработать")
def earn(msg):
    global ERROR_COUNT
    uid = msg.from_user.id
    user = get_user(uid)
    if not user:
        bot.send_message(msg.chat.id, "Напишите /start")
        return
    
    unsub = get_unsubscribed(uid)
    if unsub and uid not in ADMIN_IDS:
        channels_text = "\n".join([f"• {ch['name']}" for ch in unsub])
        bot.send_message(msg.chat.id, f"⚠️ Подпишитесь:\n\n{channels_text}", reply_markup=sub_keyboard())
        return
    
    bot.send_message(msg.chat.id, "📺 Реклама...")
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(show_advert(uid, GRAMADS_API_KEY))
        loop.close()
        if success:
            amount, err = earn_stars(uid)
            if err:
                bot.send_message(msg.chat.id, err)
                return
            user = get_user(uid)
            bot.send_message(msg.chat.id,
                f"⭐ +{amount} ⭐!\n💰 Баланс: {user[4]:.1f} ⭐\n📊 Сегодня: {user[10]}/{DAILY_CLICK_LIMIT}",
                reply_markup=main_kb())
        else:
            bot.send_message(msg.chat.id, "❌ Ошибка рекламы")
    except Exception as e:
        ERROR_COUNT += 1
        logging.error(f"Earn error: {e}")
        bot.send_message(msg.chat.id, "❌ Ошибка")

@bot.message_handler(func=lambda m: m.text == "👤 Профиль")
def profile(msg):
    uid = msg.from_user.id
    user = get_user(uid)
    if not user:
        bot.send_message(msg.chat.id, "Напишите /start")
        return
    rank = get_user_rank(uid)
    total = get_total_users()
    bot.send_message(msg.chat.id,
        f"👤 ПРОФИЛЬ\n\n💰 Баланс: {user[4]:.1f} ⭐\n📈 Заработано: {user[5]:.1f} ⭐\n"
        f"💸 Выведено: {user[6]:.1f} ⭐\n🔄 Кликов: {user[7]}\n"
        f"👥 Друзей: {user[15]}\n🏆 Место: #{rank} из {total}\n"
        f"🎯 Сегодня: {user[10]}/{DAILY_CLICK_LIMIT}",
        reply_markup=main_kb())

@bot.message_handler(func=lambda m: m.text == "👥 Друзья")
def friends(msg):
    uid = msg.from_user.id
    user = get_user(uid)
    if not user:
        bot.send_message(msg.chat.id, "Напишите /start")
        return
    bot.send_message(msg.chat.id,
        f"👥 РЕФЕРАЛКА\n\n💰 За друга: +{REFERRAL_BONUS} ⭐\n"
        f"📊 Пассив: {REFERRAL_PERCENT}%\n\n"
        f"🔗 Ссылка:\nhttps://t.me/{(bot.get_me()).username}?start={user[13]}\n\n"
        f"👥 Друзей: {user[15]}\n💰 Заработано: {user[16]:.1f} ⭐",
        reply_markup=main_kb())

@bot.message_handler(func=lambda m: m.text == "🏆 Топ")
def top(msg):
    users = get_top_users(10)
    uid = msg.from_user.id
    rank = get_user_rank(uid)
    text = "🏆 ТОП-10\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, (uname, bal) in enumerate(users):
        m = medals[i] if i < 3 else f"{i+1}."
        text += f"{m} {uname} — {bal:.1f} ⭐\n"
    text += f"\n📊 Ваше место: #{rank}"
    bot.send_message(msg.chat.id, text, reply_markup=main_kb())

@bot.message_handler(func=lambda m: m.text == "🎁 Бонус")
def bonus(msg):
    uid = msg.from_user.id
    amount, err = get_daily_bonus(uid)
    if err:
        bot.send_message(msg.chat.id, err, reply_markup=main_kb())
        return
    user = get_user(uid)
    bot.send_message(msg.chat.id,
        f"🎁 +{amount} ⭐!\n💰 Баланс: {user[4]:.1f} ⭐",
        reply_markup=main_kb())

@bot.message_handler(func=lambda m: m.text == "💸 Вывод")
def withdraw_menu(msg):
    bot.send_message(msg.chat.id,
        f"💸 ВЫВОД\n\nМинимум: {WITHDRAW_MIN} ⭐\n\n/withdraw СУММА",
        reply_markup=main_kb())

@bot.message_handler(commands=['withdraw'])
def withdraw(msg):
    uid = msg.from_user.id
    user = get_user(uid)
    if not user:
        bot.send_message(msg.chat.id, "Напишите /start")
        return
    args = msg.text.split()
    if len(args) < 2:
        bot.send_message(msg.chat.id, "Укажите сумму: /withdraw 10")
        return
    try:
        amount = float(args[1])
    except:
        bot.send_message(msg.chat.id, "Введите число")
        return
    if amount < WITHDRAW_MIN:
        bot.send_message(msg.chat.id, f"Минимум: {WITHDRAW_MIN} ⭐")
        return
    if amount > user[4]:
        bot.send_message(msg.chat.id, "Недостаточно средств")
        return
    new_balance = user[4] - amount
    new_withdrawn = user[6] + amount
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET balance = ?, total_withdrawn = ? WHERE telegram_id = ?",
              (new_balance, new_withdrawn, uid))
    now = datetime.datetime.now().isoformat()
    c.execute("INSERT INTO withdrawals (user_id, amount, requested_at) VALUES (?, ?, ?)",
              (user[0], amount, now))
    conn.commit()
    conn.close()
    bot.send_message(msg.chat.id,
        f"✅ Заявка на {amount} ⭐ отправлена!",
        reply_markup=main_kb())

# ========== АДМИН-ПАНЕЛЬ ==========

@bot.message_handler(commands=['admin'])
def admin(msg):
    if msg.from_user.id not in ADMIN_IDS:
        bot.send_message(msg.chat.id, "❌ Нет доступа")
        return
    bot.send_message(msg.chat.id, "🛡️ АДМИН-ПАНЕЛЬ", reply_markup=admin_kb())

@bot.message_handler(func=lambda m: m.text == "📊 Статистика")
def stats(msg):
    if msg.from_user.id not in ADMIN_IDS:
        return
    total = get_total_users()
    active = get_active_users()
    clicks = get_total_clicks()
    uptime = int(time.time() - START_TIME)
    hours = uptime // 3600
    minutes = (uptime % 3600) // 60
    seconds = uptime % 60
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT SUM(total_earned) FROM users WHERE is_banned=0")
    earned = c.fetchone()[0] or 0
    c.execute("SELECT SUM(total_withdrawn) FROM users WHERE is_banned=0")
    withdrawn = c.fetchone()[0] or 0
    conn.close()
    
    bot.send_message(msg.chat.id,
        f"📊 СТАТИСТИКА\n\n"
        f"👥 Участников: {total}\n"
        f"🟢 Активных (24ч): {active}\n"
        f"🔄 Всего кликов: {clicks}\n"
        f"⭐ Заработано: {earned:.1f}\n"
        f"💸 Выведено: {withdrawn:.1f}\n"
        f"❌ Ошибок: {ERROR_COUNT}\n"
        f"⏱ Время работы: {hours}ч {minutes}м {seconds}с",
        reply_markup=admin_kb())

@bot.message_handler(func=lambda m: m.text == "👥 Топ-50")
def top50(msg):
    if msg.from_user.id not in ADMIN_IDS:
        return
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT telegram_id, first_name, username, balance, total_earned, clicks FROM users WHERE is_banned=0 ORDER BY balance DESC LIMIT 50")
    users = c.fetchall()
    conn.close()
    
    if not users:
        bot.send_message(msg.chat.id, "Нет пользователей", reply_markup=admin_kb())
        return
    
    text = "👥 ТОП-50 ПО БАЛАНСУ\n\n"
    for i, u in enumerate(users):
        text += f"{i+1}. {u[1]} (@{u[2] or '—'}) — {u[3]:.1f} ⭐\n"
    
    bot.send_message(msg.chat.id, text, reply_markup=admin_kb())

@bot.message_handler(func=lambda m: m.text == "🔍 Поиск")
def search_prompt(msg):
    if msg.from_user.id not in ADMIN_IDS:
        return
    bot.send_message(msg.chat.id, 
        "🔍 ПОИСК ПОЛЬЗОВАТЕЛЯ\n\n"
        "/user ID — по Telegram ID\n"
        "/user @username — по username",
        reply_markup=admin_kb())

@bot.message_handler(commands=['user'])
def user_info(msg):
    if msg.from_user.id not in ADMIN_IDS:
        return
    args = msg.text.split()
    if len(args) < 2:
        bot.send_message(msg.chat.id, "/user ID или
