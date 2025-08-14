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
        "answer": "flag{easy_brute_force}",
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
        "goto_url": "http://xss.ais3.club:50000/",  # TODO: 換成你的實際路徑或外部題目網址
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

    # **核心邏輯：替換劇情中的 __{name}__**
    if "text" in step:
        step["text"] = step["text"].replace("_{name}_", player_name)

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
        return jsonify({"success": False, "message": "遊戲已結束"})

    step = STORY[idx]
    if step.get("type") != "question" or step.get("question_id") != qid:
        return jsonify({"success": False, "message": "目前不在此題"}), 400

    q = QUESTS.get(qid)
    if not q:
        return jsonify({"success": False, "message": "題目不存在"}), 404

    if ans == q["answer"]:
        set_progress(token, idx + 1)
        return jsonify({"success": True, "message": "答案正確！繼續前進"})
    else:
        return jsonify({"success": False, "message": "錯誤，繼續答題"})

@app.route("/api/hint", methods=["POST"])
def get_hint():
    token = get_token()
    data = request.get_json() or {}
    qid = data.get("question_id")
    q = QUESTS.get(qid)
    if not q:
        return jsonify({"success": False, "message": "題目不存在"}), 404

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