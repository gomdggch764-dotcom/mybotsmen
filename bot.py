import sqlite3
import random
import datetime
import json
import asyncio
import logging
from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup
from ads import show_advert

# ========== ÐÐÐ¡Ð¢Ð ÐžÐ™ÐšÐ Ð›ÐžÐ“Ð“Ð˜Ð ÐžÐ’ÐÐÐ˜Ð¯ ==========
logging.basicConfig(level=logging.INFO)

# ========== ÐšÐžÐÐ¤Ð˜Ð“Ð£Ð ÐÐ¦Ð˜Ð¯ ==========
from dotenv import load_dotenv
import os
load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = [6621617827]  # Ð¢Ð’ÐžÐ™ TELEGRAM ID

# ========== ÐÐÐ¡Ð¢Ð ÐžÐ™ÐšÐ˜ GRAMADS ==========
# ÐŸÐ¾Ð»ÑƒÑ‡Ð¸ ÐºÐ»ÑŽÑ‡ Ð·Ð´ÐµÑÑŒ: https://gramads.net (Ð² Ð»Ð¸Ñ‡Ð½Ð¾Ð¼ ÐºÐ°Ð±Ð¸Ð½ÐµÑ‚Ðµ â†’ Ð¸ÐºÐ¾Ð½ÐºÐ° ÑˆÐµÑÑ‚ÐµÑ€Ð½Ð¸ â†’ ÑÐºÐ¾Ð¿Ð¸Ñ€Ð¾Ð²Ð°Ñ‚ÑŒ ÐºÐ»ÑŽÑ‡)
GRAMADS_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1ODM2MyIsImp0aSI6IjM4MWIyY2RmLThkNzYtNDkzMC1hNGZiLWYwOTAwZDdiYjlhYSIsIm5hbWUiOiJFYXJuU2F2ZWxpeSIsImJvdGlkIjoiMjI3NzEiLCJodHRwOi8vc2NoZW1hcy54bWxzb2FwLm9yZy93cy8yMDA1LzA1L2lkZW50aXR5L2NsYWltcy9uYW1laWRlbnRpZmllciI6IjU4MzYzIiwibmJmIjoxNzg4Mjg3MjQ3LCJleHAiOjE3ODg0OTYwNDcsImlzcyI6IlN0dWdub3YiLCJhdWQiOiJVc2VycyJ9.p_85j4_PQfJ6oO_eiJqkPHB6KQFxCfr4zm2yj9Gjbpk"  # Ð—ÐÐœÐ•ÐÐ˜ ÐÐ Ð¡Ð’ÐžÐ™ ÐšÐ›Ð®Ð§!

# ========== ÐÐÐ¡Ð¢Ð ÐžÐ™ÐšÐ˜ Ð‘ÐžÐ¢Ð ==========
MIN_EARN = 2.3
MAX_EARN = 6.2
DAILY_CLICK_LIMIT = 50
WITHDRAW_MIN = 10
REFERRAL_BONUS = 5
REFERRAL_PERCENT = 10
DB_NAME = "earn_bot.db"
FAKE_TOP_FILE = "fake_top.json"

