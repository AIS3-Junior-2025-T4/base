# run.py
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from flask_cors import CORS
from functools import lru_cache, wraps
import secrets
import os
import re
import socket

from app.linuxCMD import *

BOT_PORT = int(os.getenv("BOT_PORT", 7777))
BOT_HOST = os.getenv("BOT_HOST", "localhost")
# 取得 main.py 檔案所在的目錄的絕對路徑
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 將 'notes' 資料夾的路徑與其拼接
NOTES_DIR = os.path.join(BASE_DIR, "notes")

# 確保 notes 資料夾存在，如果不存在就建立它
if not os.path.exists(NOTES_DIR):
    os.makedirs(NOTES_DIR)

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'app', 'templates'),
    static_folder=os.path.join(BASE_DIR, 'app', 'static'),
)


print("Template folder:", app.template_folder)
print("index.html exists?", os.path.exists(os.path.join(app.template_folder, "index.html")))

CORS(app)
app.config['SECRET_KEY'] = os.urandom(16)

# -----------------------------
# 資料庫（可日後搬到 DB）
# -----------------------------
# 題目資料庫：介紹、前往網址、正確答案與提示
QUESTS = {
    "q1": {
        "title": "第一關：幽影中的密語",
        "intro": "在黑暗中，只有 cookie 會說話。找到它，抄下它。",
        "goto_url": "/challenge/cookie",  # TODO: 換成你的實際路徑或外部題目網址
        "answer": "FLAG{this_is_the_first_secret}",
        "hints": [
            "瀏覽器的儲存之處不只一個。",
            "開發者工具 → Application → Cookies。",
            "看起來像 FLAG 的字串，通常就是它。"
        ]
    },
    "q2": {
        "title": "第二關：破譯者之眼",
        "intro": "頁面上什麼都沒有？那就看看原始碼。還不夠？也許要觀察請求。",
        "goto_url": "/challenge/pwn",  # TODO: 換成你的實際路徑或外部題目網址
        "answer": "FLAG{another_cool_flag_here}",
        "hints": [
            "右鍵 → 檢視原始碼。",
            "Network 分頁常有驚喜。",
            "別忘了搜尋 'FLAG'。"
        ]
    }
}

# 劇情資料庫：type 支援
# - dialogue：敘事
# - quest：顯示題目介紹與「前往」按鈕（quest_id 對應 QUESTS）
# - question：彈出對話框，等待答題（question_id 對應 QUESTS）
# - end：結束
STORY = [
    {"type": "dialogue", "character": "旁白", "text": "這是一個寂靜的夜晚，你收到一封神秘的信件…"},
    {"type": "dialogue", "character": "神秘客", "text": "如果你能看到這則訊息，代表你就是我們要找的人。"},
    {"type": "dialogue", "character": "神秘客", "text": "我們需要你的幫助。但首先，你需要證明自己的能力。"},
    {"type": "quest", "quest_id": "q1"},          # 顯示 q1 的題目卡
    {"type": "question", "question_id": "q1"},    # 等待 q1 作答；答對才會繼續
    {"type": "dialogue", "character": "神秘客", "text": "做得好！接下來會更困難。"},
    {"type": "quest", "quest_id": "q2"},
    {"type": "question", "question_id": "q2"},
    {"type": "dialogue", "character": "旁白", "text": "恭喜你完成所有挑戰！"},
    {"type": "end"}
]

