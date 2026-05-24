import os
import sqlite3
import requests
import telebot
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread

# --- 1. RENDER PORT TIMEOUT BYPASS (FLASK SERVER) ---
app = Flask('')

@app.route('/')
def home():
    return "<h1>ROCKER XPOSED VIP SERVER BOT IS ACTIVE</h1>"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 2. BOT CONFIGURATION ---
BOT_TOKEN = "8497914783:AAH-EbriHxs3tvU-AnI70fxDyreblYgei-E"

# 🌟 DONO ADMIN IDs YAHAN SET KAR DI HAIN 🌟
ADMIN_IDS = [8347566603, 6631326358]

bot = telebot.TeleBot(BOT_TOKEN)
BASE_URL = "https://todayfree.xo.je/api"

# --- 3. DATABASE SETUP (FOR REPORTS) ---
def init_db():
    conn = sqlite3.connect('automation_stats.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reach_logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, count INTEGER)''')
    conn.commit()
    conn.close()

def update_reach_count(count):
    conn = sqlite3.connect('automation_stats.db')
    c = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    
    c.execute("SELECT count FROM reach_logs WHERE date = ?", (today,))
    row = c.fetchone()
    if row:
        new_count = row[0] + count
        c.execute("UPDATE reach_logs SET count = ? WHERE date = ?", (new_count, today))
    else:
        c.execute("INSERT INTO reach_logs (date, count) VALUES (?, ?)", (today, count))
        
    conn.commit()
    conn.close()

def fetch_report(days):
    conn = sqlite3.connect('automation_stats.db')
    c = conn.cursor()
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    c.execute("SELECT SUM(count) FROM reach_logs WHERE date >= ?", (start_date,))
    result = c.fetchone()[0]
    conn.close()
    return result if result else 0

# --- 4. ADMIN COMMAND SUITE ---
@bot.message_handler(commands=['report'])
def send_analytics(message):
    # Check if the user is in the admin list
    if message.from_user.id in ADMIN_IDS:
        daily = fetch_report(0)   
        weekly = fetch_report(7)  
        monthly = fetch_report(30) 
        
        report_text = (
            f"📊 *ROCKER XPOSED - PERFORMANCE REPORT* 📊\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔹 *Today Reached:* {daily} Orders\n"
            f"🔹 *This Week Total:* {weekly} Orders\n"
            f"🔹 *This Month Total:* {monthly} Orders\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ _VIP Server Operational_"
        )
        bot.reply_to(message, report_text, parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ Access Denied: Aap is bot ke admin nahi hain.")

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
            update_reach_count(reached_successfully)
            return "success", reached_successfully
        else:
            return "failed_reach", 0
            
    return "auth_failed", 0

# --- 6. TEXT MESSAGE HANDLER (ID & PASSWORD DETECTOR) ---
@bot.message_handler(func=lambda message: True)
def handle_incoming_credentials(message):
    chat_id = message.chat.id
    msg_text = message.text.strip()
    
    if "," in msg_text:
        try:
            bot.delete_message(chat_id, message.message_id)
        except Exception as e:
            print(f"Message clear failed: {e}")
            
        status_msg = bot.send_message(chat_id, "🔒 *Credentials Secure!* Chat ko clear kar diya gaya hai.\n⚙️ VIP Server login aur automatic reach processing shuru ho rahi hai...")
        
        try:
            tech_id, tech_password = msg_text.split(",", 1)
            tech_id = tech_id.strip()
            tech_password = tech_password.strip()
        except Exception:
            bot.edit_message_text("❌ Galat format! Kripya `ID,Password` format mein bhejin (beech mein comma hona chahiye).", chat_id, status_msg.message_id)
            return

        result, count = start_automation_flow(tech_id, tech_password)
        
        if result == "success":
            bot.edit_message_text(f"✅ *Task Completed!*\n\n🔹 Total *{count}* In-Progress orders ko successfully Reach mark kar diya gaya hai.\n🚪 Account automatic logout ho chuka hai.", chat_id, status_msg.message_id, parse_mode="Markdown")
        elif result == "no_orders":
            bot.edit_message_text("ℹ️ Aapke account mein koi bhi *IN PROGRESS* order nahi mila.\n🚪 Safe logout completed.", chat_id, status_msg.message_id, parse_mode="Markdown")
        elif result == "auth_failed":
            bot.edit_message_text("❌ *Login Failed!* Kripya apna sahi Technician ID aur Password check karein.", chat_id, status_msg.message_id, parse_mode="Markdown")
        else:
            bot.edit_message_text("⚠️ Server se contact nahi ho pa raha hai ya portal slow hai. Kripya thodi der baad try karein.", chat_id, status_msg.message_id)
            
    else:
        bot.reply_to(message, "👋 Welcome to ROCKER XPOSED VIP Bot!\n\n👉 Apne orders automatic reach karne ke liye apni details is tarah bhejein:\n`AapkiID,AapkaPassword`\n\n_(Note: Details padhte hi bot chat se delete kar dega)_", parse_mode="Markdown")

# --- 7. APPLICATION ENTRY POINT ---
if __name__ == "__main__":
    init_db()
    
    server_thread = Thread(target=run_server)
    server_thread.start()
    
    print("🚀 Rocker Xposed Bot is Polling smoothly with Main Server...")
    bot.infinity_polling()

