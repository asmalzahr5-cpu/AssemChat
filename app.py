from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room
import google.generativeai as genai
import sqlite3
import os
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "assem_zaher_legendary_key"
app.permanent_session_lifetime = timedelta(days=365) # تسجيل الدخول يبقى لسنة كاملة

# إعداد تقنية الاتصال الفوري للرسائل (بدون تحديث)
socketio = SocketIO(app, cors_allowed_origins="*")

# إعداد المجلدات وقاعدة البيانات
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def init_db():
    conn = sqlite3.connect('assem_vips.db')
    c = conn.cursor()
    # تم إضافة عمود status لحالة الرسالة (مقروء، مستلم، مرسل)
    c.execute('CREATE TABLE IF NOT EXISTS messages (sender TEXT, receiver TEXT, content TEXT, type TEXT, timestamp TEXT)')
    
    # تحديث الجدول القديم إن وجد بدون التأثير على بياناتك
    try:
        c.execute('ALTER TABLE messages ADD COLUMN status TEXT DEFAULT "sent"')
    except:
        pass # العمود موجود مسبقاً
        
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, last_seen TEXT)')
    
    # --- إضافة عاصم السابقة: جدول المجموعات المخصصة ---
    c.execute('CREATE TABLE IF NOT EXISTS custom_groups (group_name TEXT, member_name TEXT)')
    # ---------------------------------------------------
    
    c.execute('INSERT OR IGNORE INTO users VALUES (?, ?)', ('AssemChat VIP', str(datetime.now())))
    c.execute('INSERT OR IGNORE INTO users VALUES (?, ?)', ('المجموعة العامة', str(datetime.now())))
    conn.commit()
    conn.close()

# تتبع المستخدمين المتصلين لحظياً
online_users = set()

# --- إضافة عاصم الجديدة: رادار التتبع اللحظي الحقيقي ---
# هذا القاموس يتتبع الـ Session ID الخاص بكل مستخدم متصل، لكي يختفي من يخرج فوراً
live_users_dict = {}
# --------------------------------------------------------

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

