from flask import Flask, request
import requests
import time

app = Flask(__name__)

TOKEN = "8477934891:AAE7D1WUEWWHmK8IsmNhN1hjDJgH4gAf2EA"
CHAT_ID = "6179725591"
BLOCKED = {}
WAITING = {}  # {chat_id: {'action': 'add'/'tempban', 'user_id': '123', 'step': 1}}

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, data={'chat_id': CHAT_ID, 'text': msg}, timeout=10)
    except:
        pass

def get_user_info(user_id):
    try:
        url = f"https://api.roblox.com/users/{user_id}"
        data = requests.get(url).json()
        username = data.get("Username", "Unknown")
        display = data.get("DisplayName", username)
        return username, display
    except:
        return "Unknown", "Unknown"

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        try:
            update = request.get_json()
            if 'message' in update:
                msg = update['message']
                chat_id = str(msg['chat']['id'])
                text = msg.get('text', '').strip()

                if chat_id != CHAT_ID:
                    return "OK", 200

                # Waiting for reason
                if chat_id in WAITING:
                    action = WAITING[chat_id]['action']
                    user_id = WAITING[chat_id]['user_id']
                    username, display = get_user_info(user_id)

                    if action == 'add':
                        BLOCKED[user_id] = {'perm': True, 'msg': text}
                        send(f"✅ PERM BANNED\n"
                             f"👤 Name: {display} (@{username})\n"
                             f"🆔 ID: {user_id}\n"
                             f"📝 Reason: {text}")
                    elif action == 'tempban':
                        mins = WAITING[chat_id].get('mins', 5)
                        expire = time.time() + (mins * 60)
                        BLOCKED[user_id] = {'perm': False, 'msg': text, 'expire': expire}
                        send(f"⏰ TEMP BANNED ({mins}m)\n"
                             f"👤 Name: {display} (@{username})\n"
                             f"🆔 ID: {user_id}\n"
                             f"📝 Reason: {text}")

                    del WAITING[chat_id]
                    return "OK", 200

                # Commands
                parts = text.split()
                cmd = parts[0]

                if cmd == '/add' and len(parts) >= 2:
                    user_id = parts[1]
                    username, display = get_user_info(user_id)
                    WAITING[chat_id] = {'action': 'add', 'user_id': user_id}
                    send(f"🔨 PERM BAN\n"
                         f"👤 Name: {display} (@{username})\n"
                         f"🆔 ID: {user_id}\n\n"
                         f"📝 Type your kick reason:")
                    return "OK", 200

                elif cmd == '/tempban' and len(parts) >= 3:
                    user_id, mins = parts[1], parts[2]
                    username, display = get_user_info(user_id)
                    WAITING[chat_id] = {'action': 'tempban', 'user_id': user_id, 'mins': int(mins)}
                    send(f"⏰ TEMP BAN ({mins}m)\n"
                         f"👤 Name: {display} (@{username})\n"
                         f"🆔 ID: {user_id}\n\n"
                         f"📝 Type your kick reason:")
                    return "OK", 200

                elif cmd == '/remove' and len(parts) >= 2:
                    user_id = parts[1]
                    username, display = get_user_info(user_id)
                    BLOCKED.pop(user_id, None)
                    send(f"✅ UNBANNED\n"
                         f"👤 Name: {display} (@{username})\n"
                         f"🆔 ID: {user_id}")
                    return "OK", 200

                elif cmd == '/list':
                    if not BLOCKED:
                        send("📭 No one blocked.")
                    else:
                        res = "🚫 BLOCKED LIST:\n\n"
                        for i, (uid, data) in enumerate(BLOCKED.items(), 1):
                            username, display = get_user_info(uid)
                            if data['perm'] or time.time() < data['expire']:
                                t = "PERM" if data['perm'] else f"{int((data['expire'] - time.time())/60)}m"
                                res += f"{i}. {display} (@{username})\n   🆔 {uid} [{t}]\n   📝 {data['msg']}\n\n"
                        send(res)
                    return "OK", 200

                elif cmd == '/clear':
                    BLOCKED.clear()
                    send("🗑️ All cleared!")
                    return "OK", 200

        except Exception as e:
            send(f"Error: {e}")
    return "OK", 200

@app.route('/check/<user_id>')
def check(user_id):
    data = BLOCKED.get(user_id, {})
    if data.get('perm') or (not data.get('perm') and time.time() < data.get('expire', 0)):
        return "true"
    return "false"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