QUESTS = {
    "q1": {
        "title": "第一關：Linux",
        "intro": "找出FLAG & 熟悉LINUX指令",
        "goto_url": "/challenge/linux",  # TODO: 換成你的實際路徑或外部題目網址
        "answer": "flag{linux_basics_ok}",
        "hints": [
        ]
    },
    "q2": {
        "title": "第二關：Request",
        "intro": "BURP入門，想辦法猜拳營電腦吧~",
        "goto_url": "/challenge/request",  # TODO: 換成你的實際路徑或外部題目網址
        "answer": "FLAG{you_modified_the_request_body_successfully}",
        "hints": [
        ]
    },
    "q3": {
        "title": "第三關：Burp Suite",
        "intro": "這是一個登入介面，要怎麼才能登入呢?(學會BURP爆破密碼功能)",
        "goto_url": "/challenge/pwn",  # TODO: 換成你的實際路徑或外部題目網址
        "answer": "flag{easy_brute_force}",
        "hints": [
        ]
    },
    "q4": {
        "title": "第四關：Cookie",
        "intro": "現在你有帳號密碼了!那要怎麼拿到FLAG呢?(hint:decode,cookie)",
        "goto_url": "/challenge/cookie",  # TODO: 換成你的實際路徑或外部題目網址
        "answer": "flag{c00k13_h4ck_succc3ss}",
        "hints": [
        ]
    },
    "q5": {
        "title": "第五關：XSS",
        "intro": "接觸JAVASCRIPT，了解如何注入網頁",
        "goto_url": "/challenge/xss",  # TODO: 換成你的實際路徑或外部題目網址
        "answer": "flag{wow_you_are_going_to_win}",
        "hints": [
        ]
    }
}
# 劇情資料庫
STORY = [
    {"type": "dialogue", "text": "歡迎來到這次的AIS3 junior的營隊,  __{name}__ ！"},
    {"type": "dialogue", "text": "在這次營隊中，我們將會學到許多有關網路安全前後端的技術"},
    {"type": "dialogue", "text": "你準備接受挑戰了嗎?"},
    {"type": "dialogue", "text": "溫馨提示，請勿將本闖關所學習到的技術用於非法用途\n畢竟嘛~~~我們是一群好駭客呀"},
    {"type": "dialogue", "text": "第一天課程："},
    {"type": "dialogue", "text": "早上，講師三角snake為了讓 __{name}__ 知道\n 身為一個好駭客都需要使用linux\n於是跟他分享了linux的相關特點與優勢\n如:開源、網頁伺服器常用Linux等..."},
    {"type": "dialogue", "text": "在介紹完這些後，三角snake告訴了 __{name}__ linux的相關指令: \nls # 查看當下目錄\nls -a # 查看當下目錄(可以看到隱藏資料)\ncd /{dir_name} # 移動到{dir_name}資料夾\npwd # 自己在哪\ncat {file_name} # 看{file_name}的內容......"},
    {"type": "dialogue", "text": "在介紹完這些後，三角snake給了 __{name}__ 一個小測驗\n以證明他是不是真的學會了......"},
    
    {"type": "quest", "quest_id": "q1", "title": "第一關：Linux"},
    {"type": "dialogue", "text": "挑戰者需要利用剛剛學習到的相關指令\n先找出hint1，然後找到hint2，最終找出flag在哪裡"},
    {"type": "question", "question_id": "q1"},

    {"type": "dialogue", "text": "做得好！接下來會更困難"},
    {"type": "dialogue", "text": "吃過美味的肯德基後， __{name}__ 精神滿滿的回去上接下來下午的課程......"},
    {"type": "dialogue", "text": "課程剛開始，一位名為歐薩卡的助教跟 __{name}__ 介紹了\n 中電會(SCAICT)及南臺灣學生資訊社群(SCIST)"},
    {"type": "dialogue", "text": "經由歐薩卡的介紹，你得知原來在台灣，有著如此豐富的資訊交流環境"},
    {"type": "dialogue", "text": " __{name}__ 在經過審慎的評估過後，決定兩個都加入\n並決定多與這些社群中志同道合的同學們互相交流、互相成長"},
    {"type": "dialogue", "text": "之後，三角snake才開始介紹網路-前端給 __{name}__ 聽\n __{name}__ 知道了前端三件套:HTML、JavaScript、CSS\n還知道了Header、Request Body是什麼"},
    {"type": "dialogue", "text": "五點，飢腸轆轆的 __{name}__ 在上完一天的課程後\n決定去吃炸豬排......這燉飯還因為學生的身份獲得了一杯招待飲料\n真是太幸運了!!!\n唯一美中不足的就是......不小心將應該倒在沙拉上的和風醬倒在了自己的褲子上......." },
    {"type": "dialogue", "text": "六點半， __{name}__ 回到了教室，開始寫三角snake給他佈置的作業"},
    
    {"type": "quest", "quest_id": "q2", "title": "第二關：Request"},
    {"type": "dialogue", "text": "這是今天的作業，來試試看BURP入門，想辦法猜拳贏過電腦吧~"},
    {"type": "question", "question_id": "q2"},

    {"type": "dialogue", "text": "九點， __{name}__ 拖著疲憊的步伐回到了宿舍\n並在盥洗完成後早早的睡下了，也結束這充實的一天"},
    {"type": "dialogue", "text": "第二天課程："},
    {"type": "dialogue", "text": "一早就起床的 __{name}__ ，帶著愉快的心情去吃早餐，並期待著今天的課程......"},
    {"type": "dialogue", "text": "九點， __{name}__ 準時打卡進入教室，  早上的課程依舊是由三角蛇教授......"},
    {"type": "dialogue", "text": "課程過的很快，轉眼便到了下午下午的課程\n是由一位叫vincent的講師講解，內容是網頁安全的後端"},
    {"type": "dialogue", "text": "課程十分的困難，但認真的 __{name}__ 還是全部都學會了......\n今天學的內容主要是SQL Injection、XSS和CSRF等攻擊手法與防禦之道"},
    
    {"type": "quest", "quest_id": "q3", "title": "第三關：Burp Suite"},
    {"type": "dialogue", "text": "這是一個登入介面，要怎麼才能登入呢?(試著學會BURP爆破密碼功能吧)"},
    {"type": "question", "question_id": "q3"},

    {"type": "dialogue", "text": "晚上，則是最令 __{name}__ 期待的資安講座，講座開始前，有位自稱馮教授的講師也向 __{name}__ 推薦了一個社群——北台灣資訊社群"},
    {"type": "dialogue", "text": "於是，今晚的 __{name}__ 又又又加入了一個社群"},
    {"type": "dialogue", "text": "咳咳~說回正題這次的講座是請來奧義智慧的創辦人來對 __{name}__ 分享他的經歷，同時也告訴 __{name}__ 現在的AI發展趨勢， __{name}__ 受益良多......"},
    {"type": "dialogue", "text": "然而也就再這時，他收到了一個令人震驚的消息——颱風要來了，活動將提早結束了......"},
    {"type": "dialogue", "text": " __{name}__ 默默的走回宿舍，沉默是今晚的 __{name}__  __{name}__ 沮喪的回到了宿舍，準備洗洗睡了"},
    {"type": "dialogue", "text": "但是在被子蓋上的前一刻， __{name}__ 猛然想起......作業忘了寫了、專題也忘了討論了......"},
    
    {"type": "quest", "quest_id": "q4", "title": "第四關：Cookie"},
    {"type": "dialogue", "text": "現在你有帳號密碼了!那要怎麼拿到FLAG呢?(hint:decode,cookie)"},
    {"type": "question", "question_id": "q4"},

    {"type": "dialogue", "text": "於是他一個彈射起步，從這座歷史悠久的床上跳了下來開始做起今日的題目"},
    {"type": "dialogue", "text": "......." },
    {"type": "dialogue", "text": "第三天的陽光緩緩升起，正在夢中的黃金海岸看日出的 __{name}__ 也緩緩的醒來"},
    {"type": "dialogue", "text": "很快，今天的課程開始了，今天的課程主要是將網路後端的內容講完"},
    {"type": "dialogue", "text": "時間過的很快.......最後半天的課程都已經結束了中午的時間為作業時間， __{name}__ 也跟著大家一起做作業"},
    {"type": "dialogue", "text": "時間過的很快，眨眼就已經到了分別的時候儘管大家都很不捨，大家還是在收拾完行李後，各回各家......"},
    {"type": "dialogue", "text": "然而......事情遠沒有結束，因為還有個專題大魔王還沒做"},
    {"type": "dialogue", "text": "8/13.......熬夜中......"},
    
    {"type": "quest", "quest_id": "q5", "title": "第五關：XSS"},
    {"type": "dialogue", "text": "最後一關了！接觸JAVASCRIPT，了解如何注入網頁吧"},
    {"type": "question", "question_id": "q5"},

    {"type": "dialogue", "text": "8/14......熬夜中......."},
    {"type": "dialogue", "text": " __{name}__ 與組員僅趕慢趕終於將專題做完送出了!"},
    {"type": "dialogue", "text": "8/19____看著AIS3的貼文......"},
    {"type": "dialogue", "text": "......"},
    {"type": "dialogue", "text": "......"},
    {"type": "dialogue", "text": "最佳專題!"},
    {"type": "dialogue", "text": "恭喜你， __{name}__ ，你完成了所有挑戰！"},
    {"type": "end"}
]

