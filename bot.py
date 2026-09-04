# -*- coding: utf-8 -*-
import sqlite3
import random
import datetime
import json
import asyncio
import logging
import os
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

# Обязательные каналы для подписки
REQUIRED_CHANNELS = [
    {
        'id': '@spookyscripts',
        'name': 'Spooky Scripts',
        'url': 'https://t.me/spookyscripts'
    },
    {
        'id': '-1003788328996',
        'name': 'Канал 2',
        'url': 'https://t.me/+GMHDq5Fij2M5MmFh'
    },
    {
        'id': '-1004356916182',
        'name': 'OUTLOW SCRIPTS',
        'url': 'https://t.me/+GIrw6Qj8tkZiMzhh'
    }
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
    kb.row("📊 Статистика", "👥 Все пользователи")
    kb.row("🔝 ТОП-20", "✉️ Рассылка")
    kb.row("◀️ В главное меню")
    return kb

def check_subscriptions(user_id):
    """Проверяет подписку на все обязательные каналы"""
    not_subscribed = []
    for channel in REQUIRED_CHANNELS:
        try:
            member = bot.get_chat_member(channel['id'], user_id)
            if member.status in ['left', 'kicked', 'banned']:
                not_subscribed.append(channel)
        except Exception as e:
            logging.error(f"Ошибка проверки подписки на {channel['id']}: {e}")
            # Если ошибка - считаем что не подписан
            not_subscribed.append(channel)
    return not_subscribed

def create_subscription_keyboard():
    """Создаёт клавиатуру с кнопками для подписки"""
    kb = InlineKeyboardMarkup(row_width=1)
    for channel in REQUIRED_CHANNELS:
        kb.add(InlineKeyboardButton(f"📢 {channel['name']}", url=channel['url']))
    kb.add(InlineKeyboardButton("✅ Я подписался!", callback_data="check_sub"))
    return kb

bot = TeleBot(TOKEN)

def send_subscription_required(message):
    """Отправляет сообщение о необходимости подписки"""
    not_subscribed = check_subscriptions(message.from_user.id)
    channels_list = "\n".join([f"• {ch['name']} - {ch['url']}" for ch in not_subscribed])
    bot.send_message(
        message.chat.id,
        f"⚠️ Для использования бота необходимо подписаться на все каналы:\n\n"
        f"{channels_list}\n\n"
        f"После подписки нажмите кнопку «✅ Я подписался!»",
        reply_markup=create_subscription_keyboard()
    )

@bot.message_handler(commands=['start'])
def start(msg):
    uid = msg.from_user.id
    name = msg.from_user.first_name
    uname = msg.from_user.username or "без username"
    ref = msg.text.split()[1] if len(msg.text.split()) > 1 else None
    user = register_user(uid, name, uname, ref)
    
    # ПРОВЕРЯЕМ ПОДПИСКУ ДЛЯ ВСЕХ (и старых и новых)
    not_subscribed = check_subscriptions(uid)
    
    if not_subscribed:
        # Пользователь не подписан на все каналы
        channels_list = "\n".join([f"• {ch['name']} - {ch['url']}" for ch in not_subscribed])
        bot.send_message(
            msg.chat.id,
            f"⚠️ Для использования бота необходимо подписаться на все каналы:\n\n"
            f"{channels_list}\n\n"
            f"После подписки нажмите кнопку «✅ Я подписался!»",
            reply_markup=create_subscription_keyboard()
        )
        return
    
    # Пользователь подписан на все каналы
    bonus_msg = ""
    today = datetime.date.today().isoformat()
    if user[17] != today:
        ba = random.randint(5, 15)
        update_user(uid, balance=user[4]+ba, total_earned=user[5]+ba, daily_bonus_date=today)
        bonus_msg = f"\n\n🎁 Ежедневный бонус: +{ba} ⭐!"
    ref_msg = "\n\n👥 Вы пришли по реферальной ссылке!" if user[14] else ""
    bot.send_message(msg.chat.id,
        f"⭐ Добро пожаловать в EarnSaveliyBot, {name}!\n\n"
        f"💰 Баланс: {user[4]:.1f} ⭐\n"
        f"📈 Заработано: {user[5]:.1f} ⭐{bonus_msg}{ref_msg}\n\n"
        f"Нажимай «💰 Заработать» и смотри рекламу, чтобы получить от {MIN_EARN} до {MAX_EARN} ⭐!\n"
        f"Зови друзей и получай {REFERRAL_PERCENT}% от их дохода! 🚀",
        reply_markup=main_kb())

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub_callback(call):
    uid = call.from_user.id
    not_subscribed = check_subscriptions(uid)
    
    if not_subscribed:
        # Всё ещё не подписан
        channels_list = "\n".join([f"• {ch['name']}" for ch in not_subscribed])
        bot.answer_callback_query(call.id, "❌ Вы не подписаны на все каналы!", show_alert=True)
        try:
            bot.edit_message_text(
                f"⚠️ Вы не подписаны на:\n\n{channels_list}\n\n"
                f"Подпишитесь и нажмите «✅ Я подписался!» снова",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=create_subscription_keyboard()
            )
        except:
            pass
    else:
        # Подписан на все каналы
        bot.answer_callback_query(call.id, "✅ Подписка подтверждена!", show_alert=True)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        
        # Показываем главное меню
        user = get_user(uid)
        if not user:
            user = register_user(uid, call.from_user.first_name, call.from_user.username or "без username")
        
        bonus_msg = ""
        today = datetime.date.today().isoformat()
        if user[17] != today:
            ba = random.randint(5, 15)
            update_user(uid, balance=user[4]+ba, total_earned=user[5]+ba, daily_bonus_date=today)
            bonus_msg = f"\n\n🎁 Ежедневный бонус: +{ba} ⭐!"
        
        bot.send_message(
            call.message.chat.id,
            f"⭐ Добро пожаловать в EarnSaveliyBot, {call.from_user.first_name}!\n\n"
            f"💰 Баланс: {user[4]:.1f} ⭐\n"
            f"📈 Заработано: {user[5]:.1f} ⭐{bonus_msg}\n\n"
            f"Нажимай «💰 Заработать» и смотри рекламу, чтобы получить от {MIN_EARN} до {MAX_EARN} ⭐!\n"
            f"Зови друзей и получай {REFERRAL_PERCENT}% от их дохода! 🚀",
            reply_markup=main_kb()
        )

# Декоратор для проверки подписки перед любым действием
def subscription_required(func):
    def wrapper(message):
        uid = message.from_user.id
        
        # Пропускаем админов
        if uid in ADMIN_IDS:
            return func(message)
        
        # Проверяем подписку
        not_subscribed = check_subscriptions(uid)
        if not_subscribed:
            send_subscription_required(message)
            return
        
        return func(message)
    return wrapper

# Применяем проверку ко всем действиям
@bot.message_handler(func=lambda m: m.text == "💰 Заработать")
@subscription_required
def earn(msg):
    uid = msg.from_user.id
    user = get_user(uid)
    if not user:
        bot.send_message(msg.chat.id, "❌ Введите /start")
        return
    if user[18]:
        bot.send_message(msg.chat.id, "❌ Вы забанены!", reply_markup=main_kb())
        return
    
    bot.send_message(msg.chat.id, "📺 Показываем рекламу... Пожалуйста, подождите!")
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(show_advert(uid, GRAMADS_API_KEY))
        loop.close()
        if success:
            amount, err = earn_stars(uid)
            if err:
                bot.send_message(msg.chat.id, err, reply_markup=main_kb())
                return
            user = get_user(uid)
            bot.send_message(msg.chat.id,
                f"⭐ +{amount} ⭐ за просмотр рекламы!\n\n"
                f"💰 Баланс: {user[4]:.1f} ⭐\n"
                f"📈 Всего: {user[5]:.1f} ⭐\n"
                f"📊 Сегодня: {user[10]}/{DAILY_CLICK_LIMIT}",
                reply_markup=main_kb())
        else:
            bot.send_message(msg.chat.id, "❌ Не удалось показать рекламу. Попробуйте позже.", reply_markup=main_kb())
    except Exception as e:
        logging.error(f"Ошибка в earn: {e}")
        bot.send_message(msg.chat.id, "❌ Произошла ошибка. Попробуйте позже.", reply_markup=main_kb())

@bot.message_handler(func=lambda m: m.text == "👤 Профиль")
@subscription_required
def profile(msg):
    uid = msg.from_user.id
    user = get_user(uid)
    if not user:
        bot.send_message(msg.chat.id, "❌ Введите /start")
        return
    
    rank = get_user_rank(uid)
    total = get_total_users()
    bot.send_message(msg.chat.id,
        f"👤 ПРОФИЛЬ\n\n"
        f"🆔 ID: {user[1]}\n👤 Имя: {user[2]}\n📛 @{user[3] or '—'}\n\n"
        f"💰 Баланс: {user[4]:.1f} ⭐\n📈 Заработано: {user[5]:.1f} ⭐\n💸 Выведено: {user[6]:.1f} ⭐\n"
        f"🔄 Кликов: {user[7]}\n📊 Средний: {user[8]:.2f} ⭐\n"
        f"👥 Друзей: {user[15]}\n💰 С рефералов: {user[16]:.1f} ⭐\n"
        f"🏆 Место: #{rank} из {total}\n"
        f"🎯 Сегодня: {user[10]}/{DAILY_CLICK_LIMIT}",
        reply_markup=main_kb())

@bot.message_handler(func=lambda m: m.text == "👥 Друзья")
@subscription_required
def friends(msg):
    uid = msg.from_user.id
    user = get_user(uid)
    if not user:
        bot.send_message(msg.chat.id, "❌ Введите /start")
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT u.username, u.created_at FROM users u
                 JOIN referrals r ON r.referred_id = u.id
                 WHERE r.referrer_id = ? ORDER BY r.created_at DESC LIMIT 5''', (user[0],))
    refs = c.fetchall()
    conn.close()
    ref_list = "\n".join([f"{i+1}. @{r[0] or '—'} — {r[1][:10]}" for i, r in enumerate(refs)]) or "Пока никого 😢"
    bot.send_message(msg.chat.id,
        f"👥 РЕФЕРАЛКА\n\n"
        f"💰 За друга: +{REFERRAL_BONUS} ⭐\n"
        f"📊 Пассив: {REFERRAL_PERCENT}% от кликов друга\n\n"
        f"📋 Ссылка:\nhttps://t.me/{(bot.get_me()).username}?start={user[13]}\n\n"
        f"👥 Приглашено: {user[15]}\n💰 С рефералов: {user[16]:.1f} ⭐\n\n"
        f"📋 Последние:\n{ref_list}",
        reply_markup=main_kb())

@bot.message_handler(func=lambda m: m.text == "🏆 Топ")
@subscription_required
def top(msg):
    uid = msg.from_user.id
    users = get_top_users(10)
    rank = get_user_rank(uid)
    total = get_total_users()
    if not users:
        bot.send_message(msg.chat.id, "Пока нет игроков 😢", reply_markup=main_kb())
        return
    text = "🏆 ТОП-10\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, (uname, bal) in enumerate(users):
        m = medals[i] if i < 3 else f"{i+1}."
        text += f"{m} {uname} — {bal:.1f} ⭐\n"
    text += f"\n📊 Твоё место: #{rank} из {total}"
    bot.send_message(msg.chat.id, text, reply_markup=main_kb())

@bot.message_handler(func=lambda m: m.text == "🎁 Бонус")
@subscription_required
def bonus(msg):
    uid = msg.from_user.id
    amount, err = get_daily_bonus(uid)
    if err:
        bot.send_message(msg.chat.id, err, reply_markup=main_kb())
        return
    user = get_user(uid)
    bot.send_message(msg.chat.id,
        f"🎁 +{amount} ⭐\n\n💰 Баланс: {user[4]:.1f} ⭐\n\nВозвращайся завтра! 🚀",
        reply_markup=main_kb())

@bot.message_handler(func=lambda m: m.text == "💸 Вывод")
@subscription_required
def withdraw_menu(msg):
    bot.send_message(msg.chat.id,
        f"💸 ВЫВОД\n\nМинимум: {WITHDRAW_MIN} ⭐\n\nКоманда: /withdraw X\nПример: 
