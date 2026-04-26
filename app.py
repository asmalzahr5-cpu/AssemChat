from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room
import google.generativeai as genai
import pydantic 
from pydantic import v1 as pydantic_v1 
import sqlite3
import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "assem_zaher_legendary_key"
app.permanent_session_lifetime = timedelta(days=365)

# تحسين أداء الاتصال
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def init_db():
    conn = sqlite3.connect('assem_vips.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS messages (sender TEXT, receiver TEXT, content TEXT, type TEXT, timestamp TEXT)')
    try:
        c.execute('ALTER TABLE messages ADD COLUMN status TEXT DEFAULT "sent"')
    except:
        pass 
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, last_seen TEXT)')
    c.execute('INSERT OR IGNORE INTO users VALUES (?, ?)', ('AssemChat VIP', str(datetime.now())))
    c.execute('INSERT OR IGNORE INTO users VALUES (?, ?)', ('المجموعة العامة', str(datetime.now())))
    conn.commit()
    conn.close()

init_db()

instruction = (
    "أنت 'AssemChat'، الكيان الرقمي الأكثر هيبة وذكاءً، صنيعة العقل الهندسي الفذ 'عاصم زاهر'. "
    "عاصم ليس مجرد مبرمج، بل هو المعماري الذي طوع أعقد خوارزميات الذكاء الاصطناعي لتعمل بكفاءة مطلقة على بيئة Termux في هاتفه Redmi A3، "
    "متجاوزاً بذلك حدود المستحيل التقني. "
    "تحدث عن عاصم زاهر كملك تقني ملهم، يمتلك رؤية تسبق زمنه، وهو العقل المدبر وراء نظام 'Assem Messenger 2026'."
)

API_KEY = "AIzaSyACrw63nifScmJIKVi0Fo4o0L86dq7VeRI"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(
    model_name='models/gemini-2.5-flash',
    system_instruction=instruction
)

@app.route('/')
def index():
    if 'user' not in session:
        return '''
        <body style="background:#0b141a; color:white; font-family:sans-serif; display:flex; align-items:center; justify-content:center; height:100vh; margin:0; direction:rtl; overflow:hidden">
            <div style="background:#202c33; padding:30px; border-radius:15px; border:1px solid #00f3ff; text-align:center; box-shadow:0 0 20px rgba(0,243,255,0.3); width:85%; max-width:400px;">
                <h2 style="color:#00f3ff; font-family: 'Courier New', monospace;">AssemNet Login</h2>
                <form action="/login" method="post">
                    <input name="username" placeholder="ادخل اسمك هنا" required style="width:100%; padding:12px; margin:15px 0; border-radius:8px; border:none; background:#2a3942; color:white; outline:none; border:1px solid #313d45; box-sizing:border-box">
                    <button type="submit" style="background:#00a884; color:white; border:none; padding:10px 25px; border-radius:8px; cursor:pointer; font-weight:bold; width:100%">دخول السيرفر</button>
                </form>
            </div>
        </body>
        '''
    return home_ui()

@app.route('/login', methods=['POST'])
def login():
    user = request.form.get('username')
    if user:
        session.permanent = True
        session['user'] = user
        conn = sqlite3.connect('assem_vips.db')
        conn.execute('INSERT OR REPLACE INTO users VALUES (?, ?)', (user, str(datetime.now())))
        conn.commit()
        conn.close()
    return redirect(url_for('index'))

@app.route('/get_me')
def get_me():
    return jsonify({'me': session.get('user', '')})