# ========== Ð˜ÐÐ˜Ð¦Ð˜ÐÐ›Ð˜Ð—ÐÐ¦Ð˜Ð¯ Ð¤Ð•Ð™Ðš-Ð¢ÐžÐŸÐ ==========
def init_fake_top():
    default_fake = [
        {"username": "@kotnavoine", "balance": 2610},
        {"username": "@mittsf2", "balance": 1704},
        {"username": "@demon666_597", "balance": 680},
        {"username": "@FGPIDORS", "balance": 676},
        {"username": "@thisgoodworld", "balance": 312},
        {"username": "â­ Ð¡Ð¢ÐÐ›Ð¬ÐÐžÐ™ Ð’ÐžÐ˜Ð", "balance": 287.5},
        {"username": "ðŸ”¥ ÐžÐ“ÐÐ•ÐÐÐ«Ð™ Ð›Ð˜Ð¡", "balance": 254.3},
        {"username": "ðŸ’Ž ÐÐ›ÐœÐÐ—ÐÐ«Ð™ Ð‘ÐÐ ÐžÐ", "balance": 221.8},
        {"username": "ðŸ‘‘ Ð¢ÐÐœÐÐ«Ð™ Ð’Ð›ÐÐ¡Ð¢Ð•Ð›Ð˜Ð", "balance": 198.2},
        {"username": "ðŸŒ™ Ð›Ð£ÐÐÐ«Ð™ Ð¡Ð¢Ð ÐÐ–", "balance": 167.9}
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

# ========== Ð‘ÐÐ—Ð Ð”ÐÐÐÐ«Ð¥ ==========
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
        all_users.append({
            'username': u['username'],
            'balance': u['balance'],
            'is_fake': True
        })
    
    for u in real_users:
        all_users.append({
            'username': u[0] or 'Ð‘ÐµÐ· Ð¸Ð¼ÐµÐ½Ð¸',
            'balance': u[1],
            'is_fake': False
        })
    
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
        return None, "ÐŸÐ¾Ð»ÑŒÐ·Ð¾Ð²Ð°Ñ‚ÐµÐ»ÑŒ Ð½Ðµ Ð½Ð°Ð¹Ð´ÐµÐ½"
    if user[18]:
        return None, "âŒ Ð’Ñ‹ Ð·Ð°Ð±Ð°Ð½ÐµÐ½Ñ‹!"
    today = datetime.date.today().isoformat()
    if user[11] == today and user[10] >= DAILY_CLICK_LIMIT:
        return None, f"âš ï¸ Ð›Ð¸Ð¼Ð¸Ñ‚ {DAILY_CLICK_LIMIT} ÐºÐ»Ð¸ÐºÐ¾Ð² Ð½Ð° ÑÐµÐ³Ð¾Ð´Ð½Ñ!"
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
        return None, "ÐŸÐ¾Ð»ÑŒÐ·Ð¾Ð²Ð°Ñ‚ÐµÐ»ÑŒ Ð½Ðµ Ð½Ð°Ð¹Ð´ÐµÐ½"
    today = datetime.date.today().isoformat()
    if user[17] == today:
        return None, "âš ï¸ Ð‘Ð¾Ð½ÑƒÑ ÑƒÐ¶Ðµ Ð¿Ð¾Ð»ÑƒÑ‡ÐµÐ½ ÑÐµÐ³Ð¾Ð´Ð½Ñ!"
    amount = random.randint(5, 15)
    update_user(tg_id, balance=user[4]+amount, total_earned=user[5]+amount,
                daily_bonus_date=today, last_visit=datetime.datetime.now().isoformat())
    return amount, None

# ========== ÐšÐ›ÐÐ’Ð˜ÐÐ¢Ð£Ð Ð« ==========
def main_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("ðŸ’° Ð—Ð°Ñ€Ð°Ð±Ð¾Ñ‚Ð°Ñ‚ÑŒ", "ðŸ‘¤ ÐŸÑ€Ð¾Ñ„Ð¸Ð»ÑŒ")
    kb.row("ðŸ‘¥ Ð”Ñ€ÑƒÐ·ÑŒÑ", "ðŸ’¸ Ð’Ñ‹Ð²Ð¾Ð´")
    kb.row("ðŸ† Ð¢Ð¾Ð¿", "ðŸŽ Ð‘Ð¾Ð½ÑƒÑ")
    return kb

def admin_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("ðŸ“Š Ð¡Ñ‚Ð°Ñ‚Ð¸ÑÑ‚Ð¸ÐºÐ°", "ðŸ‘¥ Ð’ÑÐµ Ð¿Ð¾Ð»ÑŒÐ·Ð¾Ð²Ð°Ñ‚ÐµÐ»Ð¸")
    kb.row("ðŸ” Ð¢ÐžÐŸ-20", "âœ‰ï¸ Ð Ð°ÑÑÑ‹Ð»ÐºÐ°")
    kb.row("â—€ï¸ Ð’ Ð³Ð»Ð°Ð²Ð½Ð¾Ðµ Ð¼ÐµÐ½ÑŽ")
    return kb

# ========== Ð‘ÐžÐ¢ ==========
bot = TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(msg):
    uid = msg.from_user.id
    name = msg.from_user.first_name
    uname = msg.from_user.username or "Ð±ÐµÐ· username"
    ref = msg.text.split()[1] if len(msg.text.split()) > 1 else None
    user = register_user(uid, name, uname, ref)
    bonus_msg = ""
    today = datetime.date.today().isoformat()
    if user[17] != today:
        ba = random.randint(5, 15)
        update_user(uid, balance=user[4]+ba, total_earned=user[5]+ba, daily_bonus_date=today)
        bonus_msg = f"\n\nðŸŽ Ð•Ð¶ÐµÐ´Ð½ÐµÐ²Ð½Ñ‹Ð¹ Ð±Ð¾Ð½ÑƒÑ: +{ba} â­!"
    ref_msg = "\n\nðŸ‘¥ Ð’Ñ‹ Ð¿Ñ€Ð¸ÑˆÐ»Ð¸ Ð¿Ð¾ Ñ€ÐµÑ„ÐµÑ€Ð°Ð»ÑŒÐ½Ð¾Ð¹ ÑÑÑ‹Ð»ÐºÐµ!" if user[14] else ""
    bot.send_message(msg.chat.id,
        f"â­ Ð”Ð¾Ð±Ñ€Ð¾ Ð¿Ð¾Ð¶Ð°Ð»Ð¾Ð²Ð°Ñ‚ÑŒ Ð² EarnSaveliyBot, {name}!\n\n"
        f"ðŸ’° Ð‘Ð°Ð»Ð°Ð½Ñ: {user[4]:.1f} â­\n"
        f"ðŸ“ˆ Ð—Ð°Ñ€Ð°Ð±Ð¾Ñ‚Ð°Ð½Ð¾: {user[5]:.1f} â­{bonus_msg}{ref_msg}\n\n"
        f"ÐÐ°Ð¶Ð¸Ð¼Ð°Ð¹ Â«ðŸ’° Ð—Ð°Ñ€Ð°Ð±Ð¾Ñ‚Ð°Ñ‚ÑŒÂ» Ð¸ ÑÐ¼Ð¾Ñ‚Ñ€Ð¸ Ñ€ÐµÐºÐ»Ð°Ð¼Ñƒ, Ñ‡Ñ‚Ð¾Ð±Ñ‹ Ð¿Ð¾Ð»ÑƒÑ‡Ð¸Ñ‚ÑŒ Ð¾Ñ‚ {MIN_EARN} Ð´Ð¾ {MAX_EARN} â­!\n"
        f"Ð—Ð¾Ð²Ð¸ Ð´Ñ€ÑƒÐ·ÐµÐ¹ Ð¸ Ð¿Ð¾Ð»ÑƒÑ‡Ð°Ð¹ {REFERRAL_PERCENT}% Ð¾Ñ‚ Ð¸Ñ… Ð´Ð¾Ñ…Ð¾Ð´Ð°! ðŸš€",
        reply_markup=main_kb(), parse_mode=None)

@bot.message_handler(func=lambda m: m.text == "ðŸ’° Ð—Ð°Ñ€Ð°Ð±Ð¾Ñ‚Ð°Ñ‚ÑŒ")
def earn(msg):
    uid = msg.from_user.id
    user = get_user(uid)
    if not user:
        bot.send_message(msg.chat.id, "âŒ Ð’Ð²ÐµÐ´Ð¸Ñ‚Ðµ /start")
        return
    if user[18]:
        bot.send_message(msg.chat.id, "âŒ Ð’Ñ‹ Ð·Ð°Ð±Ð°Ð½ÐµÐ½Ñ‹!", reply_markup=main_kb())
        return
    
    # ÐžÑ‚Ð¿Ñ€Ð°Ð²Ð»ÑÐµÐ¼ ÑƒÐ²ÐµÐ´Ð¾Ð¼Ð»ÐµÐ½Ð¸Ðµ Ð¾ Ð½Ð°Ñ‡Ð°Ð»Ðµ Ð¿Ð¾ÐºÐ°Ð·Ð° Ñ€ÐµÐºÐ»Ð°Ð¼Ñ‹
    bot.send_message(msg.chat.id, "ðŸ“º ÐŸÐ¾ÐºÐ°Ð·Ñ‹Ð²Ð°ÐµÐ¼ Ñ€ÐµÐºÐ»Ð°Ð¼Ñƒ... ÐŸÐ¾Ð¶Ð°Ð»ÑƒÐ¹ÑÑ‚Ð°, Ð¿Ð¾Ð´Ð¾Ð¶Ð´Ð¸Ñ‚Ðµ!")
    
    try:
        # Ð¡Ð¾Ð·Ð´Ð°Ñ‘Ð¼ ÑÐ¾Ð±Ñ‹Ñ‚Ð¸Ð¹Ð½Ñ‹Ð¹ Ñ†Ð¸ÐºÐ» Ð´Ð»Ñ Ð°ÑÐ¸Ð½Ñ…Ñ€Ð¾Ð½Ð½Ð¾Ð³Ð¾ Ð·Ð°Ð¿Ñ€Ð¾ÑÐ°
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # ÐŸÐ¾ÐºÐ°Ð·Ñ‹Ð²Ð°ÐµÐ¼ Ñ€ÐµÐºÐ»Ð°Ð¼Ñƒ Ñ‡ÐµÑ€ÐµÐ· GramAds
        success = loop.run_until_complete(show_advert(uid, GRAMADS_API_KEY))
        loop.close()
        
        if success:
            # Ð•ÑÐ»Ð¸ Ñ€ÐµÐºÐ»Ð°Ð¼Ð° Ð¿Ð¾ÐºÐ°Ð·Ð°Ð½Ð° â€” Ð½Ð°Ñ‡Ð¸ÑÐ»ÑÐµÐ¼ Ð·Ð²Ñ‘Ð·Ð´Ñ‹
            amount, err = earn_stars(uid)
            if err:
                bot.send_message(msg.chat.id, err, reply_markup=main_kb())
                return
            user = get_user(uid)
            bot.send_message(msg.chat.id,
                f"â­ +{amount} â­ Ð·Ð° Ð¿Ñ€Ð¾ÑÐ¼Ð¾Ñ‚Ñ€ Ñ€ÐµÐºÐ»Ð°Ð¼Ñ‹!\n\n"
                f"ðŸ’° Ð‘Ð°Ð»Ð°Ð½Ñ: {user[4]:.1f} â­\n"
                f"ðŸ“ˆ Ð’ÑÐµÐ³Ð¾: {user[5]:.1f} â­\n"
                f"ðŸ“Š Ð¡ÐµÐ³Ð¾Ð´Ð½Ñ: {user[10]}/{DAILY_CLICK_LIMIT}",
                reply_markup=main_kb())
        else:
            bot.send_message(msg.chat.id, 
                "âŒ ÐÐµ ÑƒÐ´Ð°Ð»Ð¾ÑÑŒ Ð¿Ð¾ÐºÐ°Ð·Ð°Ñ‚ÑŒ Ñ€ÐµÐºÐ»Ð°Ð¼Ñƒ. ÐŸÐ¾Ð¿Ñ€Ð¾Ð±ÑƒÐ¹Ñ‚Ðµ Ð¿Ð¾Ð·Ð¶Ðµ.",
                reply_markup=main_kb())
    except Exception as e:
        logging.error(f"ÐžÑˆÐ¸Ð±ÐºÐ° Ð² earn: {e}")
        bot.send_message(msg.chat.id, 
            f"âŒ ÐŸÑ€Ð¾Ð¸Ð·Ð¾ÑˆÐ»Ð° Ð¾ÑˆÐ¸Ð±ÐºÐ°. ÐŸÐ¾Ð¿Ñ€Ð¾Ð±ÑƒÐ¹Ñ‚Ðµ Ð¿Ð¾Ð·Ð¶Ðµ.",
            reply_markup=main_kb())

@bot.message_handler(func=lambda m: m.text == "ðŸ‘¤ ÐŸÑ€Ð¾Ñ„Ð¸Ð»ÑŒ")
def profile(msg):
    uid = msg.from_user.id
    user = get_user(uid)
    if not user:
        bot.send_message(msg.chat.id, "âŒ Ð’Ð²ÐµÐ´Ð¸Ñ‚Ðµ /start")
        return
    rank = get_user_rank(uid)
    total = get_total_users()
    bot.send_message(msg.chat.id,
        f"ðŸ‘¤ ÐŸÐ ÐžÐ¤Ð˜Ð›Ð¬\n\n"
        f"ðŸ†” ID: {user[1]}\nðŸ‘¤ Ð˜Ð¼Ñ: {user[2]}\nðŸ“› @{user[3] or 'â€”'}\n\n"
        f"ðŸ’° Ð‘Ð°Ð»Ð°Ð½Ñ: {user[4]:.1f} â­\nðŸ“ˆ Ð—Ð°Ñ€Ð°Ð±Ð¾Ñ‚Ð°Ð½Ð¾: {user[5]:.1f} â­\nðŸ’¸ Ð’Ñ‹Ð²ÐµÐ´ÐµÐ½Ð¾: {user[6]:.1f} â­\n"
        f"ðŸ”„ ÐšÐ»Ð¸ÐºÐ¾Ð²: {user[7]}\nðŸ“Š Ð¡Ñ€ÐµÐ´Ð½Ð¸Ð¹: {user[8]:.2f} â­\n"
        f"ðŸ‘¥ Ð”Ñ€ÑƒÐ·ÐµÐ¹: {user[15]}\nðŸ’° Ð¡ Ñ€ÐµÑ„ÐµÑ€Ð°Ð»Ð¾Ð²: {user[16]:.1f} â­\n"
        f"ðŸ† ÐœÐµÑÑ‚Ð¾: #{rank} Ð¸Ð· {total}\n"
        f"ðŸŽ¯ Ð¡ÐµÐ³Ð¾Ð´Ð½Ñ: {user[10]}/{DAILY_CLICK_LIMIT}",
        reply_markup=main_kb(), parse_mode=None)

@bot.message_handler(func=lambda m: m.text == "ðŸ‘¥ Ð”Ñ€ÑƒÐ·ÑŒÑ")
def friends(msg):
    uid = msg.from_user.id
    user = get_user(uid)
    if not user:
        bot.send_message(msg.chat.id, "âŒ Ð’Ð²ÐµÐ´Ð¸Ñ‚Ðµ /start")
        return
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT u.username, u.created_at FROM users u
                 JOIN referrals r ON r.referred_id = u.id
                 WHERE r.referrer_id = ? ORDER BY r.created_at DESC LIMIT 5''', (user[0],))
    refs = c.fetchall()
    conn.close()
    ref_list = "\n".join([f"{i+1}. @{r[0] or 'â€”'} â€” {r[1][:10]}" for i, r in enumerate(refs)]) or "ÐŸÐ¾ÐºÐ° Ð½Ð¸ÐºÐ¾Ð³Ð¾ ðŸ˜¢"
    bot.send_message(msg.chat.id,
        f"ðŸ‘¥ Ð Ð•Ð¤Ð•Ð ÐÐ›ÐšÐ\n\n"
        f"ðŸ’° Ð—Ð° Ð´Ñ€ÑƒÐ³Ð°: +{REFERRAL_BONUS} â­\n"
        f"ðŸ“Š ÐŸÐ°ÑÑÐ¸Ð²: {REFERRAL_PERCENT}% Ð¾Ñ‚ ÐºÐ»Ð¸ÐºÐ¾Ð² Ð´Ñ€ÑƒÐ³Ð°\n\n"
        f"ðŸ“‹ Ð¡ÑÑ‹Ð»ÐºÐ°:\nhttps://t.me/{(bot.get_me()).username}?start={user[13]}\n\n"
        f"ðŸ‘¥ ÐŸÑ€Ð¸Ð³Ð»Ð°ÑˆÐµÐ½Ð¾: {user[15]}\nðŸ’° Ð¡ Ñ€ÐµÑ„ÐµÑ€Ð°Ð»Ð¾Ð²: {user[16]:.1f} â­\n\n"
        f"ðŸ“‹ ÐŸÐ¾ÑÐ»ÐµÐ´Ð½Ð¸Ðµ:\n{ref_list}",
        reply_markup=main_kb(), parse_mode=None)

@bot.message_handler(func=lambda m: m.text == "ðŸ† Ð¢Ð¾Ð¿")
def top(msg):
    users = get_top_users(10)
    uid = msg.from_user.id
    rank = get_user_rank(uid)
    total = get_total_users()
    if not users:
        bot.send_message(msg.chat.id, "ÐŸÐ¾ÐºÐ° Ð½ÐµÑ‚ Ð¸Ð³Ñ€Ð¾ÐºÐ¾Ð² ðŸ˜¢", reply_markup=main_kb())
        return
    text = "ðŸ† Ð¢ÐžÐŸ-10\n\n"
    medals = ["ðŸ¥‡", "ðŸ¥ˆ", "ðŸ¥‰"]
    for i, (uname, bal) in enumerate(users):
        m = medals[i] if i < 3 else f"{i+1}."
        text += f"{m} {uname} â€” {bal:.1f} â­\n"
    text += f"\nðŸ“Š Ð¢Ð²Ð¾Ñ‘ Ð¼ÐµÑÑ‚Ð¾: #{rank} Ð¸Ð· {total}"
    bot.send_message(msg.chat.id, text, reply_markup=main_kb(), parse_mode=None)

@bot.message_handler(func=lambda m: m.text == "ðŸŽ Ð‘Ð¾Ð½ÑƒÑ")
def bonus(msg):
    uid = msg.from_user.id
    amount, err = get_daily_bonus(uid)
    if err:
        bot.send_message(msg.chat.id, err, reply_markup=main_kb())
        return
    user = get_user(uid)
    bot.send_message(msg.chat.id,
        f"ðŸŽ +{amount} â­\n\nðŸ’° Ð‘Ð°Ð»Ð°Ð½Ñ: {user[4]:.1f} â­\n\nÐ’Ð¾Ð·Ð²Ñ€Ð°Ñ‰Ð°Ð¹ÑÑ Ð·Ð°Ð²Ñ‚Ñ€Ð°! ðŸš€",
        reply_markup=main_kb(), parse_mode=None)

@bot.message_handler(func=lambda m: m.text == "ðŸ’¸ Ð’Ñ‹Ð²Ð¾Ð´")
def withdraw_menu(msg):
    bot.send_message(msg.chat.id,
        f"ðŸ’¸ Ð’Ð«Ð’ÐžÐ”\n\nÐœÐ¸Ð½Ð¸Ð¼ÑƒÐ¼: {WITHDRAW_MIN} â­\n\nÐšÐ¾Ð¼Ð°Ð½Ð´Ð°: /withdraw X\nÐŸÑ€Ð¸Ð¼ÐµÑ€: /withdraw 10",
        reply_markup=main_kb(), parse_mode=None)

@bot.message_handler(commands=['withdraw'])
def withdraw(msg):
    uid = msg.from_user.id
    user = get_user(uid)
    if not user:
        bot.send_message(msg.chat.id, "âŒ Ð’Ð²ÐµÐ´Ð¸Ñ‚Ðµ /start")
        return
    if user[18]:
        bot.send_message(msg.chat.id, "âŒ Ð’Ñ‹ Ð·Ð°Ð±Ð°Ð½ÐµÐ½Ñ‹!")
        return
    args = msg.text.split()
    if len(args) < 2:
        bot.send_message(msg.chat.id, "âŒ Ð£ÐºÐ°Ð¶Ð¸Ñ‚Ðµ ÑÑƒÐ¼Ð¼Ñƒ: /withdraw 10")
        return
    try:
        amount = float(args[1])
    except:
        bot.send_message(msg.chat.id, "âŒ Ð’Ð²ÐµÐ´Ð¸Ñ‚Ðµ Ñ‡Ð¸ÑÐ»Ð¾")
        return
    if amount < WITHDRAW_MIN:
        bot.send_message(msg.chat.id, f"âŒ ÐœÐ¸Ð½Ð¸Ð¼ÑƒÐ¼: {WITHDRAW_MIN} â­")
        return
    if amount > user[4]:
        bot.send_message(msg.chat.id, f"âŒ ÐÐµÐ´Ð¾ÑÑ‚Ð°Ñ‚Ð¾Ñ‡Ð½Ð¾! Ð£ Ð²Ð°Ñ: {user[4]:.1f} â­")
        return
    new_balance = user[4] - amount
    new_withdrawn = user[6] + amount
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET balance = ?, total_withdrawn = ? WHERE telegram_id = ?",
              (new_balance, new_withdrawn, uid))
    now = datetime.datetime.now().isoformat()
    c.execute("INSERT INTO withdrawals (user_id, amount, requested_at) VALUES (?,?,?)",
              (user[0], amount, now))
    conn.commit()
    conn.close()
    bot.send_message(msg.chat.id,
        f"âœ… Ð—Ð°ÑÐ²ÐºÐ° Ð½Ð° {amount} â­ Ð¾Ñ‚Ð¿Ñ€Ð°Ð²Ð»ÐµÐ½Ð°!\nðŸ’° ÐžÑÑ‚Ð°Ñ‚Ð¾Ðº: {new_balance:.1f} â­",
        reply_markup=main_kb(), parse_mode=None)

# ========== ÐÐ”ÐœÐ˜Ð ==========
@bot.message_handler(commands=['admin'])
def admin(msg):
    if msg.from_user.id not in ADMIN_IDS:
        bot.send_message(msg.chat.id, "âŒ ÐÐµÑ‚ Ð´Ð¾ÑÑ‚ÑƒÐ¿Ð°")
        return
    bot.send_message(msg.chat.id, "ðŸ›¡ï¸ ÐÐ”ÐœÐ˜Ð-ÐŸÐÐÐ•Ð›Ð¬", reply_markup=admin_kb(), parse_mode=None)

@bot.message_handler(commands=['addfake'])
def add_fake(msg):
    if msg.from_user.id not in ADMIN_IDS:
        bot.send_message(msg.chat.id, "âŒ ÐÐµÑ‚ Ð´Ð¾ÑÑ‚ÑƒÐ¿Ð°")
        return
    
    args = msg.text.split()
    if len(args) < 3:
        bot.send_message(msg.chat.id, "âŒ Ð˜ÑÐ¿Ð¾Ð»ÑŒÐ·ÑƒÐ¹: /addfake @username 1000")
        return
    
    username = args[1]
    try:
        balance = float(args[2])
    except:
        bot.send_message(msg.chat.id, "âŒ Ð‘Ð°Ð»Ð°Ð½Ñ Ð´Ð¾Ð»Ð¶ÐµÐ½ Ð±Ñ‹Ñ‚ÑŒ Ñ‡Ð¸ÑÐ»Ð¾Ð¼")
        return
    
    fake_users = init_fake_top()
    fake_users.append({"username": username, "balance": balance})
    fake_users.sort(key=lambda x: x['balance'], reverse=True)
    
    with open(FAKE_TOP_FILE, 'w', encoding='utf-8') as f:
        json.dump(fake_users, f, ensure_ascii=False, indent=2)
    
    bot.send_message(msg.chat.id, f"âœ… Ð”Ð¾Ð±Ð°Ð²Ð»ÐµÐ½ {username} Ñ Ð±Ð°Ð»Ð°Ð½ÑÐ¾Ð¼ {balance} â­")

@bot.message_handler(commands=['fake_list'])
def fake_list(msg):
    if msg.from_user.id not in ADMIN_IDS:
        bot.send_message(msg.chat.id, "âŒ ÐÐµÑ‚ Ð´Ð¾ÑÑ‚ÑƒÐ¿Ð°")
        return
    
    fake_users = init_fake_top()
    if not fake_users:
        bot.send_message(msg.chat.id, "ðŸ“­ Ð¤ÐµÐ¹Ðº-Ñ‚Ð¾Ð¿ Ð¿ÑƒÑÑ‚")
        return
    
    text = "ðŸ“‹ Ð¤Ð•Ð™Ðš-Ð¢ÐžÐŸ (JSON)\n\n"
    for i, u in enumerate(fake_users[:20]):
        text += f"{i+1}. {u['username']} â€” {u['balance']} â­\n"
    
    bot.send_message(msg.chat.id, text, parse_mode=None)

@bot.message_handler(commands=['removefake'])
def remove_fake(msg):
    if msg.from_user.id not in ADMIN_IDS:
        bot.send_message(msg.chat.id, "âŒ ÐÐµÑ‚ Ð´Ð¾ÑÑ‚ÑƒÐ¿Ð°")
        return
    
    args = msg.text.split()
    if len(args) < 2:
        bot.send_message(msg.chat.id, "âŒ Ð˜ÑÐ¿Ð¾Ð»ÑŒÐ·ÑƒÐ¹: /removefake @username")
        return
    
    username = args[1]
    fake_users = init_fake_top()
    
    new_list = [u for u in fake_users if u['username'] != username]
    
    if len(new_list) == len(fake_users):
        bot.send_message(msg.chat.id, f"âŒ {username} Ð½Ðµ Ð½Ð°Ð¹Ð´ÐµÐ½ Ð² Ñ„ÐµÐ¹Ðº-Ñ‚Ð¾Ð¿Ðµ")
        return
    
    with open(FAKE_TOP_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_list, f, ensure_ascii=False, indent=2)
    
    bot.send_message(msg.chat.id, f"âœ… Ð£Ð´Ð°Ð»Ñ‘Ð½ {username} Ð¸Ð· Ñ„ÐµÐ¹Ðº-Ñ‚Ð¾Ð¿Ð°")

@bot.message_handler(func=lambda m: m.text == "â—€ï¸ Ð’ Ð³Ð»Ð°Ð²Ð½Ð¾Ðµ Ð¼ÐµÐ½ÑŽ")
def back(msg):
    bot.send_message(msg.chat.id, "âœ… Ð’Ð¾Ð·Ð²Ñ€Ð°Ñ‚", reply_markup=main_kb())

@bot.message_handler(func=lambda m: m.text == "ðŸ“Š Ð¡Ñ‚Ð°Ñ‚Ð¸ÑÑ‚Ð¸ÐºÐ°")
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
    c.execute("SELECT COUNT(*) FROM referrals")
    refs = c.fetchone()[0] or 0
    c.execute("SELECT username, balance FROM users WHERE is_banned=0 ORDER BY balance DESC LIMIT 1")
    top = c.fetchone()
    conn.close()
    top_text = f"@{top[0] or 'â€”'} ({top[1]:.1f} â­)" if top else "ÐÐµÑ‚"
    bot.send_message(msg.chat.id,
        f"ðŸ“Š Ð¡Ð¢ÐÐ¢Ð˜Ð¡Ð¢Ð˜ÐšÐ\n\n"
        f"ðŸ‘¥ Ð’ÑÐµÐ³Ð¾: {total}\nâœ… ÐÐºÑ‚Ð¸Ð²Ð½Ñ‹Ñ…: {active}\n"
        f"ðŸ’° Ð—Ð°Ñ€Ð°Ð±Ð¾Ñ‚Ð°Ð½Ð¾: {earned:.1f} â­\nðŸ”„ ÐšÐ»Ð¸ÐºÐ¾Ð²: {clicks}\n"
        f"ðŸ‘¥ Ð ÐµÑ„ÐµÑ€Ð°Ð»Ð¾Ð²: {refs}\nðŸ† Ð¢Ð¾Ð¿-1: {top_text}",
        reply_markup=admin_kb(), parse_mode=None)

@bot.message_handler(func=lambda m: m.text == "ðŸ‘¥ Ð’ÑÐµ Ð¿Ð¾Ð»ÑŒÐ·Ð¾Ð²Ð°Ñ‚ÐµÐ»Ð¸")
def all_users(msg):
    if msg.from_user.id not in ADMIN_IDS:
        return
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT username, balance, created_at FROM users WHERE is_banned=0 ORDER BY created_at DESC LIMIT 20")
    users = c.fetchall()
    conn.close()
    if not users:
        bot.send_message(msg.chat.id, "ÐÐµÑ‚ Ð¿Ð¾Ð»ÑŒÐ·Ð¾Ð²Ð°Ñ‚ÐµÐ»ÐµÐ¹", reply_markup=admin_kb())
        return
    text = "ðŸ‘¥ ÐŸÐžÐ¡Ð›Ð•Ð”ÐÐ˜Ð• 20\n\n"
    for u in users:
        text += f"@{u[0] or 'â€”'} â€” {u[1]:.1f} â­ ({u[2][:10]})\n"
    bot.send_message(msg.chat.id, text, reply_markup=admin_kb(), parse_mode=None)

@bot.message_handler(func=lambda m: m.text == "ðŸ” Ð¢ÐžÐŸ-20")
def top20(msg):
    if msg.from_user.id not in ADMIN_IDS:
        return
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT username, balance, clicks FROM users WHERE is_banned=0 ORDER BY balance DESC LIMIT 20")
    users = c.fetchall()
    conn.close()
    text = "ðŸ” Ð¢ÐžÐŸ-20\n\n"
    medals = ["ðŸ¥‡","ðŸ¥ˆ","ðŸ¥‰"]
    for i, (uname, bal, clicks) in enumerate(users):
        m = medals[i] if i < 3 else f"{i+1}."
        text += f"{m} @{uname or 'â€”'} â€” {bal:.1f} â­ ({clicks} ÐºÐ»Ð¸ÐºÐ¾Ð²)\n"
    bot.send_message(msg.chat.id, text, reply_markup=admin_kb(), parse_mode=None)

@bot.message_handler(func=lambda m: m.text == "âœ‰ï¸ Ð Ð°ÑÑÑ‹Ð»ÐºÐ°")
def mail_start(msg):
    if msg.from_user.id not in ADMIN_IDS:
        return
    bot.send_message(msg.chat.id, "âœ‰ï¸ Ð’Ð²ÐµÐ´Ð¸ Ñ‚ÐµÐºÑÑ‚ Ñ€Ð°ÑÑÑ‹Ð»ÐºÐ¸ (Ð¸Ð»Ð¸ /cancel Ð´Ð»Ñ Ð¾Ñ‚Ð¼ÐµÐ½Ñ‹)", reply_markup=admin_kb())
    bot.register_next_step_handler(msg, mail_send)

def mail_send(msg):
    if msg.text == "/cancel":
        bot.send_message(msg.chat.id, "âŒ ÐžÑ‚Ð¼ÐµÐ½ÐµÐ½Ð¾", reply_markup=admin_kb())
        return
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT telegram_id FROM users WHERE is_banned=0")
    users = c.fetchall()
    conn.close()
    sent = 0
    for u in users:
        try:
            bot.send_message(u[0], f"ðŸ“¢ ÐžÐ‘ÐªÐ¯Ð’Ð›Ð•ÐÐ˜Ð•\n\n{msg.text}", parse_mode=None)
            sent += 1
        except:
            pass
    bot.send_message(msg.chat.id, f"âœ… ÐžÑ‚Ð¿Ñ€Ð°Ð²Ð»ÐµÐ½Ð¾ {sent} Ð¿Ð¾Ð»ÑŒÐ·Ð¾Ð²Ð°Ñ‚ÐµÐ»ÑÐ¼", reply_markup=admin_kb())

# ========== Ð—ÐÐŸÐ£Ð¡Ðš ==========
if __name__ == "__main__":
    print("ðŸ“¦ Ð£ÑÑ‚Ð°Ð½Ð°Ð²Ð»Ð¸Ð²Ð°ÐµÐ¼ Ð±Ð¸Ð±Ð»Ð¸Ð¾Ñ‚ÐµÐºÐ¸...")
    print("ðŸ“¦ Ð˜Ð½Ð¸Ñ†Ð¸Ð°Ð»Ð¸Ð·Ð°Ñ†Ð¸Ñ Ð‘Ð”...")
    init_db()
    print("âœ… Ð‘Ð” Ð³Ð¾Ñ‚Ð¾Ð²Ð°")
    print("ðŸ“¦ Ð˜Ð½Ð¸Ñ†Ð¸Ð°Ð»Ð¸Ð·Ð°Ñ†Ð¸Ñ Ñ„ÐµÐ¹Ðº-Ñ‚Ð¾Ð¿Ð°...")
    init_fake_top()
    print("âœ… Ð¤ÐµÐ¹Ðº-Ñ‚Ð¾Ð¿ Ð·Ð°Ð³Ñ€ÑƒÐ¶ÐµÐ½")
    print("ðŸš€ Ð—Ð°Ð¿ÑƒÑÐº Ð±Ð¾Ñ‚Ð°...")
    print("ðŸ¤– Ð‘Ð¾Ñ‚: @EarnSaveliyBot")
    print("ðŸ“Š ÐÐ°Ð¶Ð¼Ð¸ Ctrl+C Ð´Ð»Ñ Ð¾ÑÑ‚Ð°Ð½Ð¾Ð²ÐºÐ¸")
    print("ðŸ“º Ð ÐµÐºÐ»Ð°Ð¼Ð° Ð¿Ð¾Ð´ÐºÐ»ÑŽÑ‡ÐµÐ½Ð° Ñ‡ÐµÑ€ÐµÐ· GramAds")
    bot.polling(none_stop=True)


