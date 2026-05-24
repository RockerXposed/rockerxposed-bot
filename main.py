import os
import sqlite3
import requests
import telebot
import secrets
import time
from flask import Flask
from threading import Thread

# --- 1. RENDER PORT TIMEOUT BYPASS (FLASK SERVER) ---
app = Flask('')

@app.route('/')
def home():
    return "<h1>ROCKER XPOSED VIP SERVER IS RUNNING SMOOTHLY</h1>"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 2. BOT CONFIGURATION ---
BOT_TOKEN = "8497914783:AAH-EbriHxs3tvU-AnI70fxDyreblYgei-E"
ADMIN_IDS = [8347566603, 6631326358]

bot = telebot.TeleBot(BOT_TOKEN)
BASE_URL = "https://todayfree.xo.je"

user_sessions = {}
last_dashboard_id = {}

# --- 3. DATABASE SETUP (CREDITS & KEYS) ---
def init_db():
    conn = sqlite3.connect('automation_stats.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS user_credits 
                 (user_id INTEGER PRIMARY KEY, credits INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS keys_pool 
                 (key_code TEXT PRIMARY KEY, credits INTEGER, status TEXT)''')
    conn.commit()
    conn.close()

def get_user_credits(user_id):
    if user_id in ADMIN_IDS:
        return 999999
    conn = sqlite3.connect('automation_stats.db')
    c = conn.cursor()
    c.execute("SELECT credits FROM user_credits WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def add_user_credits(user_id, credits_to_add):
    conn = sqlite3.connect('automation_stats.db')
    c = conn.cursor()
    c.execute("SELECT credits FROM user_credits WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if row:
        new_credits = row[0] + credits_to_add
        c.execute("UPDATE user_credits SET credits = ? WHERE user_id = ?", (new_credits, user_id))
    else:
        c.execute("INSERT INTO user_credits (user_id, credits) VALUES (?, ?)", (user_id, credits_to_add))
    conn.commit()
    conn.close()

def deduct_user_credits(user_id, credits_to_deduct):
    if user_id in ADMIN_IDS:
        return
    conn = sqlite3.connect('automation_stats.db')
    c = conn.cursor()
    c.execute("SELECT credits FROM user_credits WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if row:
        new_credits = max(0, row[0] - credits_to_deduct)
        c.execute("UPDATE user_credits SET credits = ? WHERE user_id = ?", (new_credits, user_id))
    conn.commit()
    conn.close()

def generate_key_in_db(credits_val):
    key_code = f"RX-{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}"
    conn = sqlite3.connect('automation_stats.db')
    c = conn.cursor()
    c.execute("INSERT INTO keys_pool (key_code, credits, status) VALUES (?, ?, 'UNUSED')", (key_code, credits_val))
    conn.commit()
    conn.close()
    return key_code

def redeem_key_in_db(user_id, key_code):
    conn = sqlite3.connect('automation_stats.db')
    c = conn.cursor()
    c.execute("SELECT credits FROM keys_pool WHERE key_code = ? AND status = 'UNUSED'", (key_code,))
    row = c.fetchone()
    if row:
        credits_val = row[0]
        c.execute("UPDATE keys_pool SET status = 'USED' WHERE key_code = ?", (key_code,))
        conn.commit()
        conn.close()
        add_user_credits(user_id, credits_val)
        return True, credits_val
    conn.close()
    return False, 0

# --- 4. ADMIN SUITE ---
@bot.message_handler(commands=['genkey'])
def handle_genkey(message):
    if message.from_user.id in ADMIN_IDS:
        try:
            args = message.text.split()
            if len(args) < 2:
                bot.reply_to(message, "❌ Format: `/genkey [credits]`\nExample: `/genkey 200`")
                return
            credits_val = int(args[1])
            new_key = generate_key_in_db(credits_val)
            bot.reply_to(message, f"🔑 *KEY GENERATED:* `{new_key}`\n💰 *Credits:* {credits_val} Reach", parse_mode="Markdown")
        except Exception as e:
            bot.reply_to(message, f"❌ Error: {str(e)}")

# --- 5. AUTOMATION LOGIC ---
def start_automation_flow(tech_id, password):
    session = requests.Session()
    session.headers.update({
        'Content-Type': 'application/json',
        'X-Requested-With': 'welcome.to.dynamoscode',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Mobile)'
    })
    
    login_payload = {"tech_id": str(tech_id), "password": str(password)}
    login_data = {}
    
    # Dono router endpoints securely test karega
    try:
        login_res = session.post(f"{BASE_URL}/api/login.php", json=login_payload, timeout=12)
        login_data = login_res.json()
    except Exception:
        try:
            login_res = session.post(f"{BASE_URL}/login.php", json=login_payload, timeout=12)
            login_data = login_res.json()
        except Exception:
            return "server_error", 0

    if login_data.get("success") is True or login_data.get("status") == "success":
        orders_list = []
        try:
            orders_res = session.get(f"{BASE_URL}/api/get_orders.php?tech_id={tech_id}", timeout=12)
            orders_list = orders_res.json().get("orders", [])
        except Exception:
            try:
                orders_res = session.get(f"{BASE_URL}/get_orders.php?tech_id={tech_id}", timeout=12)
                orders_list = orders_res.json().get("orders", [])
            except Exception:
                return "error_fetch", 0

        progress_orders = [o for o in orders_list if str(o.get("status", "")).lower() == "in progress"]
        if not progress_orders:
            return "no_orders", 0
        
        reached_successfully = 0
        for order in progress_orders:
            try:
                reach_payload = {"wo_id": order.get("id"), "status": "REACHED", "lat": "28.6139", "lon": "77.2090"}
                reach_res = session.post(f"{BASE_URL}/api/mark_reached.php", json=reach_payload, timeout=10)
                if reach_res.status_code != 200:
                    reach_res = session.post(f"{BASE_URL}/mark_reached.php", json=reach_payload, timeout=10)
                
                if reach_res.status_code == 200:
                    reached_successfully += 1
            except Exception:
                continue
        
        if reached_successfully > 0:
            return "success", reached_successfully
        return "failed_reach", 0
    return "auth_failed", 0

# --- 6. PREMIUM DASHBOARD MENUS FLOW ---
def send_initial_menu(chat_id, user_id):
    if chat_id in last_dashboard_id:
        try: bot.delete_message(chat_id, last_dashboard_id[chat_id])
        except Exception: pass

    user_credits = get_user_credits(user_id)
    sent_msg = None
    
    if user_id in ADMIN_IDS:
        user_sessions[chat_id] = "AUTHORIZED"
        admin_menu = (
            "🚀 *Welcome To Rocker Xposed* 👑\n"
            "▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️\n"
            "⚡ • *Fast Reach Service.*\n"
            "🔓 • *Without Otp Setup.*\n"
            "📍 • *Google Map Error Fix.*\n"
            "🚪 • *Auto Logout.*\n"
            "💎 • *Credit:* `Unlimited`\n"
            "📝 • *I'd & Password:* `{06##,Pa##}`\n\n"
            "👉 *Apni Details `ID,Password` Format Mein Send Karein:*"
        )
        sent_msg = bot.send_message(chat_id, admin_menu, parse_mode="Markdown")
    elif user_credits <= 0:
        user_sessions[chat_id] = "NEED_KEY"
        buy_menu = (
            "👋 *Welcome To Rocker Xposed* 🔥\n\n"
            "❌ Aapke paas is bot ko use karne ke liye *0 Credits* bache hain.\n\n"
            "🔑 • *Enter License Key* \n"
            "🛒 • *Buy License Key*"
        )
        sent_msg = bot.send_message(chat_id, buy_menu, parse_mode="Markdown")
    else:
        user_sessions[chat_id] = "AUTHORIZED"
        user_menu = (
            "🚀 *Welcome To Rocker Xposed* 👋\n"
            "▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️\n"
            "⚡ • *Fast Reach Service.*\n"
            "🔓 • *Without Otp Setup.*\n"
            "📍 • *Google Map Error Fix.*\n"
            "🚪 • *Auto Logout.*\n"
            f"💰 • *Credit:* `{user_credits}`\n"
            "📝 • *I'd & Password:* `{06##,Pa##}`\n\n"
            "👉 *Apni Details `ID,Password` Format Mein Send Karein:*"
        )
        sent_msg = bot.send_message(chat_id, user_menu, parse_mode="Markdown")

    if sent_msg:
        last_dashboard_id[chat_id] = sent_msg.message_id

@bot.message_handler(commands=['start', 'help'])
def start_cmd(message):
    send_initial_menu(message.chat.id, message.from_user.id)

# --- 7. MAIN CHAT ACTIONS & AUTO CLEAR ---
@bot.message_handler(func=lambda message: True)
def handle_incoming_messages(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    msg_text = message.text.strip()
    
    try: bot.delete_message(chat_id, message.message_id)
    except Exception: pass

    if chat_id not in user_sessions:
        if get_user_credits(user_id) > 0 or user_id in ADMIN_IDS:
            user_sessions[chat_id] = "AUTHORIZED"
        else:
            user_sessions[chat_id] = "NEED_KEY"

    if user_sessions[chat_id] == "NEED_KEY":
        success, credits_gained = redeem_key_in_db(user_id, msg_text)
        if success:
            user_sessions[chat_id] = "AUTHORIZED"
            success_msg = bot.send_message(chat_id, f"✅ *Key Activated Successfully!*\n💰 `{credits_gained}` Credits added.")
            time.sleep(2)
            try: bot.delete_message(chat_id, success_msg.message_id)
            except Exception: pass
            send_initial_menu(chat_id, user_id)
        else:
            bot.send_message(chat_id, "❌ *Invalid License Key!* Kripya sahi enter karein:")
        return

    if "," in msg_text:
        if get_user_credits(user_id) <= 0:
            user_sessions[chat_id] = "NEED_KEY"
            send_initial_menu(chat_id, user_id)
            return
            
        status_msg = bot.send_message(chat_id, "⏳ *VIP Server 2.0.7 processing...* Kripya wait karein.")
        
        try:
            tech_id, tech_password = msg_text.split(",", 1)
            tech_id = tech_id.strip()
            tech_password = tech_password.strip()
        except Exception:
            bot.edit_message_text("❌ *Format error!* Use `ID,Password` format.", chat_id, status_msg.message_id)
            return

        result, count = start_automation_flow(tech_id, tech_password)
        
        if result == "success":
            deduct_user_credits(user_id, count)
            rem_credits = get_user_credits(user_id)
            bot.edit_message_text(f"

