# run.py
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from flask_cors import CORS
from functools import lru_cache, wraps
import secrets
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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

def get_progress(token):
    return PROGRESS.get(token, 0)

def set_progress(token, idx):
    PROGRESS[token] = idx

def login_blocker(func, user_token="", RETRY_LIMIT=RETRY_LIMIT):
    #token = request.headers.get("Authorization")
    @lru_cache(maxsize=10)
    def counter(token, returnable=False):
        if not returnable:
            return -1
        return counter(token) + 1
        
    @wraps(func)
    def wrapper(*args, **kwargs):
        # token = session.get("username")
        token = user_token
        
        if not sessions.get(token, False) or not token:
            return jsonify({"error": "未授權"}), 403
            #pass
        retry_count = counter(token, True)
        if retry_count > RETRY_LIMIT:
            return jsonify({"error": "超過嘗試次數，請15分鐘後再試一次"}), 403
        return func(user_token)
    return wrapper


# -----------------------------
# 路由
# -----------------------------
@app.route("/", methods=["GET"])
def index():
    token = get_token()
    if token in sessions.keys():
        del sessions[token]
        del PROGRESS[token]
    sessions[token] = True
    # 允許重整後保持進度，第一次進來預設 0
    PROGRESS.setdefault(token, 0)
    return render_template("index.html", token=token)

# 固定電腦贏的對應關係
win_map = {
    "rock": "paper",
    "paper": "scissors",
    "scissors": "rock"
}

@app.route("/<path>/challenge/request")
def request(path: str):
    @login_blocker(path, RETRY_LIMIT=RETRY_LIMIT)
    def request(path=path):
        return render_template("request.html", URLs=path)
    return request

@app.route("/<path>/challenge/request/play", methods=["POST"])
def play(path: str):
    @login_blocker(path, RETRY_LIMIT=RETRY_LIMIT)
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
    return play

@app.route("/<path>/challenge/cookie", methods=["GET", "POST"])
def cookie(path: str):
    @login_blocker(path, RETRY_LIMIT=RETRY_LIMIT)
    def cookie(path=path):
        token = path.split("/")[0]
        if sessions.get(token):
            
            sessions[token] = False
            #session['username'] = oken
            URL = get_token()
            sessions[URL] = True
            URL = f"/{URL}/cookie"
            return render_template("login.html", URLs=url_for(URL))

        else:
            return jsonify({"success": False}), 401
    return cookie

@app.route("/<path>/challenge/pwn", methods=["GET", "POST"])
def pwn(path: str):
    @login_blocker(path, RETRY_LIMIT=RETRY_LIMIT)
    def pwn(path=path):
        token = path.split("/")[0]
        if sessions.get(token):
            
            sessions[token] = False
            #session['username'] = oken
            URL = get_token()
            sessions[URL] = True
            URL = f"/{URL}/pwn"
            return render_template("login.html", URLs=url_for(URL))

        else:
            return jsonify({"success": False}), 401
    return pwn

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
    return random_route

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
    return random_route

@app.route("/api/story/next", methods=["POST"])
def story_next():
    token = request.get_json()
    token = token.get("token")#get_token()
    idx = get_progress(token)

    if idx >= len(STORY):
        return jsonify({"type": "end"})

    step = STORY[idx]

    # 規則：遇到 question 不自動前進，等答對再往下
    if step["type"] == "question":
        return jsonify(step)

    # 其他類型：先回傳，再把進度 +1
    set_progress(token, idx + 1)
    return jsonify(step)

@app.route("/api/quest/<quest_id>", methods=["POST"])
def quest_detail(quest_id):
    token = request.get_json()
    token = token.get("token")
    q = QUESTS.get(quest_id)
    if not q:
        return jsonify({"error": "題目不存在"}), 404
    return jsonify({
        "quest_id": quest_id,
        "title": q["title"],
        "intro": q["intro"],
        "goto_url": f"/{token}/{q['goto_url']}"
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
