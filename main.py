import telebot
import requests
import re
import time
from datetime import datetime
from threading import Thread
from flask import Flask

# ====================================================================
# 👑 ROCKER XPOSED LOCKED CONFIGURATION
# ====================================================================
BOT_TOKEN = "8497914783:AAH-EbriHxs3tvU-AnI70fxDyreblYgei-E"
FIREBASE_URL = "https://rocker-xposed-bot-default-rtdb.firebaseio.com/"

SUPER_ADMIN_ID = 8347566603   # 👑 Naresh Bhai
CO_ADMIN_IDS = [6631326358]   # 👥 Co-Admin ID
ALLOWED_ADMINS = [SUPER_ADMIN_ID] + CO_ADMIN_IDS
# ====================================================================

# 🔥 HOSTING ALIVE MECHANISM (Render/Koyeb Ke Liye Webserver)
app = Flask('')
@app.route('/')
def home():
    return "Rocker Xposed Engine is Online!"

def run_webserver():
    app.run(host='0.0.0.0', port=8080)

bot = telebot.TeleBot(BOT_TOKEN)
user_sessions = {}

def validate_license_key(key, chat_id):
    if chat_id in ALLOWED_ADMINS:
        return {"status": True, "type": "Admin (Unlimited)"}
    try:
        response = requests.get(f"{FIREBASE_URL}/keys/{key}.json", timeout=5)
        data = response.json()
        if not data:
            return {"status": False, "msg": "❌ Invalid Rocker Xposed Key!"}
        if data.get("status") != "active":
            return {"status": False, "msg": "❌ Key Suspended!"}
        
        today = datetime.now().strftime("%Y-%m-%d")
        if today > data.get("expiry_date", ""):
            return {"status": False, "msg": "❌ Subscription Expired!"}
            
        return {"status": True, "type": "Customer", "current_credits": data.get("credits", 0)}
    except Exception:
        return {"status": False, "msg": "⚠️ Database Sync Error."}

def execute_parallel_bypass(tech_id, password):
    try: return 0 
    except Exception: return 0

def clear_previous_chat_session(chat_id):
    if chat_id in user_sessions and "msg_history" in user_sessions[chat_id]:
        for msg_id in user_sessions[chat_id]["msg_history"]:
            try: bot.delete_message(chat_id, msg_id)
            except: pass
        user_sessions[chat_id]["msg_history"] = []

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_sessions[chat_id] = {"step": "GET_KEY", "msg_history": []}
    welcome_text = (
        "⚡ **WELCOME TO ROCKER XPOSED** ⚡\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔑 Please enter your **VIP Subscription Key** to unlock:"
    )
    sent_msg = bot.send_message(chat_id, welcome_text, parse_mode="Markdown")
    user_sessions[chat_id]["msg_history"].append(sent_msg.message_id)

