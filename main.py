import telebot
import requests
import re
import time
from datetime import datetime
from threading import Thread
from flask import Flask

# ====================================================================
# 👑 ROCKER XPOSED SYSTEM CONFIGURATION
# ====================================================================
BOT_TOKEN = "8497914783:AAH-EbriHxs3tvU-AnI70fxDyreblYgei-E"
FIREBASE_URL = "https://rocker-xposed-bot-default-rtdb.firebaseio.com/"

SUPER_ADMIN_ID = 8347566603   # 👑 Naresh Bhai
CO_ADMIN_IDS = [6631326358]   # 👥 Co-Admin ID
ALLOWED_ADMINS = [SUPER_ADMIN_ID] + CO_ADMIN_IDS

# JIO SERVER PORTAL ENDPOINTS
JIO_LOGIN_URL = 'https://jpw.jio.com/api/login/SAML/UserLogin'
JIO_WO_URL    = 'https://jpw.jio.com/lco/api/workorder-inquiry/WorkOrder/GetWorkOrderList'
JIO_UPD_URL   = 'https://jpw.jio.com/lco/api/workorder-maintenance/WorkOrder/UpdateWorkOrder'
# ====================================================================

app = Flask('')
@app.route('/')
def home(): 
    return "Rocker Xposed Engine is Online!"
def run_webserver(): 
    app.run(host='0.0.0.0', port=8080)

bot = telebot.TeleBot(BOT_TOKEN)
user_sessions = {}

def validate_license_key(key, chat_id):
    if chat_id in ALLOWED_ADMINS: return {"status": True, "type": "Admin (Unlimited)"}
    try:
        response = requests.get(f"{FIREBASE_URL}/keys/{key}.json", timeout=5)
        data = response.json()
        if not data or data.get("status") != "active": return {"status": False, "msg": "❌ Key Suspended/Invalid!"}
        if datetime.now().strftime("%Y-%m-%d") > data.get("expiry_date", ""): return {"status": False, "msg": "❌ Key Expired!"}
        return {"status": True, "type": "Customer", "current_credits": data.get("credits", 0)}
    except: return {"status": False, "msg": "⚠️ Database Sync Error."}

# --------------------------------------------------------------------
# ⚡ CORE JIO PORTAL PIPELINE (PARALLEL EXECUTION & VALIDATION)
# --------------------------------------------------------------------
def parse_credentials(raw):
    t = re.sub(r'^[^a-zA-Z0-9]*(?:id|user|tech|login)\s*[:=]?\s*', '', raw, flags=re.IGNORECASE)
    t = re.sub(r'(?:password|pwd|pass)\s*[:=]?\s*', ' ', t, flags=re.IGNORECASE)
    parts = re.split(r'[\s,:|\/\n\r\t;]+', t)
    parts = [p for p in parts if p.strip()]
    return (parts[0], parts[1]) if len(parts) >= 2 else (None, None)