# -----------------------------
# 狀態：用 session token 管理每個玩家
# -----------------------------
PROGRESS = {}           # token -> 故事索引
HINT_INDEX = {}         # (token, question_id) -> 已給的提示數量
sessions = {}
RETRY_LIMIT = 5

def get_token():
    #if 'token' not in session:
    #    session['token'] = secrets.token_hex(16)
    return secrets.token_hex(16)#session['token']

def get_session_id():
    return session.get("player_name")
    

def get_progress(token):
    return PROGRESS.get(token, 0)

def set_progress(token, idx):
    PROGRESS[token] = idx

def login_blocker(user_token="", RETRY_LIMIT=RETRY_LIMIT):
    def decorator(func):
        #token = request.headers.get("Authorization")
        token = user_token
        @lru_cache(maxsize=10)
        def counter(token, returnable=False):
            if not returnable:
                return -1
            return counter(token) + 1
            
        @wraps(func)
        def wrapper(*args, **kwargs):
            # token = session.get("username")
            token = user_token
            
            if not sessions.get(token) or not token:
                
                return jsonify({"error": "未授權"}), 403
                #pass
            retry_count = counter(token, True)
            if retry_count > RETRY_LIMIT:
                return jsonify({"error": "超過嘗試次數，請15分鐘後再試一次"}), 403
            return func(token)
        return wrapper
    return decorator