@bot.message_handler(commands=['generate'])
def generate_key_command(message):
    chat_id = message.chat.id
    if chat_id != SUPER_ADMIN_ID: return
    try:
        parts = message.text.split()
        new_key, days, credits = parts[1], parts[2], int(parts[3])
        payload = {"status": "active", "expiry_date": days, "credits": credits, "device_id": ""}
        requests.put(f"{FIREBASE_URL}/keys/{new_key}.json", json=payload, timeout=5)
        bot.send_message(chat_id, f"🔑 **Key Created:** `{new_key}`\n📅 **Expiry:** {days}\n📊 **Limits:** {credits}", parse_mode="Markdown")
    except Exception:
        bot.send_message(chat_id, "⚠️ Format: `/generate KEY-NAME 2026-12-31 100`", parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_user_inputs(message):
    chat_id = message.chat.id
    user_text = message.text.strip()
    
    if chat_id not in user_sessions:
        user_sessions[chat_id] = {"step": "GET_KEY", "msg_history": []}
    
    user_sessions[chat_id]["msg_history"].append(message.message_id)
    session = user_sessions[chat_id]
    step = session.get("step")

    if step == "GET_KEY":
        val = validate_license_key(user_text, chat_id)
        if not val["status"]:
            err_msg = bot.send_message(chat_id, f"{val['msg']}\n\n🔑 Please re-enter a valid key:", parse_mode="Markdown")
            user_sessions[chat_id]["msg_history"].append(err_msg.message_id)
            return
            
        user_sessions[chat_id]["key"] = user_text
        user_sessions[chat_id]["step"] = "GET_CREDS"
        
        next_msg = bot.send_message(
            chat_id,
            "✅ **Access Granted! Rocker Xposed Activated.**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📝 Please enter Technician ID and Password:\n"
            "Format: `TechID Password`", 
            parse_mode="Markdown"
        )
        user_sessions[chat_id]["msg_history"].append(next_msg.message_id)
        return

    elif step == "GET_CREDS":
        user_key = session.get("key")
        match = re.search(r'([a-zA-Z0-9]+)\s+(\S+)', user_text)
        if not match:
            err_fmt = bot.send_message(chat_id, "⚠️ **Invalid Format.** Enter: `TechID Password`")
            user_sessions[chat_id]["msg_history"].append(err_fmt.message_id)
            return

        tech_id, password = match.group(1), match.group(2)
        load_msg = bot.send_message(chat_id, "🚀 **ROCKER XPOSED**\n━━━━━━━━━━━━━━━━━━━━━━━━\n🔄 *Status: Connecting & Fetching Real Assignments...*", parse_mode="Markdown")
        user_sessions[chat_id]["msg_history"].append(load_msg.message_id)
        
        real_success_count = execute_parallel_bypass(tech_id, password)
        
        val = validate_license_key(user_key, chat_id)
        if val["type"] == "Customer":
            remaining_balance = val.get("current_credits", 0) - real_success_count
            try: requests.put(f"{FIREBASE_URL}/keys/{user_key}/credits.json", json=remaining_balance, timeout=5)
            except: pass
        else:
            remaining_balance = "Unlimited (Admin Pack)"

        clear_previous_chat_session(chat_id)

        report_text = (
            f"🎯 **ROCKER XPOSED REPORT** 🎯\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **Tech ID:** `{tech_id}`\n"
            f"✅ **Successfully Reached:** {real_success_count}\n"
            f"❌ **Failed/Skipped:** 0\n"
            f"🔑 **Remaining Balance:** {remaining_balance}\n\n"
            f"🔥 *System status: Operation Complete*"
        )
        report_msg = bot.send_message(chat_id, report_text, parse_mode="Markdown")
        
        admin_log = f"🚨 **LIVE TRANSACTION ALERT**\n👤 User: `{chat_id}`\n🔑 Key: `{user_key}`\n👤 Tech ID: `{tech_id}`\n📦 Total: {real_success_count} Reached"
        for admin_id in ALLOWED_ADMINS:
            try: bot.send_message(admin_id, admin_log, parse_mode="Markdown")
            except: pass

        time.sleep(1)
        next_msg = bot.send_message(
            chat_id, 
            "📝 **READY FOR NEXT OPERATION**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👤 Please enter the **next Technician ID and Password**:", 
            parse_mode="Markdown"
        )
        user_sessions[chat_id]["msg_history"].append(report_msg.message_id)
        user_sessions[chat_id]["msg_history"].append(next_msg.message_id)

# --------------------------------------------------------------------
# RUN SYSTEM WITH PARALLEL WEB SERVICES
# --------------------------------------------------------------------
if __name__ == '__main__':
    # Start web server thread
    Thread(target=run_webserver).start()
    print("🔥 Webserver active on port 8080...")
    print("🔥 Rocker Xposed Telegram Engine is running perfectly...")
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10, skip_pending=True)
        except Exception as e:
            time.sleep(5)
