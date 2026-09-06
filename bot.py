# -*- coding: utf-8 -*-
import sqlite3
import random
import datetime
import json
import logging
import os
import time
import requests
from dotenv import load_dotenv
from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = [6621617827]

# ========== WALLET PAY (@send) ==========
WALLET_TOKEN = "630423:AAuDdKYE80k9w5OqlPosVitpIyeGL8XXxg7"
WALLET_API_URL = "https://pay.wallet.tg/api"

MIN_EARN = 0.6
MAX_EARN = 1.0
DAILY_CLICK_LIMIT = 50
VIP_DAILY_CLICK_LIMIT = 50
WITHDRAW_MIN = 120
WITHDRAW_WAIT_DAYS = 7
VIP_PRICE_USDT = 1.0
REFERRAL_BONUS = 3
REFERRAL_PERCENT = 3
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

# ========== WALLET PAY API ==========
def create_wallet_invoice(amount, currency='USDT', description='VIP покупка'):
    try:
        url = f"{WALLET_API_URL}/createInvoice"
        headers = {
            'X-API-Key': WALLET_TOKEN,
            'Content-Type': 'application/json'
        }
        data = {
            'amount': amount,
            'currency': currency,
            'description': description,
            'expires_in': 3600
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        result = response.json()
        
        if result.get('ok'):
            return result['result']
        else:
            logging.error(f"Wallet Pay error: {result}")
            return None
    except Exception as e:
        logging.error(f"Error creating invoice: {e}")
        return None

def get_wallet_invoice_status(invoice_id):
    try:
        url = f"{WALLET_API_URL}/getInvoice"
        headers = {
            'X-API-Key': WALLET_TOKEN,
            'Content-Type': 'application/json'
        }
        params = {
            'invoice_id': invoice_id
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        result = response.json()
        
        if result.get('ok'):
            return result['result'].get('status')
        return None
    except Exception as e:
        logging.error(f"Error checking invoice: {e}")
        return None

# ========== ИНИЦИАЛИЗАЦИЯ ==========
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
    
    try:
        c.execute("ALTER TABLE users ADD COLUMN is_vip INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    
    try:
        c.execute("ALTER TABLE users ADD COLUMN vip_expires TEXT")
    except sqlite3.OperationalError:
        pass
    
    c.execute('''CREATE TABLE IF NOT EXISTS wallet_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        invoice_id TEXT UNIQUE,
        amount REAL,
        currency TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT,
        completed_at TEXT
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
    try:
        c.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in c.fetchall()]
        
        if 'is_vip' in columns and 'vip_expires' in columns:
            c.execute("SELECT * FROM users WHERE telegram_id = ?", (tg_id,))
        else:
            c.execute("SELECT id, telegram_id, first_name, username, balance, total_earned, total_withdrawn, clicks, avg_earning, last_click, clicks_today, last_click_date, last_visit, referral_code, referrer_id, referral_count, referral_earned, daily_bonus_date, is_banned, created_at FROM users WHERE telegram_id = ?", (tg_id,))
    except:
        c.execute("SELECT * FROM users WHERE telegram_id = ?", (tg_id,))
    
    user = c.fetchone()
    conn.close()
    return user

def update_user(tg_id, **kwargs):
    conn = get_db()
    c = conn.cursor()
    for key, val in kwargs.items():
        try:
            c.execute(f"UPDATE users SET {key} = ? WHERE telegram_id = ?", (val, tg_id))
        except sqlite3.OperationalError:
            pass
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
    
    c.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in c.fetchall()]
    
    if 'is_vip' in columns and 'vip_expires' in columns:
        c.execute('''INSERT INTO users (telegram_id, first_name, username, referral_code, referrer_id, created_at, last_visit, is_vip, vip_expires)
                     VALUES (?,?,?,?,?,?,?,0,NULL)''', (tg_id, first_name, username, code, referrer_id, now, now))
    else:
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

def is_vip_active(user):
    if not user:
        return False
    
    if len(user) < 22:
        return False
    
    if not user[20]:
        return False
    
    expires = user[21]
    if not expires:
        return False
    
    return datetime.datetime.now().isoformat() < expires

def get_vip_click_limit(user):
    return VIP_DAILY_CLICK_LIMIT if is_vip_active(user) else DAILY_CLICK_LIMIT

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
    
    if len(user) > 18 and user[18]:
        return None, "❌ Вы забанены!"
    
    click_limit = get_vip_click_limit(user)
    today = datetime.date.today().isoformat()
    
    if user[11] == today and user[10] >= click_limit:
        vip_text = " (VIP)" if is_vip_active(user) else ""
        return None, f"⚠️ Лимит {click_limit} кликов на сегодня{vip_text}!"
    
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
    if is_vip_active(user):
        amount = random.randint(10, 25)
    
    update_user(tg_id, balance=user[4]+amount, total_earned=user[5]+amount,
                daily_bonus_date=today, last_visit=datetime.datetime.now().isoformat())
    return amount, None

def buy_vip_wallet(tg_id, invoice_id):
    user = get_user(tg_id)
    if not user:
        return False, "Пользователь не найден"
    
    if is_vip_active(user):
        return False, "VIP уже активен"
    
    expires = (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat()
    update_user(tg_id, is_vip=1, vip_expires=expires)
    
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE wallet_payments SET status = 'completed', completed_at = ? WHERE invoice_id = ?",
              (datetime.datetime.now().isoformat(), invoice_id))
    conn.commit()
    conn.close()
    
    return True, "✅ VIP активирован на 30 дней!"

# ========== КЛАВИАТУРЫ ==========

def main_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("💰 Заработать", "👤 Профиль")
    kb.row("👥 Друзья", "💸 Вывод")
    kb.row("🏆 Топ", "🎁 Бонус")
    kb.row("👑 VIP")
    return kb

def admin_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📊 Статистика", "👥 Все пользователи")
    kb.row("🔝 ТОП-20", "✉️ Рассылка")
    kb.row("👑 VIP список", "💳 Платежи")
    kb.row("◀️ В главное меню")
    return kb

bot = TeleBot(TOKEN, skip_pending=True)

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

# ========== ОСНОВНЫЕ ОБРАБОТЧИКИ ==========

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
    
    vip_status = "👑 VIP" if is_vip_active(user) else "❌ Нет VIP"
    bot.send_message(msg.chat.id,
        f"⭐ Добро пожаловать, {name}!\n\n"
        f"💰 Баланс: {user[4]:.1f} ⭐\n"
        f"📈 Заработано: {user[5]:.1f} ⭐{bonus_msg}\n"
        f"👑 {vip_status}\n\n"
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
        vip_status = "👑 VIP" if is_vip_active(user) else "❌ Нет VIP"
        bot.send_message(call.message.chat.id,
            f"⭐ Добро пожаловать!\n\n💰 Баланс: {user[4]:.1f} ⭐\n👑 {vip_status}\n\nЖми «💰 Заработать»!",
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
    
    amount, err = earn_stars(uid)
    if err:
        bot.send_message(msg.chat.id, err)
        return
    user = get_user(uid)
    click_limit = get_vip_click_limit(user)
    vip_text = " (VIP)" if is_vip_active(user) else ""
    bot.send_message(msg.chat.id,
        f"⭐ +{amount} ⭐!\n💰 Баланс: {user[4]:.1f} ⭐\n📊 Сегодня: {user[10]}/{click_limit}{vip_text}",
        reply_markup=main_kb())

@bot.message_handler(func=lambda m: m.text == "👤 Профиль")
def profile(msg):
    uid = msg.from_user.id
    user = get_user(uid)
    if not user:
        bot.send_message(msg.chat.id, "Напишите /start")
        return
    
    rank = get_user_rank(uid)
    total = get_total_users()
    
    vip_status = "👑 VIP" if is_vip_active(user) else "❌ Нет VIP"
    click_limit = get_vip_click_limit(user)
    
    profile_text = (
        f"👤 ПРОФИЛЬ\n\n"
        f"💰 Баланс: {user[4]:.1f} ⭐\n"
        f"📈 Заработано: {user[5]:.1f} ⭐\n"
        f"💸 Выведено: {user[6]:.1f} ⭐\n"
        f"🔄 Кликов: {user[7]}\n"
        f"👥 Друзей: {user[15]}\n"
        f"🏆 Место: #{rank} из {total}\n"
        f"🎯 Сегодня: {user[10]}/{click_limit}\n"
        f"👑 {vip_status}"
    )
    
    if is_vip_active(user) and len(user) > 21 and user[21]:
        expires = datetime.datetime.fromisoformat(user[21])
        days_left = (expires - datetime.datetime.now()).days
        profile_text += f"\n⏳ VIP до: {expires.strftime('%d.%m.%Y')} (осталось {days_left} дн.)"
    
    bot.send_message(msg.chat.id, profile_text, reply_markup=main_kb())
    
    if not is_vip_active(user):
        bot.send_message(msg.chat.id,
            f"🌟 ХОТИТЕ БОЛЬШЕ ВОЗМОЖНОСТЕЙ?\n\n"
            f"Купите VIP всего за {VIP_PRICE_USDT} USDT через @send\n\n"
            f"✅ Моментальная выплата звезд от Fragment (вместо 3-7 дней)\n"
            f"✅ {VIP_DAILY_CLICK_LIMIT} запросов в день (вместо {DAILY_CLICK_LIMIT})\n"
            f"✅ Отдельная поддержка с быстрым ответом\n"
            f"✅ Увеличенный ежедневный бонус\n\n"
            f"👑 Нажмите кнопку «👑 VIP» для покупки!",
            reply_markup=main_kb())

@bot.message_handler(func=lambda m: m.text == "👑 VIP")
def vip_menu(msg):
    uid = msg.from_user.id
    user = get_user(uid)
    if not user:
        bot.send_message(msg.chat.id, "Напишите /start")
        return
    
    if is_vip_active(user):
        expires = datetime.datetime.fromisoformat(user[21])
        days_left = (expires - datetime.datetime.now()).days
        bot.send_message(msg.chat.id,
            f"👑 ВЫ VIP!\n\n"
            f"✅ Моментальная выплата от Fragment\n"
            f"✅ {VIP_DAILY_CLICK_LIMIT} кликов в день\n"
            f"✅ Приоритетная поддержка\n"
            f"⏳ Активен до: {expires.strftime('%d.%m.%Y')}\n"
            f"⏳ Осталось: {days_left} дней\n\n"
            f"💰 Баланс: {user[4]:.1f} ⭐",
            reply_markup=main_kb())
    else:
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton(f"💳 Купить VIP за {VIP_PRICE_USDT} USDT", callback_data="buy_vip_wallet"))
        keyboard.add(InlineKeyboardButton("❓ Что дает VIP?", callback_data="vip_info"))
        
        bot.send_message(msg.chat.id,
            f"👑 VIP СТАТУС\n\n"
            f"💰 Цена: {VIP_PRICE_USDT} USDT\n"
            f"⏳ Длительность: 30 дней\n"
            f"💳 Оплата через @send (Wallet Pay)\n\n"
            f"💰 Ваш баланс: {user[4]:.1f} ⭐\n\n"
            f"Нажмите кнопку для оплаты:",
            reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "buy_vip_wallet")
def buy_vip_wallet_callback(call):
    uid = call.from_user.id
    user = get_user(uid)
    
    if not user:
        bot.answer_callback_query(call.id, "❌ Ошибка", show_alert=True)
        return
    
    if is_vip_active(user):
        bot.answer_callback_query(call.id, "❌ VIP уже активен!", show_alert=True)
        return
    
    invoice = create_wallet_invoice(VIP_PRICE_USDT, 'USDT', f'VIP покупка для {uid}')
    
    if not invoice:
        bot.answer_callback_query(call.id, "❌ Ошибка создания платежа. Попробуйте позже.", show_alert=True)
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO wallet_payments (user_id, invoice_id, amount, currency, created_at) VALUES (?,?,?,?,?)",
              (uid, invoice['id'], VIP_PRICE_USDT, 'USDT', datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("💳 ОПЛАТИТЬ", url=invoice['pay_url']))
    keyboard.add(InlineKeyboardButton("🔄 Проверить оплату", callback_data=f"check_wallet_{invoice['id']}"))
    keyboard.add(InlineKeyboardButton("❌ Отмена", callback_data="cancel_wallet"))
    
    bot.answer_callback_query(call.id, "💳 Счет создан!", show_alert=True)
    try:
        bot.edit_message_text(
            f"💳 ОПЛАТА VIP\n\n"
            f"💰 Сумма: {VIP_PRICE_USDT} USDT\n"
            f"⏳ Длительность: 30 дней\n\n"
            f"Нажмите «ОПЛАТИТЬ»\n"
            f"После оплаты нажмите «Проверить оплату»\n\n"
            f"⏳ Счет действителен 1 час",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
    except:
        bot.send_message(call.message.chat.id,
            f"💳 ОПЛАТА VIP\n\nСумма: {VIP_PRICE_USDT} USDT\n\nНажмите кнопку для оплаты:",
            reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("check_wallet_"))
def check_wallet_payment(call):
    invoice_id = call.data.split("_")[2]
    uid = call.from_user.id
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT status FROM wallet_payments WHERE invoice_id = ? AND user_id = ?", (invoice_id, uid))
    result = c.fetchone()
    conn.close()
    
    if not result:
        bot.answer_callback_query(call.id, "❌ Платеж не найден", show_alert=True)
        return
    
    if result[0] == 'completed':
        bot.answer_callback_query(call.id, "✅ VIP уже активирован!", show_alert=True)
        return
    
    status = get_wallet_invoice_status(invoice_id)
    
    if status == 'paid' or status == 'confirmed':
        success, msg_text = buy_vip_wallet(uid, invoice_id)
        
        if success:
            bot.answer_callback_query(call.id, "✅ VIP АКТИВИРОВАН!", show_alert=True)
            user = get_user(uid)
            try:
                bot.edit_message_text(
                    f"✅ VIP АКТИВИРОВАН!\n\n"
                    f"💳 Оплачено: {VIP_PRICE_USDT} USDT\n"
                    f"👑 Действует 30 дней\n\n"
                    f"Теперь доступно:\n"
                    f"✅ Моментальные выплаты\n"
                    f"✅ {VIP_DAILY_CLICK_LIMIT} кликов в день\n"
                    f"✅ Приоритетная поддержка",
                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=main_kb()
                )
            except:
                bot.send_message(call.message.chat.id, msg_text, reply_markup=main_kb())
        else:
            bot.answer_callback_query(call.id, msg_text, show_alert=True)
    elif status == 'expired':
        bot.answer_callback_query(call.id, "❌ Счет истек", show_alert=True)
        try:
            bot.edit_message_text(
                "❌ СЧЕТ ИСТЕК\n\nПопробуйте создать новый",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=main_kb()
            )
        except:
            pass
    else:
        bot.answer_callback_query(call.id, "⏳ Ожидаем оплату...", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "cancel_wallet")
def cancel_wallet_payment(call):
    try:
        bot.edit_message_text(
            "❌ Оплата отменена",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=main_kb()
        )
    except:
        bot.send_message(call.message.chat.id, "❌ Отменено", reply_markup=main_kb())
    bot.answer_callback_query(call.id, "Отменено")

@bot.callback_query_handler(func=lambda call: call.data == "vip_info")
def vip_info_callback(call):
    vip_info_text = (
        "🌟 ПРЕИМУЩЕСТВА VIP:\n\n"
        "1️⃣ 💰 Моментальная выплата\n"
        "   Получайте звезды от Fragment сразу,\n"
        "   без ожидания 3-7 дней!\n\n"
        "2️⃣ 📊 Увеличенный лимит\n"
        f"   {VIP_DAILY_CLICK_LIMIT} запросов в день\n"
        f"   вместо {DAILY_CLICK_LIMIT}\n\n"
        "3️⃣ 🎁 Увеличенный бонус\n"
        "   Ежедневный бонус до 25⭐ (вместо 15⭐)\n\n"
        "4️⃣ 👨‍💼 Приоритетная поддержка\n"
        "   Быстрые ответы от администрации\n\n"
        "5️⃣ 🚀 Эксклюзивный доступ\n"
        "   К новым функциям первыми\n\n"
        f"💰 Цена: {VIP_PRICE_USDT} USDT на 30 дней"
    )
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, vip_info_text, reply_markup=main_kb())

@bot.message_handler(func=lambda m: m.text == "◀️ В главное меню")
def back_main(msg):
    bot.send_message(msg.chat.id, "✅ Возврат", reply_markup=main_kb())

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
    vip_text = " (VIP бонус)" if is_vip_active(user) else ""
    bot.send_message(msg.chat.id,
        f"🎁 +{amount} ⭐{vip_text}!\n💰 Баланс: {user[4]:.1f} ⭐",
        reply_markup=main_kb())

@bot.message_handler(func=lambda m: m.text == "💸 Вывод")
def withdraw_menu(msg):
    uid = msg.from_user.id
    user = get_user(uid)
    if not user:
        bot.send_message(msg.chat.id, "Напишите /start")
        return
    
    vip_status = is_vip_active(user)
    wait_time = "МОМЕНТАЛЬНО ⚡" if vip_status else f"{WITHDRAW_WAIT_DAYS} дней"
    
    text = (
        f"💸 ВЫВОД\n\n"
        f"Минимум: {WITHDRAW_MIN} ⭐\n"
        f"⏳ Время ожидания: {wait_time}\n"
        f"👑 Ваш статус: {'VIP' if vip_status else 'Обычный'}\n\n"
        f"/withdraw СУММА"
    )
    
    if not vip_status:
        text += f"\n\n💡 Купите VIP за {VIP_PRICE_USDT} USDT и получайте выплаты моментально!"
    
    bot.send_message(msg.chat.id, text, reply_markup=main_kb())

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
    
    vip_status = is_vip_active(user)
    wait_text = "⚡ МОМЕНТАЛЬНО!" if vip_status else f"⏳ Ожидание {WITHDRAW_WAIT_DAYS} дней"
    
    response = f"✅ Заявка на {amount} ⭐ отправлена!\n📅 {wait_text}"
    
    if not vip_status:
        response += f"\n\n💡 С VIP вы бы получили выплату моментально вместо {WITHDRAW_WAIT_DAYS} дней ожидания!\nКупите VIP за {VIP_PRICE_USDT} USDT через @send"
    
    bot.send_message(msg.chat.id, response, reply_markup=main_kb())

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
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT SUM(total_earned) FROM users WHERE is_banned=0")
    earned = c.fetchone()[0] or 0
    
    try:
        c.execute("SELECT COUNT(*) FROM users WHERE is_vip=1 AND vip_expires > datetime('now')")
        vip_count = c.fetchone()[0] or 0
    except:
        vip_count = 0
    
    c.execute("SELECT COUNT(*) FROM wallet_payments WHERE status = 'completed'")
    wallet_payments = c.fetchone()[0] or 0
    
    conn.close()
    
    bot.send_message(msg.chat.id,
        f"📊 СТАТИСТИКА\n\n"
        f"👥 Всего: {total}\n"
        f"🟢 Активных: {active}\n"
        f"👑 VIP: {vip_count}\n"
        f"🔄 Кликов: {clicks}\n"
        f"⭐ Заработано: {earned:.1f}\n"
        f"💳 Оплат через @send: {wallet_payments}",
        reply_markup=admin_kb())

@bot.message_handler(func=lambda m: m.text == "👥 Все пользователи")
def all_users(msg):
    if msg.from_user.id not in ADMIN_IDS:
        return
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        c.execute("SELECT telegram_id, first_name, username, balance, is_vip FROM users WHERE is_banned=0 ORDER BY balance DESC LIMIT 30")
        users = c.fetchall()
    except:
        c.execute("SELECT telegram_id, first_name, username, balance FROM users WHERE is_banned=0 ORDER BY balance DESC LIMIT 30")
        users = [(u[0], u[1], u[2], u[3], 0) for u in c.fetchall()]
    
    conn.close()
    
    if not users:
        bot.send_message(msg.chat.id, "Нет пользователей", reply_markup=admin_kb())
        return
    
    text = "👥 ПОЛЬЗОВАТЕЛИ\n\n"
    for i, u in enumerate(users):
        vip_icon = "👑 " if len(u) > 4 and u[4] else ""
        text += f"{i+1}. {vip_icon}{u[1]} (@{u[2] or '—'}) — {u[3]:.1f} ⭐\n"
    
    bot.send_message(msg.chat.id, text, reply_markup=admin_kb())

@bot.message_handler(func=lambda m: m.text == "🔝 ТОП-20")
def top20(msg):
    if msg.from_user.id not in ADMIN_IDS:
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT username, balance FROM users WHERE is_banned=0 ORDER BY balance DESC LIMIT 20")
    users = c.fetchall()
    conn.close()
    
    text = "🔝 ТОП-20\n\n"
    for i, u in enumerate(users):
        text += f"{i+1}. @{u[0] or '—'} — {u[1]:.1f} ⭐\n"
    
    bot.send_message(msg.chat.id, text, reply_markup=admin_kb())

@bot.message_handler(func=lambda m: m.text == "👑 VIP список")
def vip_list(msg):
    if msg.from_user.id not in ADMIN_IDS:
        return
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        c.execute("SELECT telegram_id, first_name, username, balance, vip_expires FROM users WHERE is_vip=1 AND vip_expires > datetime('now') ORDER BY vip_expires")
        vips = c.fetchall()
    except:
        vips = []
    
    conn.close()
    
    if not vips:
        bot.send_message(msg.chat.id, "Нет активных VIP", reply_markup=admin_kb())
        return
    
    text = "👑 АКТИВНЫЕ VIP\n\n"
    for v in vips:
        try:
            expires = datetime.datetime.fromisoformat(v[4])
            days_left = (expires - datetime.datetime.now()).days
            text += f"• {v[1]} (@{v[2] or '—'}) — {v[3]:.1f}⭐, осталось {days_left} дн.\n"
        except:
            text += f"• {v[1]} (@{v[2] or '—'}) — {v[3]:.1f}⭐\n"
    
    bot.send_message(msg.chat.id, text, reply_markup=admin_kb())

@bot.message_handler(func=lambda m: m.text == "💳 Платежи")
def wallet_payments_list(msg):
    if msg.from_user.id not in ADMIN_IDS:
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, user_id, amount, currency, status, created_at FROM wallet_payments ORDER BY id DESC LIMIT 20")
    payments = c.fetchall()
    conn.close()
    
    if not payments:
        bot.send_message(msg.chat.id, "Нет платежей через @send", reply_markup=admin_kb())
        return
    
    text = "💳 ПЛАТЕЖИ ЧЕРЕЗ @send\n\n"
    for p in payments:
        status_icon = "✅" if p[4] == 'completed' else "⏳" if p[4] == 'pending' else "❌"
        text += f"#{p[0]} | {p[2]} {p[3]} | {status_icon} {p[4]} | {p[1]}\n"
    
    bot.send_message(msg.chat.id, text, reply_markup=admin_kb())

@bot.message_handler(commands=['broadcast'])
def broadcast(msg):
    if msg.from_user.id not in ADMIN_IDS:
        return
    
    text = msg.text.replace('/broadcast', '').strip()
    if not text:
        bot.send_message(msg.chat.id, "/broadcast ТЕКСТ")
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT telegram_id FROM users WHERE is_banned=0")
    users = c.fetchall()
    conn.close()
    
    sent = 0
    for u in users:
        try:
            bot.send_message(u[0], text)
            sent += 1
        except:
            pass
    
    bot.send_message(msg.chat.id, f"✅ Отправлено {sent} пользователям", reply_markup=admin_kb())

@bot.message_handler(func=lambda m: m.text == "✉️ Рассылка")
def broadcast_prompt(msg):
    if msg.from_user.id not in ADMIN_IDS:
        return
    bot.send_message(msg.chat.id, "✉️ РАССЫЛКА\n\n/broadcast ТЕКСТ", reply_markup=admin_kb())

@bot.message_handler(commands=['addfake'])
def add_fake(msg):
    if msg.from_user.id not in ADMIN_IDS:
        return
    
    args = msg.text.split()
    if len(args) < 3:
        bot.send_message(msg.chat.id, "/addfake @username 1000")
        return
    
    username = args[1]
    try:
        balance = float(args[2])
    except:
        bot.send_message(msg.chat.id, "Баланс - число")
        return
    
    fake_users = init_fake_top()
    fake_users.append({"username": username, "balance": balance})
    fake_users.sort(key=lambda x: x['balance'], reverse=True)
    
    with open(FAKE_TOP_FILE, 'w', encoding='utf-8') as f:
        json.dump(fake_users, f, ensure_ascii=False, indent=2)
    
    bot.send_message(msg.chat.id, f"✅ Добавлен {username}")

@bot.message_handler(commands=['fake_list'])
def fake_list(msg):
    if msg.from_user.id not in ADMIN_IDS:
        return
    
    fake_users = init_fake_top()
    text = "📋 ФЕЙК-ТОП\n\n"
    for i, u in enumerate(fake_users[:20]):
        text += f"{i+1}. {u['username']} — {u['balance']} ⭐\n"
    
    bot.send_message(msg.chat.id, text)

@bot.message_handler(commands=['removefake'])
def remove_fake(msg):
    if msg.from_user.id not in ADMIN_IDS:
        return
    
    args = msg.text.split()
    if len(args) < 2:
        bot.send_message(msg.chat.id, "/removefake @username")
        return
    
    username = args[1]
    fake_users = init_fake_top()
    new_list = [u for u in fake_users if u['username'] != username]
    
    with open(FAKE_TOP_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_list, f, ensure_ascii=False, indent=2)
    
    bot.send_message(msg.chat.id, f"✅ Удалён {username}")

@bot.message_handler(commands=['givevip'])
def give_vip(msg):
    if msg.from_user.id not in ADMIN_IDS:
        return
    
    args = msg.text.split()
    if len(args) < 2:
        bot.send_message(msg.chat.id, "/givevip @username")
        return
    
    username = args[1]
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT telegram_id, first_name, is_vip FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    
    if not user:
        bot.send_message(msg.chat.id, "Пользователь не найден")
        return
    
    if user[2]:
        bot.send_message(msg.chat.id, f"У {user[1]} уже есть VIP")
        return
    
    expires = (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat()
    update_user(user[0], is_vip=1, vip_expires=expires)
    bot.send_message(msg.chat.id, f"✅ VIP выдан {user[1]} на 30 дней")

@bot.message_handler(commands=['removevip'])
def remove_vip(msg):
    if msg.from_user.id not in ADMIN_IDS:
        return
    
    args = msg.text.split()
    if len(args) < 2:
        bot.send_message(msg.chat.id, "/removevip @username")
        return
    
    username = args[1]
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT telegram_id, first_name FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    
    if not user:
        bot.send_message(msg.chat.id, "Пользователь не найден")
        return
    
    update_user(user[0], is_vip=0, vip_expires=None)
    bot.send_message(msg.chat.id, f"✅ VIP удален у {user[1]}")

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    init_db()
    init_fake_top()
    
    print("🤖 Бот запущен!")
    print(f"👑 VIP цена: {VIP_PRICE_USDT} USDT")
    print(f"📊 Обычный лимит: {DAILY_CLICK_LIMIT}")
    print(f"📊 VIP лимит: {VIP_DAILY_CLICK_LIMIT}")
    print("💳 Оплата: через @send (Wallet Pay)")
    print("📢 Реклама: ❌ ОТКЛЮЧЕНА")
    print("✅ Бот готов к работе!")
    
    bot.remove_webhook()
    time.sleep(1)
    bot.polling(none_stop=True, skip_pending=True, interval=0)