# -----------------------------
# 路由
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    token = get_token()
    #if token in sessions.keys():
    #    del sessions[token]
    #    del PROGRESS[token]
    sessions[token] = True
    # 允許重整後保持進度，第一次進來預設 0
    PROGRESS.setdefault(token, 0)
    # 如果是從名字輸入框提交的
    if request.method == "POST":
        player_name = request.form.get("name")
        if player_name:
            session['player_name'] = player_name
            # 重置進度，以免舊玩家換名字後進度錯亂
            set_progress(token, 0)
        # 重新導向回首頁，瀏覽器會用 GET 方法請求
        return redirect(url_for('index'))
    return render_template("index.html", token=token)

@app.route("/<path>/challenge/linux", methods=["GET"])
def linux(path: str):
    @login_blocker(user_token=path, RETRY_LIMIT=RETRY_LIMIT)
    def linux(path=path):
        return render_template("linuxCMD/index.html")
    return linux(path)

@app.route("/api/exec", methods=["POST"])
def api_exec():
    st = get_or_create_state()
    data = request.get_json(force=True, silent=True) or {}
    cmd = data.get("cmd", "")
    output = run_command(st, cmd)
    return jsonify({"output": output, "cwd": st["cwd"]})

@app.route("/api/reset", methods=["POST"])
def api_reset():
    st = get_or_create_state()
    sid = get_session_id()
    st["cwd"] = "/home/user"
    st["fs"] = build_initial_fs(seed=sid)
    return jsonify({"ok": True, "cwd": st["cwd"]})

# Q2 request
# 固定電腦贏的對應關係
win_map = {
    "rock": "paper",
    "paper": "scissors",
    "scissors": "rock"
}

@app.route("/<path>/challenge/request", methods=["GET", "POST"])
def req(path: str):
    @login_blocker(user_token=path, RETRY_LIMIT=RETRY_LIMIT)
    def request(path=path):
        return render_template("request.html", URLs=path)
    return request(path)

