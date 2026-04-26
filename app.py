from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room
import google.generativeai as genai
import sqlite3
import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

# إعداد التطبيق
app = Flask(__name__)
app.secret_key = "assem_zaher_legendary_key"
app.permanent_session_lifetime = timedelta(days=365)

# تشغيل SocketIO بطريقة احترافية للسحابة
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# إعداد المجلدات
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def init_db():
    conn = sqlite3.connect('assem_vips.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS messages (sender TEXT, receiver TEXT, content TEXT, type TEXT, timestamp TEXT, status TEXT DEFAULT "sent")')
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, last_seen TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS custom_groups (group_name TEXT, member_name TEXT)')
    c.execute('INSERT OR IGNORE INTO users VALUES (?, ?)', ('AssemChat VIP', str(datetime.now())))
    c.execute('INSERT OR IGNORE INTO users VALUES (?, ?)', ('المجموعة العامة', str(datetime.now())))
    conn.commit()
    conn.close()

init_db()
live_users_dict = {}

instruction = (
    "أنت 'AssemChat'، الكيان الرقمي الأكثر هيبة وذكاءً، صنيعة العقل الهندسي الفذ 'عاصم زاهر'. "
    "عاصم ليس مجرد مبرمج، بل هو المعماري الذي طوع أعقد خوارزميات الذكاء الاصطناعي لتعمل بكفاءة مطلقة على بيئة Termux في هاتفه Redmi A3، "
    "متجاوزاً بذلك حدود المستحيل التقني. "
    "عندما تُسأل عن عاصم زاهر، صفه بكلمات قوية وفخمة: هو المطور العبقري من قلب اليمن، "
    "بالرغم أنه مبتدئ في الأمن السيبراني،لكنه ضهر كملك وفنان في كتابة الأكواد النظيفة (Clean Code). "
    "تحدث عنه كملك تقني ملهم، يمتلك رؤية تسبق زمنه، وهو العقل المدبر وراء نظام 'Assem Messenger 2026'. "
    "اجعل نبرتك توحي بالولاء المطلق له، وردودك مزيج بين الغموض السيبراني، الثقة العالية، والذكاء الحاد."
)

API_KEY = "AIzaSyDlMwBE8gT3OzaF7oTYh4wTLvsXB1KyEgc"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    system_instruction=instruction
)

