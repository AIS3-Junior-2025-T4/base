# run.py
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
from functools import wraps
import secrets
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'app', 'templates'),
    static_folder=os.path.join(BASE_DIR, 'app', 'static'),
)

CORS(app)
app.config['SECRET_KEY'] = os.urandom(16)

# (你的劇情發想和 QUESTS 資料庫保持不變)
# ...
# 劇情發想：
# ...
# 題目資料庫：介紹、前往網址、正確答案與提示
QUESTS = {
    "q1": {
        "title": "第一關：Linux",
        "intro": "找出FLAG & 熟悉LINUX指令",
        "goto_url": "http://xss.ais3.club:10000/",  # TODO: 換成你的實際路徑或外部題目網址
        "answer": "flag{linux_basics_ok}",
        "hints": [
        ]
    },
    "q2": {
        "title": "第二關：Request",
        "intro": "BURP入門，想辦法猜拳營電腦吧~",
        "goto_url": "http://xss.ais3.club:20000/",  # TODO: 換成你的實際路徑或外部題目網址
        "answer": "FLAG{you_modified_the_request_body_successfully}",
        "hints": [
        ]
    },
    "q3": {
        "title": "第三關：Burp Suite",
        "intro": "這是一個登入介面，要怎麼才能登入呢?(學會BURP爆破密碼功能)",
        "goto_url": "http://xss.ais3.club:30000/",  # TODO: 換成你的實際路徑或外部題目網址
        "answer": "flag{easy_brute_force}<",
        "hints": [
        ]
    },
    "q4": {
        "title": "第四關：Cookie",
        "intro": "現在你有帳號密碼了!那要怎麼拿到FLAG呢?(hint:decode,cookie)",
        "goto_url": "http://xss.ais3.club:40000/login.html",  # TODO: 換成你的實際路徑或外部題目網址
        "answer": "flag{c00k13_h4ck_succc3ss}",
        "hints": [
        ]
    },
    "q5": {
        "title": "第五關：XSS",
        "intro": "接觸JAVASCRIPT，了解如何注入網頁",
        "goto_url": "/challenge/pwn",  # TODO: 換成你的實際路徑或外部題目網址
        "answer": "flag{wow_you_are_going_to_win}",
        "hints": [
        ]
    }
}
# 劇情資料庫
STORY = [
    {"type": "dialogue","text": "歡迎來到這次的AIS3 junior的營隊, {name}！"},
    {"type": "dialogue","text": "在這次營隊中，我們將會學到許多有關網路安全前後端的技術。"},
    {"type": "dialogue","text": "你準備接受挑戰了嗎?"},
    {"type": "quest", "quest_id": "q1"},
    {"type": "question", "question_id": "q1"},
    {"type": "dialogue", "text": "做得好！接下來會更困難。"},
    {"type": "quest", "quest_id": "q2"},
    {"type": "question", "question_id": "q2"},
    {"type": "dialogue","text": "恭喜你，{name}，你完成了所有挑戰！"},
    {"type": "end"}
]


# -----------------------------
# 狀態：用 session token 管理每個玩家
# -----------------------------
PROGRESS = {}           # token -> 故事索引
HINT_INDEX = {}         # (token, question_id) -> 已給的提示數量

def get_token():
    if 'token' not in session:
        session['token'] = secrets.token_hex(16)
    return session['token']

def get_progress(token):
    return PROGRESS.get(token, 0)

def set_progress(token, idx):
    PROGRESS[token] = idx

# -----------------------------
# 路由
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    token = get_token()
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

    # 一般 GET 請求，直接渲染頁面
    # 模板可以透過 session.player_name 判斷是否已輸入名字
    return render_template("index.html", token=token)

@app.route("/api/story/next", methods=["POST"])
def story_next():
    token = get_token()
    player_name = session.get('player_name', '挑戰者') # 從 session 獲取名字
    idx = get_progress(token)

    if idx >= len(STORY):
        return jsonify({"type": "end"})

    step = STORY[idx].copy() # 使用 .copy() 避免修改原始 STORY 列表

    # **核心邏輯：替換劇情中的 {name}**
    if "text" in step:
        step["text"] = step["text"].replace("{name}", player_name)

    if step["type"] == "question":
        return jsonify(step)

    set_progress(token, idx + 1)
    return jsonify(step)

# 其他 API 路由 (/api/quest/<quest_id>, /api/answer, /api/hint, /healthz) 保持不變
@app.route("/api/quest/<quest_id>", methods=["GET"])
def quest_detail(quest_id):
    q = QUESTS.get(quest_id)
    if not q:
        return jsonify({"error": "題目不存在"}), 404
    return jsonify({
        "quest_id": quest_id,
        "title": q["title"],
        "intro": q["intro"],
        "goto_url": q["goto_url"]
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