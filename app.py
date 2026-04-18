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
    c.execute('INSERT OR IGNORE INTO users VALUES (?, ?)', ('AssemChat VIP', str(datetime.now())))
    c.execute('INSERT OR IGNORE INTO users VALUES (?, ?)', ('المجموعة العامة', str(datetime.now())))
    conn.commit()
    conn.close()

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

def home_ui():
    # تصميمك الأصلي كما هو مع إضافات الـ CSS البسيطة للصحين والدائرة الخضراء والصوت
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
            
            .msg { padding: 12px 18px; border-radius: 12px; max-width: 80%; font-size: 15px; word-wrap: break-word; display: flex; flex-direction: column; }
            .user-msg { background: #005c4b; align-self: flex-end; color: white; border-top-right-radius: 0; }
            .bot-msg { background: #1a1a1a; align-self: flex-start; color: var(--cyber-blue); border: 1px solid #313d45; border-top-left-radius: 0; }

            .input-area { background: var(--wa-header); padding: 10px; display: flex; align-items: center; gap: 10px; }
            #user-input { flex: 1; background: #2a3942; border: none; padding: 12px; border-radius: 20px; color: white; outline: none; }
            .fab-container { position: fixed; bottom: 30px; left: 30px; z-index: 50; }
            .hexagon { width: 70px; height: 80px; background: #0b141a; clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%); border: 2px solid var(--cyber-blue); display: flex; align-items: center; justify-content: center; color: var(--cyber-blue); font-weight: bold; cursor: pointer; }

            /* الإضافات الجديدة حسب طلبك (الصحين، الدائرة الخضراء) */
            .msg-meta { align-self: flex-end; font-size: 11px; margin-top: 5px; margin-right: -5px; }
            .tick-sent { color: #8696a0; }
            .tick-delivered { color: #8696a0; }
            .tick-read { color: #00f3ff; text-shadow: 0 0 8px #00f3ff; font-weight: bold; }
            .unread-badge { background: var(--wa-green); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold; margin-right: auto; box-shadow: 0 0 10px var(--wa-green); }
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

        <div id="chat-interface">
            <div class="chat-header">
                <i class="fas fa-arrow-right" onclick="closeChat()" style="color:var(--cyber-blue); cursor:pointer"></i>
                <div class="avatar" id="active-av" style="width:35px; height:35px; font-size:14px;"></div>
                <div style="flex:1"><h4 id="active-name" style="margin:0"></h4><small id="active-status" style="color:var(--wa-green)"></small></div>
                <div style="display:flex; gap:15px; color:var(--wa-green)">
                    <i class="fas fa-video" onclick="alert('جاري بدء مكالمة فيديو حقيقية...')"></i>
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

        <script>
            const socket = io();
            let myUsername = "";
            let currentPartner = "";
            let currentTab = "chats";
            let recorder, chunks = [];
            let unreadCounts = {}; // تتبع عدد الرسائل غير المقروءة للدائرة الخضراء

            // جلب اسم المستخدم للاتصال الفوري
            fetch('/get_me').then(r=>r.json()).then(data => {
                myUsername = data.me;
                socket.emit('join', {username: myUsername});
            });

            // استقبال الرسائل المباشرة بدون تحديث!
            socket.on('new_msg', (msg) => {
                if (currentPartner === msg.sender || currentPartner === msg.receiver) {
                    loadHistory(); // تحديث الدردشة المفتوحة
                    if (currentPartner === msg.sender) {
                        socket.emit('mark_read', {sender: msg.sender}); // إرسال حالة مقروء (صحين مضيئة)
                    }
                } else if (msg.sender !== myUsername) {
                    // رسالة من شخص آخر لم نفتح دردشته: صوت + دائرة خضراء + صحين باهتة
                    document.getElementById('notify-sound').play();
                    unreadCounts[msg.sender] = (unreadCounts[msg.sender] || 0) + 1;
                    socket.emit('mark_delivered', {sender: msg.sender});
                    refreshList();
                }
            });

            socket.on('status_update', () => {
                if(currentPartner) loadHistory(); // تحديث الصحين فوراً
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
                        if(u !== 'المجموعة العامة') {
                            let badgeHtml = unreadCounts[u] ? `<div class="unread-badge">${unreadCounts[u]}</div>` : '';
                            html += `<div class="chat-item" onclick="openChat('${u}')">
                                        <div class="avatar">${u[0]}</div>
                                        <div class="chat-info"><h4>${u}</h4><p>متصل عبر AssemNet</p></div>
                                        ${badgeHtml}
                                     </div>`;
                        }
                    });
                } else if(currentTab === 'groups') {
                    html = `<div class="chat-item" onclick="openChat('المجموعة العامة')"><div class="avatar">G</div><div class="chat-info"><h4>المجموعة العامة</h4><p>مراسلة الجميع</p></div></div>`;
                } else {
                    html = `<div style="text-align:center; padding:50px; color:var(--wa-secondary)">لا توجد مكالمات سابقة</div>`;
                }
                container.innerHTML = html;
            }

            function openChat(name) {
                currentPartner = name;
                unreadCounts[name] = 0; // إخفاء الدائرة الخضراء عند الفتح
                refreshList();
                
                document.getElementById('active-name').innerText = name;
                document.getElementById('active-av').innerText = name[0];
                document.getElementById('active-status').innerText = name === 'AssemChat VIP' ? 'نظام ذكاء اصطناعي' : 'تشفير AssemNet نشط';
                document.getElementById('chat-interface').style.display = 'flex';
                
                socket.emit('mark_read', {sender: name}); // تأكيد القراءة
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
                let isScrolledToBottom = box.scrollHeight - box.clientHeight <= box.scrollTop + 50;
                
                box.innerHTML = '';
                msgs.forEach(m => {
                    let side = m.sender === 'me' ? 'user-msg' : 'bot-msg';
                    
                    // نظام الصحين (علامات الحالة)
                    let tickHtml = '';
                    if (m.sender === 'me' && currentPartner !== 'المجموعة العامة') {
                        if (m.status === 'read') tickHtml = '<span class="tick tick-read"><i class="fas fa-check-double"></i></span>';
                        else if (m.status === 'delivered') tickHtml = '<span class="tick tick-delivered"><i class="fas fa-check-double"></i></span>';
                        else tickHtml = '<span class="tick tick-sent"><i class="fas fa-check"></i></span>';
                    }

                    let contentHtml = '';
                    if(m.type === 'image') contentHtml = `<img src="${m.content}" style="max-width:100%; border-radius:10px">`;
                    else if(m.type === 'audio') contentHtml = `<audio controls src="${m.content}"></audio>`;
                    else contentHtml = `<span>${m.content}</span>`;

                    box.innerHTML += `<div class="msg ${side}">${contentHtml}<div class="msg-meta">${tickHtml}</div></div>`;
                });
                
                if(isScrolledToBottom) box.scrollTop = box.scrollHeight;
            }

            async function sendMsg() {
                let input = document.getElementById('user-input');
                let text = input.value.trim();
                if(!text) return;

                input.value = '';

                // نرسل الرسالة عبر SocketIO للسرعة الفائقة
                socket.emit('send_message', {msg: text, p: currentPartner, type: 'text'});
            }

            async function uploadFile() {
                let file = document.getElementById('file-input').files[0];
                if(!file) return;
                let formData = new FormData();
                formData.append('file', file);
                formData.append('p', currentPartner);
                await fetch('/upload', { method: 'POST', body: formData });
                // السيرفر سيتولى البث الفوري
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

            // لقد قمت بحذف setInterval كما طلبت! الآن التطبيق يعمل بالاتصال المباشر الفوري.
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
        cursor.execute("SELECT sender, content, type, status FROM messages WHERE receiver = ?", (p,))
    else:
        cursor.execute("SELECT sender, content, type, status FROM messages WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)", (user, p, p, user))
    
    # التعامل مع الحالة الافتراضية إذا لم تكن موجودة
    data = []
    for r in cursor.fetchall():
        status = r[3] if len(r) > 3 and r[3] else 'sent'
        data.append({'sender': 'me' if r[0] == user else r[0], 'content': r[1], 'type': r[2], 'status': status})
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
        
        # بث الرسالة فوراً
        socketio.emit('new_msg', {'sender': user, 'receiver': partner, 'content': '/static/uploads/'+filename, 'type': 'image', 'status': 'sent'}, room=partner)
        socketio.emit('new_msg', {'sender': user, 'receiver': partner, 'content': '/static/uploads/'+filename, 'type': 'image', 'status': 'sent'}, room=user)
    return jsonify({'status': 'ok'})

# ================= أحداث SocketIO للسرعة الفائقة وتحديث الحالة =================

@socketio.on('join')
def on_join(data):
    username = data['username']
    join_room(username)

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
    
    # بث الرسالة الفوري لكلا الطرفين (المرسل والمستقبل)
    socketio.emit('new_msg', {'sender': user, 'receiver': partner, 'content': msg, 'type': m_type, 'status': 'sent'}, room=partner)
    socketio.emit('new_msg', {'sender': user, 'receiver': partner, 'content': msg, 'type': m_type, 'status': 'sent'}, room=user)

    # إصلاح مشكلة الذكاء الاصطناعي بجعله ينطق الخطأ بدلاً من الصمت
    if partner == "AssemChat VIP" and m_type == 'text':
        try:
            response = model.generate_content(msg)
            ai_text = response.text
        except Exception as e:
            # هنا التعديل الذي سيجعلك تعرف لماذا لا يرد
            ai_text = f"عذراً يا عاصم، واجهتني مشكلة في الاتصال بمحرك جوجل. تفاصيل الخطأ للمطور: {str(e)}"
            
        conn.execute("INSERT INTO messages (sender, receiver, content, type, timestamp, status) VALUES (?, ?, ?, ?, ?, ?)", (partner, user, ai_text, 'text', str(datetime.now()), 'sent'))
        conn.commit()
        socketio.emit('new_msg', {'sender': partner, 'receiver': user, 'content': ai_text, 'type': 'text', 'status': 'sent'}, room=user)

    conn.close()

if __name__ == '__main__':
    # استخدمنا socketio.run بدلاً من app.run لتفعيل الشات الفوري
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