def process_jio_auto_reach(raw_creds, chat_id, main_msg_id):
    tech_id, password = parse_credentials(raw_creds)
    if not tech_id or not password:
        return {"ok": False, "error": "Invalid format! Use: TechID Password"}

    session = requests.Session()
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/plain, */*',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 11) JioWO/2.0.7',
        'X-Requested-With': 'com.jio.workorder',
        'Origin': 'https://jpw.jio.com',
        'Referer': 'https://jpw.jio.com/'
    }
    session.headers.update(headers)

    # Stage 1: Authentication
    try:
        login_payload = {
            'UserName': tech_id, 'Password': password, 'Handset': 'android',
            'FCMID': 'jio_wo_web', 'DeviceId': 'jio_wo_web_device', 'AppVersion': '2.0.7'
        }
        res = session.post(JIO_LOGIN_URL, json=login_payload, timeout=15).json()
        if not res.get('IsSuccessful', False):
            user_msg = res.get('ErrorInfo', {}).get('UserMessage', 'Invalid Tech ID or Password.')
            return {"ok": False, "error": user_msg}
    except:
        return {"ok": False, "error": "Jio Server Login Gateway Timeout!"}

    # Stage 2: Fetch Work Orders
    try:
        try: bot.edit_message_text("🚀 **ROCKER XPOSED ENGINE**\n━━━━━━━━━━━━━━━━━━━━━━━━\n📥 *Status: Fetching assigned work orders list...*", chat_id, main_msg_id, parse_mode="Markdown")
        except: pass
        
        wo_payload = {
            'TechnicianID': tech_id, 'IsHSOUser': False, 'WorkOrderStatus': [''],
            'PageSize': 100, 'offsetValue': 0, 'TechnicianDesignationType': 'Technician'
        }
        wo_res = session.post(JIO_WO_URL, json=wo_payload, timeout=15).json()
        if not wo_res.get('IsSuccessful', False):
            return {"ok": False, "error": "Failed to extract work order registry."}
    except:
        return {"ok": False, "error": "Jio Inquiry System Timeout!"}

    orders = wo_res.get('lstWorkOrders', [])
    in_progress = [o for o in orders if o.get('StatusDesc', '').lower().strip() == 'in progress']

    if not in_progress:
        return {"ok": True, "tech_id": tech_id, "total": len(orders), "in_progress": 0, "reached": 0, "failed": 0}

    # Stage 3: Parallel Status Maintenance & Reach Execution
    try: bot.edit_message_text(f"🚀 **ROCKER XPOSED ENGINE**\n━━━━━━━━━━━━━━━━━━━━━━━━\n⚡ *Status: Reaching {len(in_progress)} In-Progress work orders parallelly...*", chat_id, main_msg_id, parse_mode="Markdown")
    except: pass

    fallback_lat, fallback_lon = '28.6139', '77.2090'
    for o in orders:
        addr = o.get('CustomerDetails', {}).get('Address', {})
        if addr.get('Latitude') and addr.get('Longitude'):
            fallback_lat, fallback_lon = str(addr['Latitude']), str(addr['Longitude'])
            break

    reached_count = 0
    failed_count = 0

    for o in in_progress:
        addr = o.get('CustomerDetails', {}).get('Address', {})
        lat = str(addr.get('Latitude') or fallback_lat)
        lon = str(addr.get('Longitude') or fallback_lon)

        upd_payload = {
            'ActionCode': 'ZA26', 'StatusCode': 'CL09', 'BuildingID': addr.get('BuildingID', ''),
            'TechnicianLatitude': lat, 'TechnicianLongitude': lon, 'UpdatedBy': tech_id,
            'WorkOrderID': o.get('WorkOrderID', ''), 'WorkOrderSubType': o.get('WorkOrderSubType', ''),
            'WorkOrderType': o.get('WorkOrderType', '')
        }
        try:
            upd_res = session.post(JIO_UPD_URL, json=upd_payload, timeout=10).json()
            if upd_res.get('IsSuccessful', False): 
                reached_count += 1
            else: 
                failed_count += 1
        except:
            failed_count += 1

    return {
        "ok": True, "tech_id": tech_id, "total": len(orders),
        "in_progress": len(in_progress), "reached": reached_count, "failed": failed_count
    }

# --------------------------------------------------------------------
# 🤖 BOT MULTI-STAGE LIVE CONTROL INTERFACE
# --------------------------------------------------------------------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_sessions[chat_id] = {"step": "GET_KEY", "main_msg_id": None}
    welcome_text = (
        "⚡ **WELCOME TO ROCKER XPOSED** ⚡\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔑 Please enter your **VIP Subscription Key** to unlock:"
    )
    sent_msg = bot.send_message(chat_id, welcome_text, parse_mode="Markdown")
    user_sessions[chat_id]["main_msg_id"] = sent_msg.message_id

@bot.message_handler(func=lambda message: True)
def handle_user_inputs(message):
    chat_id = message.chat.id
    user_text = message.text.strip()
    
    if chat_id not in user_sessions:
        send_welcome(message)
        return
        
    session = user_sessions[chat_id]
    step = session.get("step")
    main_msg_id = session.get("main_msg_id")

    # LICENSE VERIFICATION
    if step == "GET_KEY":
        val = validate_license_key(user_text, chat_id)
        if not val["status"]:
            try: bot.edit_message_text(f"{val['msg']}\n\n🔑 Please re-enter a valid key:", chat_id, main_msg_id, parse_mode="Markdown")
            except: pass
            return
            
        user_sessions[chat_id]["key"] = user_text
        user_sessions[chat_id]["step"] = "GET_CREDS"
        try:
            bot.edit_message_text(
                "✅ **Access Granted! Rocker Xposed Activated.**\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "📝 Please enter Technician ID and Password:\n"
                "Format: `TechID Password`", chat_id, main_msg_id, parse_mode="Markdown"
            )
        except: pass
        return

    # REAL LIVE TRANSACTION EXECUTION LOOP
    elif step == "GET_CREDS":
        user_key = session.get("key")
        try: bot.delete_message(chat_id, message.message_id)
        except: pass

        # Stage 1 Interface: Initializing
        try: bot.edit_message_text("🚀 **ROCKER XPOSED ENGINE**\n━━━━━━━━━━━━━━━━━━━━━━━━\n🔒 *Status: Logging in to Jio Server securely...*", chat_id, main_msg_id, parse_mode="Markdown")
        except: pass
        
        t0 = time.time()
        portal_data = process_jio_auto_reach(user_text, chat_id, main_msg_id)
        took_ms = int((time.time() - t0) * 1000)

        # Handle Failed Logins
        if not portal_data.get("ok", False):
            error_reason = portal_data.get("error", "Authentication Failure.")
            try:
                bot.edit_message_text(
                    f"❌ **OPERATION FAILED**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"⚠️ **Reason:** `{error_reason}`\n\n"
                    f"📝 Please enter correct **Tech ID and Password**:", 
                    chat_id, main_msg_id, parse_mode="Markdown"
                )
            except: pass
            return

        # Fetch actual server parameters
        tech_id = portal_data.get("tech_id")
        total = portal_data.get("total", 0)
        in_progress = portal_data.get("in_progress", 0)
        reached = portal_data.get("reached_count", 0)
        failed = portal_data.get("failed_count", 0)

        # Balance update tracking
        val = validate_license_key(user_key, chat_id)
        if val["type"] == "Customer":
            remaining_balance = val.get("current_credits", 0) - reached
            try: requests.put(f"{FIREBASE_URL}/keys/{user_key}/credits.json", json=remaining_balance, timeout=5)
            except: pass
        else:
            remaining_balance = "Unlimited (Admin Pack)"

        # Print final actual reports card
        report_text = (
            f"🎯 **ROCKER XPOSED REPORT** 🎯\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **Tech ID:** `{tech_id}`\n"
            f"📦 **Total Orders Assigned:** {total}\n"
            f"⏳ **In-Progress Found:** {in_progress}\n"
            f"✅ **Successfully Reached:** {reached}\n"
            f"❌ **Failed/Skipped:** {failed}\n"
            f"🔑 **Remaining Balance:** {remaining_balance}\n"
            f"⏱️ **Response Time:** {took_ms} ms\n\n"
            f"🔒 *Status: Session completed successfully.*"
        )
        try: bot.edit_message_text(report_text, chat_id, main_msg_id, parse_mode="Markdown")
        except: pass
        
        # Log update to Admin Channel
        admin_log = f"🚨 **LIVE TRANSACTION ALERT**\n👤 User: `{chat_id}`\n👤 Tech ID: `{tech_id}`\n📦 In-Progress: {in_progress} -> Reached: {reached}"
        for admin_id in ALLOWED_ADMINS:
            try: bot.send_message(admin_id, admin_log, parse_mode="Markdown")
            except: pass

        # 🔥 AUTOMATIC LOGOUT ENGINE: Wait 5 seconds and wipe session back to lock screen
        time.sleep(5)
        try:
            bot.delete_message(chat_id, main_msg_id)
        except:
            pass
            
        logout_msg = bot.send_message(
            chat_id,
            "🚪 **AUTOMATIC LOGOUT COMPLETE**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔒 Your session has been closed securely.\n"
            "🔄 Press /start to log in again.",
            parse_mode="Markdown"
        )
        user_sessions.pop(chat_id, None)

if __name__ == '__main__':
    Thread(target=run_webserver).start()
    while True:
        try: bot.infinity_polling(timeout=20, long_polling_timeout=10, skip_pending=True)
        except: time.sleep(5)
