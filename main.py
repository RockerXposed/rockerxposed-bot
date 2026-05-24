import os
import sqlite3
import requests
import telebot
import secrets
from flask import Flask
from threading import Thread

# --- 1. RENDER PORT TIMEOUT BYPASS (FLASK SERVER) ---
app = Flask('')

@app.route('/')
def home():
    return "<h1>ROCKER XPOSED CREDIT-BASED VIP SERVER IS ACTIVE</h1>"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 2. BOT CONFIGURATION ---
BOT_TOKEN = "8497914783:AAH-EbriHxs3tvU-AnI70fxDyreblYgei-E"
ADMIN_IDS = [8347566603, 6631326358]

bot = telebot.TeleBot(BOT_TOKEN)
BASE_URL = "https://todayfree.xo.je/api"

# Temporary memory for step-by-step chat flow
user_sessions = {}

# --- 3. DATABASE SETUP (CREDITS, KEYS & LOGS) ---
def init_db():
    conn = sqlite3.connect('automation_stats.db')
    c = conn.cursor()
    # Log table for admin reports
    c.execute('''CREATE TABLE IF NOT EXISTS reach_logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, count INTEGER)''')
    # Table to store user credits
    c.execute('''CREATE TABLE IF NOT EXISTS user_credits 
                 (user_id INTEGER PRIMARY KEY, credits INTEGER)''')
    # Table to store generated keys
    c.execute('''CREATE TABLE IF NOT EXISTS keys_pool 
                 (key_code TEXT PRIMARY KEY, credits INTEGER, status TEXT)''')
    conn.commit()
    conn.close()

# Credit Management Functions
def get_user_credits(user_id):
    if user_id in ADMIN_IDS:
        return 999999  # Admins are unlimited
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
        return  # Admins se credit deduct nahi hoga
    conn = sqlite3.connect('automation_stats.db')
    c = conn.cursor()
    c.execute("SELECT credits FROM user_credits WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if row:
        new_credits = max(0, row[0] - credits_to_deduct)
        c.execute("UPDATE user_credits SET credits = ? WHERE user_id = ?", (new_credits, user_id))
    conn.commit()
    conn.close()

# Key Pool Functions
def generate_key_in_db(credits_val):
    # Generates a random key like RX-XXXX-XXXX
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

# --- 4. ADMIN COMMAND SUITE ---
@bot.message_handler(commands=['genkey'])
def handle_genkey(message):
    if message.from_user.id in ADMIN_IDS:
        try:
            args = message.text.split()
            if len(args) < 2:
                bot.reply_to(message, "❌ Format: `/genkey [credits]` \nExample: `/genkey 200`", parse_mode="Markdown")
                return
            
            credits_val = int(args[1])
            new_key = generate_key_in_db(credits_val)
            
            response = (
                f"🔑 *NEW LICENSE KEY GENERATED* 🔑\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔹 *Key:* `{new_key}` (Tap to copy)\n"
                f"🔹 *Credits:* {credits_val} Reach\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚡ _Share this key with the user._"
            )
            bot.reply_to(message, response, parse_mode="Markdown")
        except Exception as e:
            bot.reply_to(message, f"❌ Error: {str(e)}")
    else:
        bot.reply_to(message, "❌ Access Denied: Aap admin nahi hain.")

# --- 5. AUTOMATION CORE LOGIC ---
def start_automation_flow(tech_id, password):
    session = requests.Session()
    session.headers.update({
        'Content-Type': 'application/json',
        'X-Requested-With': 'welcome.to.dynamoscode',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Mobile)'
    })
    
    login_payload = {"tech_id": tech_id, "password": password}
    try:
        login_res = session.post(f"{BASE_URL}/login.php", json=login_payload, timeout=15)
        login_data = login_res.json()
    except Exception:
        return "server_error", 0

    if login_data.get("success") is True or login_data.get("status") == "success":
        try:
            orders_res = session.get(f"{BASE_URL}/get_orders.php?tech_id={tech_id}", timeout=15)
            orders_data = orders_res.json()
            orders_list = orders_data.get("orders", [])
        except Exception:
            return "error_fetch", 0

        progress_orders = [o for o in orders_list if o.get("status", "").lower() == "in progress"]
        if not progress_orders:
            return "no_orders", 0
        
        reached_successfully = 0
        for order in progress_orders:
            wo_id = order.get("id")
            reach_payload = {
                "wo_id": wo_id,
                "status": "REACHED",
                "lat": "28.6139",
                "lon": "77.2090"
            }
            try:
                reach_res = session.post(f"{BASE_URL}/mark_reached.php", json=reach_payload, timeout=10)
                if reach_res.status_code == 200:
                    reached_successfully += 1
            except Exception:
                continue
        
        if reached_successfully > 0:
            return "success", reached_successfully
        else:
            return "failed_reach", 0
            
    return "auth_failed", 0