@app.route("/<path>/challenge/request/play", methods=["POST"])
def play(path: str):
    @login_blocker(user_token=path, RETRY_LIMIT=RETRY_LIMIT)
    def play(path=path):
        data = request.get_json()
        player_choice = data.get("player", "")
        
        # 隱藏後門：只有當 player_choice == "win" 才會讓玩家贏
        if player_choice == "win":
            return jsonify({
                "result": "You Win!",
                "flag": "FLAG{you_modified_the_request_body_successfully}"
            })
    
        # 一般情況下：電腦永遠贏
        if player_choice in win_map:
            computer_choice = win_map[player_choice]
            result = "You Lose!"
        else:
            computer_choice = random.choice(["rock", "paper", "scissors"])
            result = "Invalid Choice"
    
        return jsonify({
            "player": player_choice,
            "computer": computer_choice,
            "result": result
        })
    return play(path)

# Q3 
@app.route("/<path>/challenge/pwn", methods=["GET", "POST"])
def pwn(path: str):
    @login_blocker(user_token=path, RETRY_LIMIT=RETRY_LIMIT)
    def pwn(path=path):
        token = path.split("/")[0]
        if sessions.get(token):
            
            # sessions[token] = False
            #session['username'] = oken
            URL = get_token()
            sessions[URL] = True
            URL = f"/{URL}/pwn"
            return render_template("login.html")#, URLs=url_for(URL))

        else:
            return jsonify({"success": False}), 401
    return pwn(path)

# Q4
@app.route("/<path>/challenge/cookie", methods=["GET", "POST"])
def cookie(path: str):
    @login_blocker(user_token=path, RETRY_LIMIT=RETRY_LIMIT)
    def cookie(path=path):
        token = path.split("/")[0]
        if sessions.get(token):
            
            # sessions[token] = False
            #session['username'] = oken
            URL = get_token()
            sessions[URL] = True
            URL = f"/{URL}/cookie"
            URL = ""
            return render_template("login.html")#, URLs=URL)

        else:
            return jsonify({"success": False}), 401
    return cookie(path)

@app.route("/<URL>/login.php", methods=["POST"])
def random_route_login(URL: str):
    @login_blocker(user_token = URL, RETRY_LIMIT=RETRY_LIMIT)
    def random_route(URL=URL):
        # 根據 num 做一些隨機處理
        if request.method == "POST":
            if (URL.split("/")[-1] == "pwn" or URL.split("/")[-1] == "cookie") and URL:
                data = request.get_json()
                # username = data.get("username")
                # password = data.get("password")
                token = URL.split("/")[0]
                if sessions.get(token):
                    
                    sessions[token] = False
                    #session['username'] = oken
                    return render_template(f"/{URL.split('/')[-1]}/login.php")#jsonify({"success": True, "token": token})
                else:
                    return jsonify({"success": False}), 401 
    return random_route(URL)

@app.route("/<URL>/member.php", methods=["POST"])
def random_route_member(URL: str):
    @login_blocker(user_token = URL, RETRY_LIMIT=RETRY_LIMIT)
    def random_route(URL=URL):
        # 根據 num 做一些隨機處理
        if request.method == "POST":
            if URL.split("/")[-1] == "cookie" and URL:
                data = request.get_json()
                # username = data.get("username")
                # password = data.get("password")
                token = URL.split("/")[0]
                if sessions.get(token):
                    
                    sessions[token] = False
                    #session['username'] = oken
                    return render_template("/cookie/member.php")#jsonify({"success": True, "token": token})
                else:
                    return jsonify({"success": False}), 401 
    return random_route(URL)

# Q5
@app.route("/<path>/challenge/xss", methods=["GET", "POST"])
def xss(path: str):
    @login_blocker(user_token = URL, RETRY_LIMIT=RETRY_LIMIT)
    def xss(path=path):
        if request.method == "POST":
            note = request.form.get("note")
            note_id = uuid.uuid4().hex
            # --- 修改這裡，使用我們建立好的絕對路徑 ---
            note_path = os.path.join(NOTES_DIR, f"{note_id}.txt")
            with open(note_path, "w+") as f:
                f.write(note)
            return redirect(url_for("view_note", note_id=note_id))

        return render_template("xss/index.html")
    return xss(path)

