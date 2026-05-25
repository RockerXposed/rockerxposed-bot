import os
import sqlite3
import requests
import json
import telebot
import secrets
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from threading import Thread

# --- 1. CLOUD WEB ENGINE SERVER WITH CORS ---
app = Flask('')
CORS(app)

# Session tracking pool for multi-ID support
session_pool = {}

@app.route('/')
def home():
    return "<h1>ROCKER XPOSED ANTI-BOT CORE IS ACTIVE</h1>"

@app.route('/api/web_login', methods=['POST'])
def web_login():
    try:
        data = request.json
        tech_id = str(data.get("tech_id", "")).strip()
        password = str(data.get("password", "")).strip()
        
        session = requests.Session()
        
        # 🌟 EXAPCT HEADERS & SYSTEM CONFIG FROM REQABLE LOG 🌟
        session.headers.update({
            'Content-Type': 'application/x-www-form-urlencoded', 
            'X-Requested-With': 'welcome.to.dynamoscode',
            'User-Agent': 'Mozilla/5.0 (Linux; Android; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36'
        })
        
        # 🔐 INJECTING THE REQABLE SECURITY COOKIES 🔐
        jar = requests.cookies.RequestsCookieJar()
        jar.set('__test', '889f999ca1bb6aca47b93a5181ffbc58', domain='todayfree.xo.je', path='/')
        session.cookies = jar
        
        # Standard Form payload
        login_payload = {
            "tech_id": tech_id, 
            "password": password
        }
        
        res = session.post("https://todayfree.xo.je/api/login.php", data=login_payload, timeout=12)
        res_data = res.json()
        
        if res_data.get("success") is True or res_data.get("status") == "success":
            session_pool[tech_id] = session
            
        return jsonify(res_data)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/web_orders', methods=['GET'])
def web_orders():
    try:
        tech_id = str(request.args.get("tech_id", "")).strip()
        session = session_pool.get(tech_id)
        
        if not session:
            return jsonify({"success": False, "orders": [], "message": "Session expired."})
            
        res = session.get(f"https://todayfree.xo.je/api/get_orders.php?tech_id={tech_id}", timeout=12)
        return jsonify(res.json())
    except Exception as e:
        return jsonify({"orders": []}), 500

@app.route('/api/web_reach', methods=['POST'])
def web_reach():
    try:
        data = request.json
        tech_id = str(data.get("tech_id", "")).strip()
        wo_id = str(data.get("wo_id", "")).strip()
        
        session = session_pool.get(tech_id)
        if not session:
            return jsonify({"success": False, "message": "No active session found"}), 401
            
        reach_payload = {
            "wo_id": wo_id,
            "customer": "Unknown Customer",
            "address": "N/A"
        }
        res = session.post("https://todayfree.xo.je/api/mark_reached.php", data=reach_payload, timeout=12)
        if res.status_code == 200:
            return jsonify({"success": True})
        return jsonify({"success": False}), 400
    except Exception:
        return jsonify({"success": False}), 500

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 2. TELEGRAM BOT INITIALIZATION ---
BOT_TOKEN = "8497914783:AAH-EbriHxs3tvU-AnI70fxDyreblYgei-E"
ADMIN_IDS = [8347566603, 6631326358]
bot = telebot.TeleBot(BOT_TOKEN)

def init_db():
    conn = sqlite3.connect('automation_stats.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS user_credits (user_id INTEGER PRIMARY KEY, credits INTEGER)''')
    conn.commit()
    conn.close()

def get_user_credits(user_id):
    if user_id in ADMIN_IDS: return 999999
    conn = sqlite3.connect('automation_stats.db')
    c = conn.cursor()
    c.execute("SELECT credits FROM user_credits WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def deduct_user_credits(user_id, credits_to_deduct):
    if user_id in ADMIN_IDS: return
    conn = sqlite3.connect('automation_stats.db')
    c = conn.cursor()
    c.execute("SELECT credits FROM user_credits WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if row:
        new_credits = max(0, row[0] - credits_to_deduct)
        c.execute("UPDATE user_credits SET credits = ? WHERE user_id = ?", (new_credits, user_id))
    conn.commit()
    conn.close()

# --- 3. BOT AUTOMATION LOGIC ---
def start_automation_flow(tech_id, password):
    session = requests.Session()
    session.headers.update({
        'Content-Type': 'application/x-www-form-urlencoded', 
        'X-Requested-With': 'welcome.to.dynamoscode',
        'User-Agent': 'Mozilla/5.0 (Linux; Android; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36'
    })
    
    # Bot automation flow also requires the protection bypass cookie
    jar = requests.cookies.RequestsCookieJar()
    jar.set('__test', '889f999ca1bb6aca47b93a5181ffbc58', domain='todayfree.xo.je', path='/')
    session.cookies = jar

    try:
        login_payload = {"tech_id": str(tech_id).strip(), "password": str(password).strip()}
        login_res = session.post("https://todayfree.xo.je/api/login.php", data=login_payload, timeout=12)
        login_data = login_res.json()
        
        if login_data.get("success") is True or login_data.get("status") == "success":
            orders_res = session.get(f"https://todayfree.xo.je/api/get_orders.php?tech_id={tech_id}", timeout=12)
            orders_list = orders_res.json().get("orders", [])
            progress_orders = [o for o in orders_list if str(o.get("status", "")).lower() == "in progress"]
            
            if not progress_orders: return "no_orders", 0
            
            reached_successfully = 0
            for order in progress_orders:
                reach_payload = {"wo_id": order.get("id"), "customer": "Unknown Customer", "address": "N/A"}
                reach_res = session.post("https://todayfree.xo.je/api/mark_reached.php", data=reach_payload, timeout=10)
                if reach_res.status_code == 200: reached_successfully += 1
            
            if reached_successfully > 0: return "success", reached_successfully
            return "failed_reach", 0
        return "auth_failed", 0
    except Exception:
        return "server_error", 0

@bot.message_handler(commands=['start', 'help'])
def start_cmd(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_credits = get_user_credits(user_id)
    bot.send_message(chat_id, f"🚀 *Welcome To Rocker Xposed Bot* 👋\n💰 *Credits:* `{user_credits}`\n\n👉 *Details ID,Password Format Mein Send Karein:*", parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_incoming_messages(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    msg_text = message.text.strip()
    
    if "," in msg_text:
        status_msg = bot.send_message(chat_id, "⏳ *VIP Core Processing...*")
        try:
            tech_id, tech_password = msg_text.split(",", 1)
            result, count = start_automation_flow(tech_id.strip(), tech_password.strip())
            if result == "success":
                deduct_user_credits(user_id, count)
                bot.edit_message_text(f"✅ *Task Completed!*\n🔹 Total *{count}* Orders marked Reached.", chat_id, status_msg.message_id, parse_mode="Markdown")
            elif result == "no_orders":
                bot.edit_message_text("ℹ️ *Account mein koi 'In Progress' order nahi mila.*", chat_id, status_msg.message_id, parse_mode="Markdown")
            else:
                bot.edit_message_text("❌ *Verification Failed!*", chat_id, status_msg.message_id)
        except Exception:
            bot.edit_message_text("❌ *Format error!* Use `ID,Password`", chat_id, status_msg.message_id)

if __name__ == "__main__":
    init_db()
    Thread(target=run_server).start()
    while True:
        try:
            bot.remove_webhook()
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception:
            time.sleep(5)