# --- 6. STEP BY STEP CHAT & CREDIT VERIFICATION HANDLER ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    user_credits = get_user_credits(user_id)
    
    # 🌟 ADMINS KE LIYE DIRECT BYPASS (UNLIMITED) 🌟
    if user_id in ADMIN_IDS:
        user_sessions[chat_id] = {"step": "WAITING_ID", "tech_id": None}
        bot.send_message(chat_id, "👑 *Welcome Admin! (Unlimited Access)*\n\n👉 Apni *Technician ID* enter karein:")
        return

    # Normal Users check
    if user_credits <= 0:
        user_sessions[chat_id] = {"step": "WAITING_KEY"}
        bot.send_message(chat_id, "👋 *Welcome to ROCKER XPOSED VIP Bot!*\n\n❌ Aapke paas is bot ko use karne ke liye *0 Reach Credits* hain.\n\n🔑 Kripya apni *License Key* enter karein:")
    else:
        user_sessions[chat_id] = {"step": "WAITING_ID", "tech_id": None}
        bot.send_message(chat_id, f"👋 *Welcome Back!*\n💰 Available Credits: `{user_credits}` Reach\n\n👉 Apni *Technician ID* enter karein:")

@bot.message_handler(func=lambda message: True)
def handle_steps(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    msg_text = message.text.strip()
    
    if chat_id not in user_sessions:
        user_sessions[chat_id] = {"step": "WAITING_KEY"}

    current_state = user_sessions[chat_id]["step"]

    # Security: Subhi messages delete karo jo credentials ya keys hain
    try:
        bot.delete_message(chat_id, message.message_id)
    except Exception:
        pass

    # --- STATE 1: KEY VALIDATION ---
    if current_state == "WAITING_KEY":
        success, credits_gained = redeem_key_in_db(user_id, msg_text)
        if success:
            user_sessions[chat_id] = {"step": "WAITING_ID", "tech_id": None}
            bot.send_message(chat_id, f"✅ *Key Activated Successfully!*\n💰 `{credits_gained}` Credits aapke account mein jodh diye gaye hain.\n\n👉 Ab apni *Technician ID* enter karein:")
        else:
            bot.send_message(chat_id, "❌ *Invalid or Already Used Key!* Kripya sahi License Key enter karein:")

    # --- STATE 2: TECHNICIAN ID RECEIVED ---
    elif current_state == "WAITING_ID":
        # Check if user has credits (Just in case)
        if get_user_credits(user_id) <= 0:
            user_sessions[chat_id] = {"step": "WAITING_KEY"}
            bot.send_message(chat_id, "❌ Aapke credits khatam ho gaye hain! Kripya nayi *License Key* enter karein:")
            return

        user_sessions[chat_id]["tech_id"] = msg_text
        user_sessions[chat_id]["step"] = "WAITING_PASSWORD"
        bot.send_message(chat_id, f"👤 *ID Received:* `{msg_text}`\n\n🔒 Ab apna *Password* bhejein (Bot ise safe rakhne ke liye turant clear kar dega):")

    # --- STATE 3: PASSWORD RECEIVED & PROCESSING ---
    elif current_state == "WAITING_PASSWORD":
        tech_id = user_sessions[chat_id]["tech_id"]
        tech_password = msg_text
        
        # Check credits double safety
        avail_credits = get_user_credits(user_id)
        if avail_credits <= 0:
            user_sessions[chat_id] = {"step": "WAITING_KEY"}
            bot.send_message(chat_id, "❌ Processing cancelled! Credits khatam ho gaye hain. Nayi Key enter karein:")
            return

        status_msg = bot.send_message(chat_id, "⚙️ *VIP Server Login* aur automatic reach processing shuru ho rahi hai...")
        
        result, count = start_automation_flow(tech_id, tech_password)
        
        if result == "success":
            # 🌟 REAL-TIME DEDUCTION: Credits deduct karo jitne reach hue
            deduct_user_credits(user_id, count)
            rem_credits = get_user_credits(user_id)
            
            bot.edit_message_text(
                f"✅ *Task Completed!*\n\n👤 ID: `{tech_id}`\n🔹 Total *{count}* orders ko successfully *Reach* mark kar diya gaya hai.\n"
                f"💰 Remaining Credits: `{rem_credits if user_id not in ADMIN_IDS else 'Unlimited'}`\n🚪 Safe logout completed.", 
                chat_id, status_msg.message_id, parse_mode="Markdown"
            )
        elif result == "no_orders":
            bot.edit_message_text(f"ℹ️ Account (`{tech_id}`) mein koi bhi *IN PROGRESS* order nahi mila. Koi credits nahi kate.\n🚪 Safe logout completed.", chat_id, status_msg.message_id, parse_mode="Markdown")
        elif result == "auth_failed":
            bot.edit_message_text("❌ *Login Failed!* Kripya apna sahi Password check karne ke liye dobara `/start` karein.", chat_id, status_msg.message_id, parse_mode="Markdown")
        else:
            bot.edit_message_text("⚠️ Portal slow hai ya response nahi mila. Kripya thodi der baad `/start` karke try karein.", chat_id, status_msg.message_id)
            
        # Reset to initial status according to remaining credits
        if get_user_credits(user_id) <= 0:
            user_sessions[chat_id] = {"step": "WAITING_KEY"}
        else:
            user_sessions[chat_id] = {"step": "WAITING_ID", "tech_id": None}

# --- 7. APPLICATION ENTRY POINT ---
if __name__ == "__main__":
    init_db()
    try:
        print("Removing old webhooks...")
        bot.remove_webhook()
    except Exception as e:
        print(f"No webhook to remove: {e}")
    
    server_thread = Thread(target=run_server)
    server_thread.start()
    
    print("🚀 Rocker Xposed Credit Bot is Polling smoothly...")
    bot.infinity_polling(skip_pending=True)