@app.route("/note/<note_id>")
def view_note(note_id):
    # --- 修改這裡，使用我們建立好的絕對路徑 ---
    note_path = os.path.join(NOTES_DIR, f"{note_id}.txt")
    if not os.path.exists(note_path):
        return "Note not found", 404

    with open(note_path, "r") as f:
        note = f.read()
    return render_template("xss/note.html", note=note)

@app.route("/<path>/report", methods=["GET", "POST"])
def report(path: str):
    response = None
    if request.method == "POST":
        url = request.form["url"]
        pattern = "^http://" + request.host.replace(".", "\\.") + "/"
        print(f"{pattern=}")
        if not url or not re.match(pattern, url):
            return "Invalid URL", 400

        print(f"[+] Sending {url} to bot")

        try:
            client = socket.create_connection((BOT_HOST, BOT_PORT))
            client.sendall(url.encode())

            response = []
            while True:
                data = client.recv(1024)
                if not data:
                    break
                response.append(data.decode())
            client.close()
            return "".join(response)
        except Exception as e:
            print(e)
            return "Something is wrong...", 500
    return render_template("xss/report.html", response=response)

@app.route("/api/story/next", methods=["POST"])
def story_next():
    token = request.get_json() or {}
    token = token.get("token")#get_token()
    idx = get_progress(token)
    player_name = session.get('player_name', '挑戰者') # 從 session 獲取名字
    
    if idx >= len(STORY):
        return jsonify({"type": "end"})

    step = STORY[idx]
    
    if "text" in step:
        step["text"] = step["text"].replace("__{name}__", player_name)

    # 規則：遇到 question 不自動前進，等答對再往下
    if step["type"] == "question":
        return jsonify(step)

    # 其他類型：先回傳，再把進度 +1
    set_progress(token, idx + 1)
    return jsonify(step)

@app.route("/api/quest/<quest_id>", methods=["POST"])
def quest_detail(quest_id):
    token = request.get_json() or {}
    token = token.get("token")
    q = QUESTS.get(quest_id)
    if not q:
        return jsonify({"error": "題目不存在"}), 404
    return jsonify({
        "quest_id": quest_id,
        "title": q["title"],
        "intro": q["intro"],
        "goto_url": f"/{token}{q['goto_url']}"
    })

@app.route("/api/answer", methods=["POST"])
def submit_answer():
    token = get_token()
    data = request.get_json() or {}
    qid = data.get("question_id")
    ans = (data.get("answer") or "").strip()

    idx = get_progress(token)
    if idx >= len(STORY):
        return jsonify({"success": False, "message": "遊戲已結束。"})

    step = STORY[idx]
    if step.get("type") != "question" or step.get("question_id") != qid:
        return jsonify({"success": False, "message": "目前不在此題。"}), 400

    q = QUESTS.get(qid)
    if not q:
        return jsonify({"success": False, "message": "題目不存在。"}), 404

    if ans == q["answer"]:
        # 答對才推進劇情
        set_progress(token, idx + 1)
        return jsonify({"success": True, "message": "答案正確！繼續前進。"})
    else:
        return jsonify({"success": False, "message": "錯誤，繼續答題。"})

@app.route("/api/hint", methods=["POST"])
def get_hint():
    token = get_token()
    data = request.get_json() or {}
    qid = data.get("question_id")
    q = QUESTS.get(qid)
    if not q:
        return jsonify({"success": False, "message": "題目不存在。"}), 404

    key = (token, qid)
    used = HINT_INDEX.get(key, 0)
    hints = q.get("hints", [])
    if used >= len(hints):
        return jsonify({"success": True, "hint": "沒有更多提示了～"})

    hint = hints[used]
    HINT_INDEX[key] = used + 1
    return jsonify({"success": True, "hint": hint})

@app.route("/healthz")
def health():
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(debug=True)