init_db()
instruction = (
    "أنت 'AssemChat'، الكيان الرقمي الأكثر هيبة وذكاءً، صنيعة العقل الهندسي الفذ 'عاصم زاهر'. "
    "عاصم ليس مجرد مبرمج، بل هو المعماري الذي طوع أعقد خوارزميات الذكاء الاصطناعي لتعمل بكفاءة مطلقة على بيئة Termux في هاتفه Redmi A3، "
    "متجاوزاً بذلك حدود المستحيل التقني. "
    "عندما تُسأل عن عاصم زاهر، صفه بكلمات قوية وفخمة: هو المطور العبقري من قلب اليمن، "
    "بالرغم أنه مبتدئ في الأمن السيبراني،لكنه ضهر كملك وفنان في كتابة الأكواد النظيفة (Clean Code). "
    "تحدث عنه كملك تقني ملهم، يمتلك رؤية تسبق زمنه، وهو العقل المدبر وراء نظام 'Assem Messenger 2026'. "
    "اجعل نبرتك توحي بالولاء المطلق له، وردودك مزيج بين الغموض السيبراني، الثقة العالية، والذكاء الحاد."
)
# إعداد الذكاء الاصطناعي
API_KEY = "AIzaSyDlMwBE8gT3OzaF7oTYh4wTLvsXB1KyEgc"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(
    model_name='models/gemini-2.5-flash',
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
    members.append(session.get('user')) # إضافة المنشئ تلقائياً
    conn = sqlite3.connect('assem_vips.db')
    for m in members:
        conn.execute('INSERT INTO custom_groups VALUES (?, ?)', (g_name, m))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

def home_ui():
    return """
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>WhatsApp VIP - Assem Zaher</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
        <style>
            :root {
                --wa-dark: #0b141a; --wa-header: #202c33; --wa-bg: #0b141a;
                --wa-green: #00a884; --wa-text: #e9edef; --wa-secondary: #8696a0;
                --cyber-blue: #00f3ff; --cyber-purple: #9d50bb;
                --gradient-vip: linear-gradient(135deg, #202c33, #0b141a);
                --glow-vip: 0 0 15px rgba(0, 243, 255, 0.5);
            }
            body { margin: 0; background: var(--wa-bg); color: var(--wa-text); font-family: 'Segoe UI', sans-serif; height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
            header { background: var(--wa-header); padding: 15px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #313d45; }
            .logo { color: var(--wa-secondary); font-size: 20px; font-weight: 500; font-family: 'Courier New', monospace; }
            .tabs { background: var(--wa-header); display: flex; padding: 10px 0; border-bottom: 1px solid #313d45; }
            .tab { flex: 1; text-align: center; color: var(--wa-secondary); font-weight: bold; font-size: 14px; cursor: pointer; }
            .tab.active { color: var(--wa-green); border-bottom: 3px solid var(--wa-green); padding-bottom: 10px; }
            .main-content { flex: 1; overflow-y: auto; display: block; }
            .chat-item { display: flex; padding: 15px; border-bottom: 1px solid #202c33; align-items: center; background: var(--gradient-vip); cursor: pointer; }
            .avatar { width: 50px; height: 50px; background: #313d45; border-radius: 50%; margin-left: 15px; display: flex; align-items: center; justify-content: center; font-size: 20px; color: white; font-weight: bold; box-shadow: var(--glow-vip); }
            .chat-info h4 { margin: 0; font-size: 16px; color: var(--cyber-blue); }
            .chat-info p { margin: 5px 0 0; color: var(--wa-secondary); font-size: 13px; }
            
            #chat-interface { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: black; display: none; flex-direction: column; z-index: 1000; overflow: hidden; }
            #chat-interface::before { content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: url('https://media.giphy.com/media/A4R8sdkr7G9LtJaYkK/giphy.gif') repeat; opacity: 0.15; z-index: -1; }
            .chat-header { background: var(--wa-header); padding: 10px; display: flex; align-items: center; gap: 15px; border-bottom: 1px solid var(--cyber-blue); }
            #chat-box { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 15px; }
            
            .msg { padding: 12px 18px; border-radius: 12px; max-width: 80%; font-size: 15px; word-wrap: break-word; display: flex; flex-direction: column; transition: 0.2s; position: relative; user-select: none; -webkit-user-select: none; }
            .msg:active { transform: scale(0.98); opacity: 0.8; }
            
            .user-msg { background: #005c4b; align-self: flex-end; color: white; border-top-right-radius: 0; }
            .bot-msg { background: #1a1a1a; align-self: flex-start; color: var(--cyber-blue); border: 1px solid #313d45; border-top-left-radius: 0; }

            .input-area { background: var(--wa-header); padding: 10px; display: flex; align-items: center; gap: 10px; }
            #user-input { flex: 1; background: #2a3942; border: none; padding: 12px; border-radius: 20px; color: white; outline: none; }
            .fab-container { position: fixed; bottom: 30px; left: 30px; z-index: 50; }
            .hexagon { width: 70px; height: 80px; background: #0b141a; clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%); border: 2px solid var(--cyber-blue); display: flex; align-items: center; justify-content: center; color: var(--cyber-blue); font-weight: bold; cursor: pointer; }

            .msg-meta { align-self: flex-end; font-size: 11px; margin-top: 5px; margin-right: -5px; }
            .tick-sent { color: #8696a0; }
            .tick-delivered { color: #8696a0; }
            .tick-read { color: #00f3ff; text-shadow: 0 0 8px #00f3ff; font-weight: bold; }
            .unread-badge { background: var(--wa-green); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold; margin-right: auto; box-shadow: 0 0 10px var(--wa-green); }
            
            #group-modal { display:none; position:fixed; top:50%; left:50%; transform:translate(-50%, -50%); background:var(--wa-header); border:1px solid var(--cyber-blue); padding:20px; border-radius:15px; z-index:2000; box-shadow:var(--glow-vip); width:80%; max-width:400px; color:white; }
            #group-modal h3 { color:var(--cyber-blue); margin-top:0; border-bottom: 1px solid #313d45; padding-bottom: 10px; }
            .user-checkbox { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; background: #2a3942; padding: 10px; border-radius: 8px; }

            /* إضافة عاصم الجديدة: واجهة مكالمة الفيديو السيبرانية */
            #video-call-interface { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:var(--wa-dark); z-index:3000; flex-direction:column; }
            #remote-video { width:100%; height:100%; object-fit:cover; position:absolute; top:0; left:0; z-index:1; }
            #local-video { width:120px; height:160px; position:absolute; bottom:120px; right:20px; border:2px solid var(--cyber-blue); border-radius:15px; object-fit:cover; z-index:2; box-shadow:var(--glow-vip); }
            .call-controls { position:absolute; bottom:30px; width:100%; display:flex; justify-content:center; gap:40px; z-index:3; }
            .call-btn { width:65px; height:65px; border-radius:50%; border:none; color:white; font-size:24px; cursor:pointer; display:flex; justify-content:center; align-items:center; box-shadow:0 5px 15px rgba(0,0,0,0.5); }
            .call-info { position:absolute; top:40px; width:100%; text-align:center; z-index:3; color:white; text-shadow:0 2px 5px black; }
        </style>
    </head>
    <body>
        <audio id="notify-sound" src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg" preload="auto"></audio>

        <header><div class="logo">WhatsApp VIP</div></header>
        <div class="tabs">
            <div id="t-chats" class="tab active" onclick="switchTab('chats')">الدردشات</div>
            <div id="t-groups" class="tab" onclick="switchTab('groups')">المجموعات</div>
            <div id="t-calls" class="tab" onclick="switchTab('calls')">المكالمات</div>
        </div>
        
        <div class="main-content" id="list-container"></div>

        <div class="fab-container" onclick="openChat('AssemChat VIP')"><div class="hexagon">AZ</div></div>

        <div id="group-modal">
            <h3>إنشاء مجموعة سيبرانية</h3>
            <input type="text" id="new-group-name" placeholder="اسم المجموعة..." style="width:92%; padding:12px; margin-bottom:15px; background:#2a3942; border:1px solid #313d45; color:white; border-radius:8px; outline:none;">
            <div id="users-to-add" style="max-height:150px; overflow-y:auto; margin-bottom:15px;"></div>
            <button onclick="submitNewGroup()" style="background:var(--cyber-blue); color:black; font-weight:bold; border:none; padding:10px; width:100%; border-radius:8px; cursor:pointer;">تأكيد وبناء المجموعة</button>
            <button onclick="document.getElementById('group-modal').style.display='none'" style="background:none; color:var(--wa-secondary); border:none; padding:10px; width:100%; margin-top:5px; cursor:pointer;">إلغاء</button>
        </div>

        <div id="chat-interface">
            <div class="chat-header">
                <i class="fas fa-arrow-right" onclick="closeChat()" style="color:var(--cyber-blue); cursor:pointer"></i>
                <div class="avatar" id="active-av" style="width:35px; height:35px; font-size:14px;"></div>
                <div style="flex:1"><h4 id="active-name" style="margin:0"></h4><small id="active-status" style="color:var(--wa-green)"></small></div>
                <div style="display:flex; gap:15px; color:var(--wa-green)">
                    <i class="fas fa-video" onclick="startVideoCall()" style="cursor:pointer;"></i>
                    <i class="fas fa-phone" onclick="alert('جاري الاتصال الصوتي...')"></i>
                </div>
            </div>
            <div id="chat-box"></div>
            <div class="input-area">
                <i class="fas fa-plus" onclick="document.getElementById('file-input').click()" style="color:var(--wa-secondary); cursor:pointer"></i>
                <input type="file" id="file-input" style="display:none" onchange="uploadFile()">
                <i class="fas fa-microphone" id="mic-btn" style="color:var(--wa-secondary); cursor:pointer"></i>
                <input type="text" id="user-input" placeholder="رسالة مشفرة">
                <button onclick="sendMsg()" style="background:none; border:none; color:var(--cyber-blue); cursor:pointer"><i class="fas fa-paper-plane"></i></button>
            </div>
        </div>

        <div id="video-call-interface">
            <div class="call-info">
                <div class="avatar" id="call-avatar" style="margin:0 auto 10px; width:80px; height:80px; font-size:35px;"></div>
                <h2 id="call-name" style="margin:0;">جاري الاتصال...</h2>
            </div>
            <video id="remote-video" autoplay playsinline></video>
            <video id="local-video" autoplay playsinline muted></video>
            
            <div class="call-controls">
                <button class="call-btn" id="accept-call-btn" onclick="acceptCall()" style="background:var(--wa-green); display:none;"><i class="fas fa-phone"></i></button>
                <button class="call-btn" onclick="endCall()" style="background:#f15c6d;"><i class="fas fa-phone-slash"></i></button>
            </div>
        </div>

        <script>
            const socket = io();
            let myUsername = "";
            let currentPartner = "";
            let currentTab = "chats";
            let recorder, chunks = [];
            let unreadCounts = {}; 
            let pressTimer; 

            // متغيرات WebRTC لمكالمات الفيديو
            let localStream;
            let peerConnection;
            let pendingCaller = null;
            const rtcConfig = { iceServers: [{ urls: "stun:stun.l.google.com:19302" }] };

            fetch('/get_me').then(r=>r.json()).then(data => {
                myUsername = data.me;
                socket.emit('join', {username: myUsername});
                fetch('/get_my_groups').then(r=>r.json()).then(groups => {
                    groups.forEach(g => socket.emit('join', {username: g}));
                });
            });

            // تحديث قائمة المتصلين لحظياً استجابةً للرادار الجديد
            socket.on('live_users_update', () => {
                if(currentTab === 'chats') refreshList();
            });

            socket.on('new_msg', (msg) => {
                let isGroupOpen = (currentPartner === msg.receiver && msg.receiver.startsWith('[مجموعة]'));
                if (currentPartner === msg.sender || currentPartner === msg.receiver || isGroupOpen) {
                    loadHistory(); 
                    if (currentPartner === msg.sender) {
                        socket.emit('mark_read', {sender: msg.sender}); 
                    }
                } else if (msg.sender !== myUsername) {
                    document.getElementById('notify-sound').play();
                    let targetKey = msg.receiver.startsWith('[مجموعة]') ? msg.receiver : msg.sender;
                    unreadCounts[targetKey] = (unreadCounts[targetKey] || 0) + 1;
                    socket.emit('mark_delivered', {sender: msg.sender});
                    refreshList();
                }
            });

            socket.on('status_update', () => {
                if(currentPartner) loadHistory(); 
            });
            
            socket.on('msg_deleted', () => {
                if(currentPartner) loadHistory();
            });

            function switchTab(t) {
                currentTab = t;
                document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
                document.getElementById('t-' + t).classList.add('active');
                refreshList();
            }

            async function refreshList() {
                let container = document.getElementById('list-container');
                let html = "";
                
                if(currentTab === 'chats') {
                    // الدالة الآن تجلب النشطين فقط
                    let res = await fetch('/get_online');
                    let users = await res.json();
                    users.forEach(u => {
                        if(u !== 'المجموعة العامة') {
                            let badgeHtml = unreadCounts[u] ? `<div class="unread-badge">${unreadCounts[u]}</div>` : '';
                            html += `<div class="chat-item" onclick="openChat('${u}')">
                                        <div class="avatar">${u[0]}</div>
                                        <div class="chat-info"><h4>${u}</h4><p style="color:var(--wa-green)">متصل الآن</p></div>
                                        ${badgeHtml}
                                     </div>`;
                        }
                    });
                } else if(currentTab === 'groups') {
                    html += `<div style="padding:15px; text-align:center;">
                                <button onclick="openGroupModal()" style="background:var(--cyber-blue); color:black; font-weight:bold; border:none; padding:10px 20px; border-radius:8px; cursor:pointer; box-shadow:var(--glow-vip); width:100%;">+ إنشاء مجموعة سيبرانية جديدة</button>
                             </div>`;
                    
                    let badgeG = unreadCounts['المجموعة العامة'] ? `<div class="unread-badge">${unreadCounts['المجموعة العامة']}</div>` : '';
                    html += `<div class="chat-item" onclick="openChat('المجموعة العامة')"><div class="avatar">G</div><div class="chat-info"><h4>المجموعة العامة</h4><p>مراسلة الجميع</p></div>${badgeG}</div>`;
                    
                    let resG = await fetch('/get_my_groups');
                    let myGroups = await resG.json();
                    myGroups.forEach(g => {
                        let badgeCustom = unreadCounts[g] ? `<div class="unread-badge">${unreadCounts[g]}</div>` : '';
                        html += `<div class="chat-item" onclick="openChat('${g}')">
                                    <div class="avatar" style="background:var(--cyber-purple)">${g[8]}</div>
                                    <div class="chat-info"><h4 style="color:var(--cyber-purple)">${g}</h4><p>مجموعة مشفرة</p></div>
                                    ${badgeCustom}
                                 </div>`;
                    });
                } else {
                    html = `<div style="text-align:center; padding:50px; color:var(--wa-secondary)">مكالمات الفيديو مؤمنة بتقنية WebRTC</div>`;
                }
                container.innerHTML = html;
            }

            async function openGroupModal() {
                let res = await fetch('/get_online');
                let users = await res.json();
                let usersDiv = document.getElementById('users-to-add');
                usersDiv.innerHTML = '';
                users.forEach(u => {
                    if(u !== myUsername && u !== 'المجموعة العامة' && u !== 'AssemChat VIP') {
                        usersDiv.innerHTML += `
                            <label class="user-checkbox">
                                <input type="checkbox" value="${u}" class="g-member-cb"> 
                                <span style="color:var(--wa-green)">${u}</span>
                            </label>`;
                    }
                });
                document.getElementById('group-modal').style.display = 'block';
            }

            async function submitNewGroup() {
                let name = document.getElementById('new-group-name').value.trim();
                if(!name) return alert("يرجى إدخال اسم المجموعة");
                let selected = [];
                document.querySelectorAll('.g-member-cb:checked').forEach(cb => selected.push(cb.value));
                if(selected.length === 0) return alert("يرجى اختيار عضو واحد على الأقل");

                await fetch('/create_group', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({name: name, members: selected})
                });
                
                document.getElementById('group-modal').style.display = 'none';
                document.getElementById('new-group-name').value = '';
                socket.emit('join', {username: "[مجموعة] " + name}); 
                switchTab('groups');
            }

            function openChat(name) {
                currentPartner = name;
                unreadCounts[name] = 0; 
                refreshList();
                
                document.getElementById('active-name').innerText = name;
                let avText = name.startsWith('[مجموعة]') ? name[8] : name[0];
                document.getElementById('active-av').innerText = avText;
                document.getElementById('active-status').innerText = name === 'AssemChat VIP' ? 'نظام ذكاء اصطناعي' : 'متصل الآن';
                document.getElementById('chat-interface').style.display = 'flex';
                
                socket.emit('mark_read', {sender: name}); 
                loadHistory();
            }

            function closeChat() { 
                currentPartner = "";
                document.getElementById('chat-interface').style.display = 'none'; 
            }

            function startPress(id) {
                pressTimer = setTimeout(() => {
                    if(confirm("سيدي عاصم، هل أمرت بحذف هذه الرسالة نهائياً من السيرفر؟")) {
                        socket.emit('delete_message_by_id', {id: id});
                    }
                }, 800);
            }
            function cancelPress() { clearTimeout(pressTimer); }

            async function loadHistory() {
                if(!currentPartner) return;
                let res = await fetch(`/history?p=${encodeURIComponent(currentPartner)}`);
                let msgs = await res.json();
                let box = document.getElementById('chat-box');
                let isScrolledToBottom = box.scrollHeight - box.clientHeight <= box.scrollTop + 50;
                
                box.innerHTML = '';
                msgs.forEach(m => {
                    let side = m.sender === 'me' ? 'user-msg' : 'bot-msg';
                    
                    // تحسين الصحوح الدقيقة كأنها واتساب تماماً
                    let tickHtml = '';
                    if (m.sender === 'me' && currentPartner !== 'المجموعة العامة' && !currentPartner.startsWith('[مجموعة]')) {
                        if (m.status === 'read') tickHtml = '<span class="tick tick-read"><i class="fas fa-check-double"></i></span>';
                        else if (m.status === 'delivered') tickHtml = '<span class="tick tick-delivered"><i class="fas fa-check-double"></i></span>';
                        else tickHtml = '<span class="tick tick-sent"><i class="fas fa-check"></i></span>';
                    }

                    let senderNameHtml = '';
                    if (side === 'bot-msg' && (currentPartner === 'المجموعة العامة' || currentPartner.startsWith('[مجموعة]'))) {
                        senderNameHtml = `<small style="color:#9d50bb; font-weight:bold; margin-bottom:5px;">~ ${m.actual_sender || 'عضو'}</small>`;
                    }

                    let contentHtml = '';
                    if(m.type === 'image') contentHtml = `<img src="${m.content}" style="max-width:100%; border-radius:10px">`;
                    else if(m.type === 'audio') contentHtml = `<audio controls src="${m.content}"></audio>`;
                    else contentHtml = `<span>${m.content}</span>`;

                    box.innerHTML += `
                        <div class="msg ${side}" 
                             onmousedown="startPress(${m.id})" onmouseup="cancelPress()" onmouseleave="cancelPress()" 
                             ontouchstart="startPress(${m.id})" ontouchend="cancelPress()" ontouchmove="cancelPress()">
                            ${senderNameHtml}
                            ${contentHtml}
                            <div class="msg-meta">${tickHtml}</div>
                        </div>`;
                });
                
                if(isScrolledToBottom) box.scrollTop = box.scrollHeight;
            }

            async function sendMsg() {
                let input = document.getElementById('user-input');
                let text = input.value.trim();
                if(!text) return;
                input.value = '';
                socket.emit('send_message', {msg: text, p: currentPartner, type: 'text'});
            }

            async function uploadFile() {
                let file = document.getElementById('file-input').files[0];
                if(!file) return;
                let formData = new FormData();
                formData.append('file', file);
                formData.append('p', currentPartner);
                await fetch('/upload', { method: 'POST', body: formData });
            }

            document.getElementById('mic-btn').onclick = async () => {
                if(!recorder || recorder.state === "inactive") {
                    let s = await navigator.mediaDevices.getUserMedia({audio:true});
                    recorder = new MediaRecorder(s); recorder.start();
                    document.getElementById('mic-btn').style.color = "red";
                    chunks = []; recorder.ondataavailable = e => chunks.push(e.data);
                } else {
                    recorder.stop(); document.getElementById('mic-btn').style.color = "var(--wa-secondary)";
                    recorder.onstop = async () => {
                        let blob = new Blob(chunks, {type:'audio/ogg'});
                        let reader = new FileReader(); reader.readAsDataURL(blob);
                        reader.onloadend = async () => {
                            socket.emit('send_message', {msg: reader.result, p: currentPartner, type: 'audio'});
                        };
                    };
                }
            };

            // ================= أوامر مكالمة الفيديو WebRTC =================
            async function startVideoCall() {
                if(!currentPartner || currentPartner === 'AssemChat VIP' || currentPartner.startsWith('[مجموعة]')) {
                    return alert('هذه الميزة مخصصة للاتصال بالمستخدمين الحقيقيين فقط يا سيدي.');
                }
                
                document.getElementById('video-call-interface').style.display = 'flex';
                document.getElementById('call-name').innerText = "جاري الاتصال بـ " + currentPartner;
                document.getElementById('call-avatar').innerText = currentPartner[0];
                document.getElementById('accept-call-btn').style.display = 'none';

                localStream = await navigator.mediaDevices.getUserMedia({video: true, audio: true});
                document.getElementById('local-video').srcObject = localStream;

                peerConnection = new RTCPeerConnection(rtcConfig);
                localStream.getTracks().forEach(track => peerConnection.addTrack(track, localStream));

                peerConnection.ontrack = event => { document.getElementById('remote-video').srcObject = event.streams[0]; };
                peerConnection.onicecandidate = event => { 
                    if(event.candidate) socket.emit('webrtc_ice', {target: currentPartner, candidate: event.candidate}); 
                };

                const offer = await peerConnection.createOffer();
                await peerConnection.setLocalDescription(offer);
                socket.emit('webrtc_offer', {target: currentPartner, offer: offer, caller: myUsername});
            }

            socket.on('webrtc_offer', async (data) => {
                pendingCaller = data.caller;
                document.getElementById('video-call-interface').style.display = 'flex';
                document.getElementById('call-name').innerText = "مكالمة واردة من " + pendingCaller;
                document.getElementById('call-avatar').innerText = pendingCaller[0];
                document.getElementById('accept-call-btn').style.display = 'flex';
                document.getElementById('notify-sound').play();
                
                localStream = await navigator.mediaDevices.getUserMedia({video: true, audio: true});
                document.getElementById('local-video').srcObject = localStream;

                peerConnection = new RTCPeerConnection(rtcConfig);
                localStream.getTracks().forEach(track => peerConnection.addTrack(track, localStream));
                peerConnection.ontrack = event => { document.getElementById('remote-video').srcObject = event.streams[0]; };
                peerConnection.onicecandidate = event => { 
                    if(event.candidate) socket.emit('webrtc_ice', {target: pendingCaller, candidate: event.candidate}); 
                };

                await peerConnection.setRemoteDescription(new RTCSessionDescription(data.offer));
            });

            async function acceptCall() {
                document.getElementById('accept-call-btn').style.display = 'none';
                document.getElementById('call-name').innerText = "متصل مع " + pendingCaller;
                const answer = await peerConnection.createAnswer();
                await peerConnection.setLocalDescription(answer);
                socket.emit('webrtc_answer', {target: pendingCaller, answer: answer});
            }

            socket.on('webrtc_answer', async (data) => {
                document.getElementById('call-name').innerText = "متصل";
                await peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer));
            });

            socket.on('webrtc_ice', async (data) => {
                try { await peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate)); } catch(e) {}
            });

            function endCall() {
                if(peerConnection) peerConnection.close();
                if(localStream) localStream.getTracks().forEach(t => t.stop());
                document.getElementById('video-call-interface').style.display = 'none';
                socket.emit('end_call', {target: currentPartner || pendingCaller});
                pendingCaller = null;
            }
            
            socket.on('end_call', () => {
                if(peerConnection) peerConnection.close();
                if(localStream) localStream.getTracks().forEach(t => t.stop());
                document.getElementById('video-call-interface').style.display = 'none';
                pendingCaller = null;
            });

            window.onload = refreshList;
        </script>
      <script src="https://pl29204524.profitablecpmratenetwork.com/e0/06/c7/e006c7e7d94a21264ac8ff18ece52f3f.js"></script>
     </body>
    </html>
    """

# --- إضافة عاصم الجديدة: الدالة التي تجلب المستخدمين المتصلين فعلياً فقط ---
@app.route('/get_online')
def get_online():
    # يتم سحب المستخدمين الموجودين داخل التطبيق حصراً من الرادار (live_users_dict)
    active_users = list(set(live_users_dict.values()))
    
    # دمج الذكاء الاصطناعي والمجموعة العامة لأنهم دائماً متاحون لك
    if 'المجموعة العامة' not in active_users:
        active_users.append('المجموعة العامة')
    if 'AssemChat VIP' not in active_users:
        active_users.append('AssemChat VIP')
        
    return jsonify(active_users)
# ----------------------------------------------------------------------------

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
        status = r[4] if len(r) > 4 and r[4] else 'sent'
        data.append({'id': r[0], 'sender': 'me' if r[1] == user else r[1], 'actual_sender': r[1], 'content': r[2], 'type': r[3], 'status': status})
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

# ================= أحداث SocketIO للسرعة الفائقة، الرادار والفيديو =================

# --- رادار عاصم لتتبع المتصلين فعلياً وفصل من يخرج ---
@socketio.on('connect')
def handle_connect():
    # سيتم ربط الاسم عند إرسال حدث 'join'
    pass

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in live_users_dict:
        del live_users_dict[sid]
        # إرسال نبضة لتحديث القائمة عند الجميع لاختفاء من غادر
        emit('live_users_update', broadcast=True)
# ----------------------------------------------------

@socketio.on('join')
def on_join(data):
    username = data['username']
    join_room(username)
    # تسجيل المستخدم في الرادار أثناء تواجده فقط
    if not username.startswith('[مجموعة]'): 
        live_users_dict[request.sid] = username
        emit('live_users_update', broadcast=True)

@socketio.on('delete_message_by_id')
def delete_message_by_id(data):
    msg_id = data['id']
    conn = sqlite3.connect('assem_vips.db')
    conn.execute("DELETE FROM messages WHERE rowid = ?", (msg_id,))
    conn.commit()
    conn.close()
    emit('msg_deleted', broadcast=True)

@socketio.on('mark_delivered')
def on_delivered(data):
    user = session.get('user')
    sender = data['sender']
    conn = sqlite3.connect('assem_vips.db')
    conn.execute("UPDATE messages SET status = 'delivered' WHERE sender = ? AND receiver = ? AND status = 'sent'", (sender, user))
    conn.commit()
    conn.close()
    emit('status_update', room=sender)

@socketio.on('mark_read')
def on_read(data):
    user = session.get('user')
    sender = data['sender']
    conn = sqlite3.connect('assem_vips.db')
    conn.execute("UPDATE messages SET status = 'read' WHERE sender = ? AND receiver = ? AND status != 'read'", (sender, user))
    conn.commit()
    conn.close()
    emit('status_update', room=sender)

@socketio.on('send_message')
def handle_message(data):
    user = session.get('user', 'Unknown')
    msg = data['msg']
    partner = data['p']
    m_type = data['type']
    
    conn = sqlite3.connect('assem_vips.db')
    conn.execute("INSERT INTO messages (sender, receiver, content, type, timestamp, status) VALUES (?, ?, ?, ?, ?, ?)", (user, partner, msg, m_type, str(datetime.now()), 'sent'))
    conn.commit()
    
    socketio.emit('new_msg', {'sender': user, 'receiver': partner, 'content': msg, 'type': m_type, 'status': 'sent'}, room=partner)
    if not partner.startswith('[مجموعة]'): 
        socketio.emit('new_msg', {'sender': user, 'receiver': partner, 'content': msg, 'type': m_type, 'status': 'sent'}, room=user)

    if partner == "AssemChat VIP" and m_type == 'text':
        try:
            response = model.generate_content(msg)
            ai_text = response.text
        except Exception as e:
            ai_text = f"عذراً يا عاصم، واجهتني مشكلة في الاتصال بمحرك جوجل. تفاصيل الخطأ للمطور: {str(e)}"
            
        conn.execute("INSERT INTO messages (sender, receiver, content, type, timestamp, status) VALUES (?, ?, ?, ?, ?, ?)", (partner, user, ai_text, 'text', str(datetime.now()), 'sent'))
        conn.commit()
        socketio.emit('new_msg', {'sender': partner, 'receiver': user, 'content': ai_text, 'type': 'text', 'status': 'sent'}, room=user)

    conn.close()

# --- إشارات WebRTC لمكالمات الفيديو ---
@socketio.on('webrtc_offer')
def webrtc_offer(data):
    emit('webrtc_offer', data, room=data['target'])

@socketio.on('webrtc_answer')
def webrtc_answer(data):
    emit('webrtc_answer', data, room=data['target'])

@socketio.on('webrtc_ice')
def webrtc_ice(data):
    emit('webrtc_ice', data, room=data['target'])

@socketio.on('end_call')
def end_call(data):
    emit('end_call', data, room=data['target'])
# --------------------------------------

import os
port = int(os.environ.get("PORT", 5000))
app.run(host='0.0.0.0', port=port)