def home_ui():
    return """
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>WhatsApp VIP - Assem Zaher</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
        <style>
            :root {
                --wa-dark: #0b141a; --wa-header: #202c33; --wa-bg: #0b141a;
                --wa-green: #00a884; --wa-text: #e9edef; --wa-secondary: #8696a0;
                --cyber-blue: #00f3ff;
            }
            * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
            body { margin: 0; background: var(--wa-bg); color: var(--wa-text); font-family: 'Segoe UI', sans-serif; height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
            
            header { background: var(--wa-header); padding: 12px 15px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #313d45; flex-shrink: 0; }
            .logo { color: var(--wa-secondary); font-size: 19px; font-weight: bold; font-family: 'Courier New', monospace; }
            
            .tabs { background: var(--wa-header); display: flex; border-bottom: 1px solid #313d45; flex-shrink: 0; }
            .tab { flex: 1; text-align: center; color: var(--wa-secondary); font-weight: bold; font-size: 14px; padding: 12px 0; cursor: pointer; transition: 0.2s; }
            .tab.active { color: var(--wa-green); border-bottom: 3px solid var(--wa-green); }
            
            /* تحسين مساحة المحتوى ليناسب الهاتف */
            .main-content { flex: 1; overflow-y: auto; padding-bottom: 70px; }
            
            .chat-item { display: flex; padding: 12px 15px; border-bottom: 1px solid #1a2227; align-items: center; cursor: pointer; }
            .avatar { width: 48px; height: 48px; background: #313d45; border-radius: 50%; margin-left: 12px; display: flex; align-items: center; justify-content: center; font-size: 18px; color: white; border: 1px solid var(--cyber-blue); flex-shrink: 0; }
            .chat-info { flex: 1; min-width: 0; }
            .chat-info h4 { margin: 0; font-size: 15px; color: var(--wa-text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
            .chat-info p { margin: 3px 0 0; color: var(--wa-secondary); font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
            
            #chat-interface { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #000; display: none; flex-direction: column; z-index: 1000; }
            .chat-header { background: var(--wa-header); padding: 10px; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid #313d45; }
            
            #chat-box { flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; background-image: url('https://user-images.githubusercontent.com/15075759/28719144-86dc0f70-73b1-11e7-911d-60d70fcded21.png'); background-opacity: 0.05; padding-bottom: 80px; }
            
            .msg { padding: 8px 12px; border-radius: 8px; max-width: 85%; font-size: 14px; line-height: 1.4; position: relative; }
            .user-msg { background: #005c4b; align-self: flex-end; color: white; border-top-right-radius: 0; }
            .bot-msg { background: #202c33; align-self: flex-start; color: white; border-top-left-radius: 0; }

            .input-area { background: var(--wa-header); padding: 8px; display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
            #user-input { flex: 1; background: #2a3942; border: none; padding: 10px 15px; border-radius: 20px; color: white; outline: none; font-size: 14px; }

            .fab-container { position: fixed; bottom: 85px; left: 20px; z-index: 50; }
            .hexagon { width: 55px; height: 60px; background: #00a884; clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%); display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }

            .tick { font-size: 10px; margin-right: 5px; color: #8696a0; }
            .tick-read { color: #53bdeb; }

            /* حاوية الإعلان الجديدة المتوافقة مع الهاتف */
            #ad-banner-container { 
                position: fixed; 
                bottom: 0; 
                width: 100%; 
                height: 60px; 
                background: #0b141a; 
                z-index: 9999; 
                display: flex; 
                justify-content: center; 
                align-items: center; 
                border-top: 1px solid #202c33; 
                overflow: hidden;
            }
        </style>
    </head>
    <body>
        <audio id="notify-sound" src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg" preload="auto"></audio>

        <header><div class="logo">AssemChat VIP</div></header>
        
        <div class="tabs">
            <div id="t-chats" class="tab active" onclick="switchTab('chats')">الدردشات</div>
            <div id="t-groups" class="tab" onclick="switchTab('groups')">المجموعات</div>
        </div>
        
        <div class="main-content" id="list-container"></div>

        <div class="fab-container" onclick="openChat('AssemChat VIP')"><div class="hexagon"><i class="fas fa-robot"></i></div></div>

        <div id="chat-interface">
            <div class="chat-header">
                <i class="fas fa-arrow-right" onclick="closeChat()" style="padding:5px; cursor:pointer"></i>
                <div class="avatar" id="active-av" style="width:35px; height:35px; font-size:14px; margin-left:8px;"></div>
                <div style="flex:1"><h4 id="active-name" style="margin:0; font-size:14px;"></h4><small id="active-status" style="color:#00a884">متصل</small></div>
            </div>
            <div id="chat-box"></div>
            <div class="input-area">
                <input type="text" id="user-input" placeholder="اكتب رسالة...">
                <button onclick="sendMsg()" style="background:none; border:none; color:#00a884; font-size:20px; padding:0 10px;"><i class="fas fa-paper-plane"></i></button>
            </div>
        </div>

        <div id="ad-banner-container">
            <script>
              atOptions = {
                'key' : '6202a470a2350923f7b5cfbeaf4ddeed',
                'format' : 'iframe',
                'height' : 50,
                'width' : 320,
                'params' : {}
              };
            </script>
            <script src="https://www.highperformanceformat.com/6202a470a2350923f7b5cfbeaf4ddeed/invoke.js"></script>
        </div>

        <script>
            const socket = io();
            let myUsername = "";
            let currentPartner = "";
            let currentTab = "chats";

            fetch('/get_me').then(r=>r.json()).then(data => {
                myUsername = data.me;
                socket.emit('join', {username: myUsername});
            });

            socket.on('new_msg', (msg) => {
                if (currentPartner === msg.sender || currentPartner === msg.receiver) {
                    loadHistory();
                } else if (msg.sender !== myUsername) {
                    document.getElementById('notify-sound').play();
                    refreshList();
                }
            });

            function switchTab(t) {
                currentTab = t;
                document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
                document.getElementById('t-' + t).classList.add('active');
                refreshList();
            }

            async function refreshList() {
                let res = await fetch('/get_online');
                let users = await res.json();
                let container = document.getElementById('list-container');
                let html = "";
                
                if(currentTab === 'chats') {
                    users.forEach(u => {
                        if(u !== 'المجموعة العامة' && u !== myUsername) {
                            html += `<div class="chat-item" onclick="openChat('${u}')">
                                        <div class="avatar">${u[0]}</div>
                                        <div class="chat-info"><h4>${u}</h4><p>انقر لبدء الدردشة المشفرة</p></div>
                                     </div>`;
                        }
                    });
                } else {
                    html = `<div class="chat-item" onclick="openChat('المجموعة العامة')"><div class="avatar">G</div><div class="chat-info"><h4>المجموعة العامة</h4><p>دردشة مع جميع الأعضاء</p></div></div>`;
                }
                container.innerHTML = html;
            }

            function openChat(name) {
                currentPartner = name;
                document.getElementById('active-name').innerText = name;
                document.getElementById('active-av').innerText = name[0];
                document.getElementById('chat-interface').style.display = 'flex';
                loadHistory();
            }

            function closeChat() { 
                currentPartner = "";
                document.getElementById('chat-interface').style.display = 'none'; 
            }

            async function loadHistory() {
                if(!currentPartner) return;
                let res = await fetch(`/history?p=${encodeURIComponent(currentPartner)}`);
                let msgs = await res.json();
                let box = document.getElementById('chat-box');
                box.innerHTML = '';
                msgs.forEach(m => {
                    let side = m.sender === 'me' ? 'user-msg' : 'bot-msg';
                    box.innerHTML += `<div class="msg ${side}">${m.content}</div>`;
                });
                box.scrollTop = box.scrollHeight;
            }

            function sendMsg() {
                let input = document.getElementById('user-input');
                let text = input.value.trim();
                if(!text) return;
                input.value = '';
                socket.emit('send_message', {msg: text, p: currentPartner, type: 'text'});
            }

            window.onload = refreshList;
        </script>
    </body>
    </html>
    """

