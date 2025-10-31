from flask import Flask, request
import requests
import time

app = Flask(__name__)

TOKEN = "8477934891:AAE7D1WUEWWHmK8IsmNhN1hjDJgH4gAf2EA"
CHAT_ID = "6179725591"
BLOCKED = {}

def send(msg):
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={msg}")
    except:
        pass

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        update = request.get_json()
        if 'message' in update:
            msg = update['message']
            if str(msg['chat']['id']) == CHAT_ID:
                text = msg.get('text', '').strip()
                parts = text.split()

                if parts[0] == '/add' and len(parts) >= 2:
                    id = parts[1]
                    custom = ' '.join(parts[2:]) if len(parts) > 2 else "Banned"
                    BLOCKED[id] = {'perm': True, 'msg': custom}
                    send(f"Banned: {id}\nMsg: {custom}")

                elif parts[0] == '/tempban' and len(parts) >= 3:
                    id, mins = parts[1], parts[2]
                    custom = ' '.join(parts[3:]) if len(parts) > 3 else "Temp ban"
                    expire = time.time() + (int(mins) * 60)
                    BLOCKED[id] = {'perm': False, 'msg': custom, 'expire': expire}
                    send(f"Temp Banned: {id} for {mins}m")

                elif parts[0] == '/remove' and len(parts) >= 2:
                    BLOCKED.pop(parts[1], None)
                    send(f"Unbanned: {parts[1]}")

                elif text == '/list':
                    if not BLOCKED:
                        send("No one blocked.")
                    else:
                        res = "BLOCKED:\n"
                        for i, (id, data) in enumerate(BLOCKED.items(), 1):
                            if data['perm'] or time.time() < data['expire']:
                                t = "[PERM]" if data['perm'] else f"[{int((data['expire'] - time.time())/60)}m]"
                                res += f"{i}. {id} {t}\n   ↳ {data['msg']}\n"
                        send(res)

                elif text == '/clear':
                    BLOCKED.clear()
                    send("All cleared!")

    return "OK", 200

@app.route('/check/<user_id>')
def check(user_id):
    data = BLOCKED.get(user_id, {})
    if data.get('perm') or (not data.get('perm') and time.time() < data.get('expire', 0)):
        return "true"
    return "false"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