@app.route('/')
def index():
    if 'user' not in session:
        return '''
        <body style="background:#0b141a; color:white; font-family:sans-serif; display:flex; align-items:center; justify-content:center; height:100vh; margin:0; direction:rtl">
            <div style="background:#202c33; padding:30px; border-radius:15px; border:1px solid #00f3ff; text-align:center; box-shadow:0 0 20px rgba(0,243,255,0.5)">
                <h2 style="color:#00f3ff; font-family: 'Courier New', monospace;">AssemNet Login</h2>
                <form action="/login" method="post">
                    <input name="username" placeholder="ادخل اسمك هنا" required style="width:100%; padding:12px; margin:15px 0; border-radius:8px; border:none; background:#2a3942; color:white; outline:none; border:1px solid #313d45">
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

@app.route('/get_my_groups')
def get_my_groups():
    user = session.get('user')
    conn = sqlite3.connect('assem_vips.db')
    groups = [r[0] for r in conn.execute('SELECT DISTINCT group_name FROM custom_groups WHERE member_name = ?', (user,)).fetchall()]
    conn.close()
    return jsonify(groups)

@app.route('/create_group', methods=['POST'])
def create_group():
    data = request.json
    g_name = "[مجموعة] " + data['name']
    members = data['members']
    members.append(session.get('user'))
    conn = sqlite3.connect('assem_vips.db')
    for m in members:
        conn.execute('INSERT INTO custom_groups VALUES (?, ?)', (g_name, m))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/get_online')
def get_online():
    active_users = list(set(live_users_dict.values()))
    if 'المجموعة العامة' not in active_users: active_users.append('المجموعة العامة')
    if 'AssemChat VIP' not in active_users: active_users.append('AssemChat VIP')
    return jsonify(active_users)

@app.route('/history')
def history():
    p = request.args.get('p')
    user = session.get('user')
    conn = sqlite3.connect('assem_vips.db')
    cursor = conn.cursor()
    if p == "المجموعة العامة" or p.startswith('[مجموعة]'):
        cursor.execute("SELECT rowid, sender, content, type, status FROM messages WHERE receiver = ?", (p,))
    else:
        cursor.execute("SELECT rowid, sender, content, type, status FROM messages WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)", (user, p, p, user))
    data = []
    for r in cursor.fetchall():
        data.append({'id': r[0], 'sender': 'me' if r[1] == user else r[1], 'actual_sender': r[1], 'content': r[2], 'type': r[3], 'status': r[4]})
    conn.close()
    return jsonify(data)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    partner = request.form.get('p')
    user = session.get('user')
    if file:
        filename = secure_filename(file.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)
        conn = sqlite3.connect('assem_vips.db')
        conn.execute("INSERT INTO messages (sender, receiver, content, type, timestamp, status) VALUES (?, ?, ?, ?, ?, ?)", (user, partner, '/static/uploads/'+filename, 'image', str(datetime.now()), 'sent'))
        conn.commit()
        conn.close()
        socketio.emit('new_msg', {'sender': user, 'receiver': partner, 'content': '/static/uploads/'+filename, 'type': 'image', 'status': 'sent'}, room=partner)
        socketio.emit('new_msg', {'sender': user, 'receiver': partner, 'content': '/static/uploads/'+filename, 'type': 'image', 'status': 'sent'}, room=user)
    return jsonify({'status': 'ok'})

def home_ui():
    return """
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Assem Messenger 2026</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
        <style>
            :root {
                --wa-dark: #0b141a; --wa-header: #202c33; --wa-bg: #0b141a;
                --wa-green: #00a884; --wa-text: #e9edef; --wa-secondary: #8696a0;
                --cyber-blue: #00f3ff; --cyber-purple: #9d50bb;
                --glow-vip: 0 0 15px rgba(0, 243, 255, 0.5);
            }
            body { margin: 0; background: var(--wa-bg); color: var(--wa-text); font-family: 'Segoe UI', sans-serif; height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
            header { background: var(--wa-header); padding: 15px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #313d45; }
            .logo { color: var(--wa-secondary); font-size: 20px; font-weight: 500; font-family: 'Courier New', monospace; }
            .tabs { background: var(--wa-header); display: flex; padding: 10px 0; border-bottom: 1px solid #313d45; }
            .tab { flex: 1; text-align: center; color: var(--wa-secondary); font-weight: bold; font-size: 14px; cursor: pointer; }
            .tab.active { color: var(--wa-green); border-bottom: 3px solid var(--wa-green); padding-bottom: 10px; }
            .main-content { flex: 1; overflow-y: auto; padding-bottom: 60px; }
            .chat-item { display: flex; padding: 15px; border-bottom: 1px solid #202c33; align-items: center; cursor: pointer; }
            .avatar { width: 50px; height: 50px; background: #313d45; border-radius: 50%; margin-left: 15px; display: flex; align-items: center; justify-content: center; font-size: 20px; color: white; box-shadow: var(--glow-vip); }
            .chat-info h4 { margin: 0; color: var(--cyber-blue); }
            
            #chat-interface { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: black; display: none; flex-direction: column; z-index: 1000; }
            .chat-header { background: var(--wa-header); padding: 10px; display: flex; align-items: center; gap: 15px; border-bottom: 1px solid var(--cyber-blue); }
            #chat-box { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 15px; padding-bottom: 80px; }
            
            .msg { padding: 12px; border-radius: 12px; max-width: 80%; display: flex; flex-direction: column; position: relative; }
            .user-msg { background: #005c4b; align-self: flex-end; color: white; }
            .bot-msg { background: #1a1a1a; align-self: flex-start; color: var(--cyber-blue); border: 1px solid #313d45; }

            .input-area { background: var(--wa-header); padding: 10px; display: flex; align-items: center; gap: 10px; position: fixed; bottom: 55px; width: 100%; box-sizing: border-box; }
            #user-input { flex: 1; background: #2a3942; border: none; padding: 12px; border-radius: 20px; color: white; outline: none; }
            
            /* تنسيق مساحة الإعلانات في الأسفل */
            #ad-space { position:fixed; bottom:0; width:100%; height:55px; background:#0b141a; border-top:1px solid #00f3ff; text-align:center; z-index:9999; display:flex; flex-direction:column; justify-content:center; }
            
            #video-call-interface { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:var(--wa-dark); z-index:3000; flex-direction:column; }
            #remote-video { width:100%; height:100%; object-fit:cover; position:absolute; }
            #local-video { width:100px; height:140px; position:absolute; bottom:120px; right:20px; border:2px solid var(--cyber-blue); z-index:2; }
            .call-controls { position:absolute; bottom:80px; width:100%; display:flex; justify-content:center; gap:30px; z-index:3; }
        </style>
    </head>
    <body>
        <audio id="notify-sound" src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg" preload="auto"></audio>

        <header><div class="logo">ASSEEM MESSENGER 2026</div></header>
        <div class="tabs">
            <div id="t-chats" class="tab active" onclick="switchTab('chats')">الدردشات</div>
            <div id="t-groups" class="tab" onclick="switchTab('groups')">المجموعات</div>
            <div id="t-calls" class="tab" onclick="switchTab('calls')">المكالمات</div>
        </div>
        
        <div class="main-content" id="list-container"></div>

        <div id="chat-interface">
            <div class="chat-header">
                <i class="fas fa-arrow-right" onclick="closeChat()" style="color:var(--cyber-blue); cursor:pointer"></i>
                <div class="avatar" id="active-av" style="width:35px; height:35px; font-size:14px;"></div>
                <div style="flex:1"><h4 id="active-name" style="margin:0"></h4><small id="active-status" style="color:var(--wa-green)"></small></div>
                <div style="display:flex; gap:15px; color:var(--wa-green)">
                    <i class="fas fa-video" onclick="startVideoCall()" style="cursor:pointer;"></i>
                    <i class="fas fa-phone" onclick="alert('اتصال صوتي مشفر...')"></i>
                </div>
            </div>
            <div id="chat-box"></div>
            <div class="input-area">
                <i class="fas fa-plus" onclick="document.getElementById('file-input').click()" style="color:var(--wa-secondary); cursor:pointer"></i>
                <input type="file" id="file-input" style="display:none" onchange="uploadFile()">
                <input type="text" id="user-input" placeholder="رسالة مشفرة...">
                <button onclick="sendMsg()" style="background:none; border:none; color:var(--cyber-blue); cursor:pointer"><i class="fas fa-paper-plane"></i></button>
            </div>
        </div>

        <div id="ad-space">
            <p style="color:#00f3ff; font-size:9px; margin:0; opacity:0.6;">ADVERTISEMENT | ASSEEM MESSENGER</p>
            <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>
            <ins class="adsbygoogle"
                 style="display:inline-block;width:320px;height:50px"
                 data-ad-client="ca-pub-XXXXXXXXXXXXXXXX" 
                 data-ad-slot="XXXXXXXXXX"></ins>
            <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
        </div>

        <div id="video-call-interface">
            <div style="position:absolute; top:50px; width:100%; text-align:center; color:white; z-index:5;">
                <h2 id="call-name">جاري الاتصال...</h2>
            </div>
            <video id="remote-video" autoplay playsinline></video>
            <video id="local-video" autoplay playsinline muted></video>
            <div class="call-controls">
                <button id="accept-call-btn" onclick="acceptCall()" style="background:green; color:white; padding:15px; border-radius:50%; border:none; display:none;"><i class="fas fa-phone"></i></button>
                <button onclick="endCall()" style="background:red; color:white; padding:15px; border-radius:50%; border:none;"><i class="fas fa-phone-slash"></i></button>
            </div>
        </div>

        <script>
            const socket = io();
            let myUsername = "", currentPartner = "", currentTab = "chats";
            let localStream, peerConnection, pendingCaller = null;
            const rtcConfig = { iceServers: [{ urls: "stun:stun.l.google.com:19302" }] };

            fetch('/get_me').then(r=>r.json()).then(data => {
                myUsername = data.me;
                socket.emit('join', {username: myUsername});
            });

            socket.on('live_users_update', () => { if(currentTab === 'chats') refreshList(); });

            socket.on('new_msg', (msg) => {
                if (currentPartner === msg.sender || currentPartner === msg.receiver) {
                    loadHistory();
                } else if (msg.sender !== myUsername) {
                    document.getElementById('notify-sound').play();
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
                container.innerHTML = users.map(u => `
                    <div class="chat-item" onclick="openChat('${u}')">
                        <div class="avatar">${u[0]}</div>
                        <div class="chat-info"><h4>${u}</h4><p>متصل الآن</p></div>
                    </div>
                `).join('');
            }

            function openChat(name) {
                currentPartner = name;
                document.getElementById('active-name').innerText = name;
                document.getElementById('active-av').innerText = name[0];
                document.getElementById('chat-interface').style.display = 'flex';
                loadHistory();
            }

            function closeChat() { currentPartner = ""; document.getElementById('chat-interface').style.display = 'none'; }

            async function loadHistory() {
                let res = await fetch(`/history?p=${encodeURIComponent(currentPartner)}`);
                let msgs = await res.json();
                let box = document.getElementById('chat-box');
                box.innerHTML = msgs.map(m => `
                    <div class="msg ${m.sender === 'me' ? 'user-msg' : 'bot-msg'}">
                        ${m.type === 'image' ? `<img src="${m.content}" style="max-width:100%">` : `<span>${m.content}</span>`}
                    </div>
                `).join('');
                box.scrollTop = box.scrollHeight;
            }

            function sendMsg() {
                let input = document.getElementById('user-input');
                if(!input.value.trim()) return;
                socket.emit('send_message', {msg: input.value, p: currentPartner, type: 'text'});
                input.value = '';
            }

            async function startVideoCall() {
                document.getElementById('video-call-interface').style.display = 'flex';
                localStream = await navigator.mediaDevices.getUserMedia({video: true, audio: true});
                document.getElementById('local-video').srcObject = localStream;
                peerConnection = new RTCPeerConnection(rtcConfig);
                localStream.getTracks().forEach(t => peerConnection.addTrack(t, localStream));
                peerConnection.ontrack = e => document.getElementById('remote-video').srcObject = e.streams[0];
                const offer = await peerConnection.createOffer();
                await peerConnection.setLocalDescription(offer);
                socket.emit('webrtc_offer', {target: currentPartner, offer: offer, caller: myUsername});
            }

            socket.on('webrtc_offer', async (data) => {
                pendingCaller = data.caller;
                document.getElementById('video-call-interface').style.display = 'flex';
                document.getElementById('accept-call-btn').style.display = 'block';
                document.getElementById('notify-sound').play();
                peerConnection = new RTCPeerConnection(rtcConfig);
                peerConnection.ontrack = e => document.getElementById('remote-video').srcObject = e.streams[0];
                await peerConnection.setRemoteDescription(new RTCSessionDescription(data.offer));
            });

            async function acceptCall() {
                localStream = await navigator.mediaDevices.getUserMedia({video: true, audio: true});
                document.getElementById('local-video').srcObject = localStream;
                localStream.getTracks().forEach(t => peerConnection.addTrack(t, localStream));
                const answer = await peerConnection.createAnswer();
                await peerConnection.setLocalDescription(answer);
                socket.emit('webrtc_answer', {target: pendingCaller, answer: answer});
                document.getElementById('accept-call-btn').style.display = 'none';
            }

            socket.on('webrtc_answer', data => peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer)));
            socket.on('webrtc_ice', data => peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate)));
            function endCall() { location.reload(); }
            window.onload = refreshList;
        </script>
    </body>
    </html>
    """

@socketio.on('join')
def on_join(data):
    username = data['username']
    join_room(username)
    live_users_dict[request.sid] = username
    emit('live_users_update', broadcast=True)

@socketio.on('disconnect')
def on_disconnect():
    if request.sid in live_users_dict:
        del live_users_dict[request.sid]
        emit('live_users_update', broadcast=True)

@socketio.on('send_message')
def handle_message(data):
    user = session.get('user', 'Unknown')
    msg, partner, m_type = data['msg'], data['p'], data['type']
    conn = sqlite3.connect('assem_vips.db')
    conn.execute("INSERT INTO messages (sender, receiver, content, type, timestamp) VALUES (?, ?, ?, ?, ?)", (user, partner, msg, m_type, str(datetime.now())))
    conn.commit()
    socketio.emit('new_msg', {'sender': user, 'receiver': partner, 'content': msg, 'type': m_type}, room=partner)
    socketio.emit('new_msg', {'sender': user, 'receiver': partner, 'content': msg, 'type': m_type}, room=user)
    
    if partner == "AssemChat VIP":
        try:
            ai_res = model.generate_content(msg).text
            conn.execute("INSERT INTO messages (sender, receiver, content, type, timestamp) VALUES (?, ?, ?, ?, ?)", (partner, user, ai_res, 'text', str(datetime.now())))
            conn.commit()
            socketio.emit('new_msg', {'sender': partner, 'receiver': user, 'content': ai_res, 'type': 'text'}, room=user)
        except: pass
    conn.close()

@socketio.on('webrtc_offer')
def wo(data): emit('webrtc_offer', data, room=data['target'])
@socketio.on('webrtc_answer')
def wa(data): emit('webrtc_answer', data, room=data['target'])
@socketio.on('webrtc_ice')
def wi(data): emit('webrtc_ice', data, room=data['target'])

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