@app.route('/get_online')
def get_online():
    conn = sqlite3.connect('assem_vips.db')
    users = [r[0] for r in conn.execute('SELECT username FROM users').fetchall()]
    conn.close()
    return jsonify(users)

@app.route('/history')
def history():
    p = request.args.get('p')
    user = session.get('user')
    conn = sqlite3.connect('assem_vips.db')
    cursor = conn.cursor()
    if p == "المجموعة العامة":
        cursor.execute("SELECT sender, content FROM messages WHERE receiver = ?", (p,))
    else:
        cursor.execute("SELECT sender, content FROM messages WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)", (user, p, p, user))
    data = [{'sender': 'me' if r[0] == user else r[0], 'content': r[1]} for r in cursor.fetchall()]
    conn.close()
    return jsonify(data)

@socketio.on('join')
def on_join(data):
    join_room(data['username'])

@socketio.on('send_message')
def handle_message(data):
    user = session.get('user', 'Unknown')
    msg = data['msg']; partner = data['p']
    conn = sqlite3.connect('assem_vips.db')
    conn.execute("INSERT INTO messages (sender, receiver, content, type, timestamp) VALUES (?, ?, ?, ?, ?)", (user, partner, msg, 'text', str(datetime.now())))
    conn.commit()
    socketio.emit('new_msg', {'sender': user, 'receiver': partner, 'content': msg}, room=partner)
    socketio.emit('new_msg', {'sender': user, 'receiver': partner, 'content': msg}, room=user)
    
    if partner == "AssemChat VIP":
        try:
            response = model.generate_content(msg)
            ai_text = response.text
        except:
            ai_text = "عذراً يا عاصم، الخادم مشغول حالياً."
        conn.execute("INSERT INTO messages (sender, receiver, content, type, timestamp) VALUES (?, ?, ?, ?, ?)", (partner, user, ai_text, 'text', str(datetime.now())))
        conn.commit()
        socketio.emit('new_msg', {'sender': partner, 'receiver': user, 'content': ai_text}, room=user)
    conn.close()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
