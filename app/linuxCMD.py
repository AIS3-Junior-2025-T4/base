from flask import session
import uuid, random, string
from typing import Dict, Any, Tuple, List

# ------------------ Virtual Filesystem ------------------
def make_dir(hidden: bool = False):
    return {"type": "dir", "children": {}, "hidden": hidden}

def make_file(content: str, hidden: bool = False):
    return {"type": "file", "content": content, "hidden": hidden}

# 小工具：隨機用的字與檔案
WORDS = ["alpha","beta","gamma","delta","omega","kappa","lambda","sigma",
         "zeta","theta","neon","ion","rust","bolt","spark","nimbus",
         "quark","pixel","nova","orbit"]

def rand_word(rng):
    return rng.choice(WORDS)

def rand_file(rng):
    name = rand_word(rng) + rng.choice([".txt",".md",".log",".cfg",".data",".bak"])
    text = rng.choice([
        "只是一般檔案。\n","與任務無關。\n","備忘錄。\n","雜項紀錄。\n","測試資料。\n"
    ])
    return name, text

def add_noise_dirs(rng, parent, depth=1, breadth=(2,5)):
    """建立隨機目錄與檔案增加干擾"""
    if depth <= 0:
        for _ in range(rng.randint(1,4)):
            n, t = rand_file(rng)
            parent["children"][n] = make_file(t)
        if rng.random() < 0.4:
            parent["children"]["."+rand_word(rng)] = make_file("隱藏檔案\n", hidden=True)
        return
    for _ in range(rng.randint(breadth[0], breadth[1])):
        dname = rand_word(rng)
        while dname in parent["children"]:
            dname += rng.choice(string.ascii_lowercase)
        parent["children"][dname] = make_dir()
        child = parent["children"][dname]
        for __ in range(rng.randint(0,3)):
            n, t = rand_file(rng)
            if n in child["children"]:
                n = "x_"+n
            child["children"][n] = make_file(t)
        if rng.random() < 0.35:
            hname = "." + rand_word(rng)
            child["children"][hname] = make_file("你看得見我嗎？\n", hidden=True)
        if rng.random() < 0.5:
            add_noise_dirs(rng, child, depth=depth-1, breadth=breadth)
def build_initial_fs(seed: str):
    rng = random.Random(seed)
    root = make_dir()

    # 固定核心骨架（任務仍然固定）
    root["children"][".hidden_dir"] = make_dir(hidden=True)
    # root["children"]["hint2"]  # 這行已移除，不再放在根目錄
    root["children"]["var"] = make_dir()
    root["children"]["home"] = make_dir()
    root["children"]["tmp"] = make_dir()
    root["children"]["etc"] = make_dir()
    root["children"]["challenge"] = make_dir()
    root["children"]["usr"] = make_dir()
    root["children"]["opt"] = make_dir()
    root["children"]["mnt"] = make_dir()
    root["children"]["sandbox"] = make_dir()

    # /var
    var = root["children"]["var"]
    var["children"]["ctf"] = make_dir()
    var["children"]["ctf"]["children"]["flag.txt"] = make_file("flag{linux_basics_ok}\n")
    var["children"]["log"] = make_dir()
    var["children"]["log"]["children"]["auth.log"] = make_file("[INFO] login ok\n")
    var["children"]["log"]["children"]["syslog"] = make_file("kernel: all good\n")
    var["children"]["spool"] = make_dir()

    # /etc
    etc = root["children"]["etc"]
    etc["children"]["hosts"] = make_file("127.0.0.1 localhost\n")
    etc["children"]["motd"] = make_file("歡迎來到練習環境！\n")
    etc["children"]["passwd"] = make_file("user:x:1000:1000::/home/user:/bin/bash\n")
    # 新位置：/etc/hints/hint2
    etc["children"]["hints"] = make_dir()
    etc["children"]["hints"]["children"]["hint2"] = make_file("flag 在 /var/ctf 路徑，檔名為 flag.txt\n")

    # /home/user
    home = root["children"]["home"]
    home["children"]["user"] = make_dir()
    user = home["children"]["user"]

    user["children"]["notes.txt"] = make_file("這裡沒有提示，但你可以使用 ls, cd, cat 試試看。\n")
    user["children"][".secret"] = make_file("你找到隱藏檔了！試試看 ls -a。\n", hidden=True)
    for sub in ["docs","downloads","projects","pictures","tasks"]:
        user["children"][sub] = make_dir()

    user["children"]["docs"]["children"]["todo.md"] = make_file("- 找到 hint1\n- 讀取 hint2\n")
    user["children"]["docs"]["children"]["linux-cheatsheet.txt"] = make_file("cd, ls -a, cat, rm\n")
    user["children"]["downloads"]["children"]["README.txt"] = make_file("檔案很多，小心有誘餌！\n")
    user["children"]["downloads"]["children"]["flag.png"] = make_file("(這只是圖檔名，沒有真 flag)\n")
    user["children"]["downloads"]["children"]["archive"] = make_dir()
    user["children"]["downloads"]["children"]["archive"]["children"]["old_hint.txt"] = make_file("假的提示。\n")
    user["children"]["projects"]["children"]["alpha"] = make_dir()
    user["children"]["projects"]["children"]["alpha"]["children"]["readme.md"] = make_file("alpha 專案筆記\n")
    user["children"]["projects"]["children"]["beta"] = make_dir()
    user["children"]["projects"]["children"]["beta"]["children"]["docs"] = make_dir()
    user["children"]["projects"]["children"]["beta"]["children"]["docs"]["children"]["design.md"] = make_file("設計草稿\n")
    user["children"]["projects"]["children"]["gamma"] = make_dir()
    user["children"]["projects"]["children"]["gamma"]["children"][".cache"] = make_dir(hidden=True)
    user["children"]["projects"]["children"]["gamma"]["children"][".cache"]["children"]["tmp.txt"] = make_file("隱藏快取\n", hidden=True)
    user["children"]["pictures"]["children"]["cats.txt"] = make_file("=^.^=\n")
    user["children"]["tasks"]["children"]["readme.md"] = make_file(
        "任務 1：在某個資料夾中找到名為 hint1 的提示。\n"
        "任務 2：根據提示找到最終 flag。\n"
    )

    # /sandbox
    sandbox = root["children"]["sandbox"]
    sandbox["children"]["practice.txt"] = make_file("這是練習用檔案。\n")
    sandbox["children"]["deep"] = make_dir()
    sandbox["children"]["deep"]["children"]["deeper"] = make_dir()
    sandbox["children"]["deep"]["children"]["deeper"]["children"]["readme.txt"] = make_file("越找越深，但沒有提示。\n")

    # /challenge（把 hint1 的內容改指向 /etc/hints）
    challenge = root["children"]["challenge"]
    challenge["children"]["folder1"] = make_dir()
    challenge["children"]["folder1"]["children"]["hint1"] = make_file("hint2 在 /etc/hints 中。\n")
    challenge["children"]["folder2"] = make_dir()
    challenge["children"]["folder2"]["children"]["hint1.bak"] = make_file("這是舊檔，無效。\n")
    challenge["children"]["folder3"] = make_dir()
    challenge["children"]["folder3"]["children"]["notes.txt"] = make_file("與任務無關的筆記。\n")
    challenge["children"]["misc"] = make_dir()
    challenge["children"]["misc"]["children"]["README"] = make_file("別被檔名騙了，真正的提示在 folder1。\n")

    # /usr, /opt, /mnt
    usr = root["children"]["usr"]
    usr["children"]["share"] = make_dir()
    usr["children"]["share"]["children"]["dict"] = make_dir()
    usr["children"]["share"]["children"]["dict"]["children"]["words.txt"] = make_file("alpha\nbeta\ngamma\n")
    usr["children"]["local"] = make_dir()
    usr["children"]["local"]["children"]["bin"] = make_dir()
    usr["children"]["local"]["children"]["bin"]["children"]["runme"] = make_file("（只是檔名，不可執行）\n")

    opt = root["children"]["opt"]
    opt["children"]["games"] = make_dir()
    opt["children"]["games"]["children"]["level1"] = make_dir()
    opt["children"]["games"]["children"]["level1"]["children"]["README.md"] = make_file("這裡沒有 hint。\n")
    opt["children"]["tools"] = make_dir()
    opt["children"]["tools"]["children"]["notes.txt"] = make_file("工具備忘。\n")

    mnt = root["children"]["mnt"]
    mnt["children"]["data"] = make_dir()
    mnt["children"]["data"]["children"]["sample.txt"] = make_file("mount 測試資料。\n")

    # 根目錄下的隱藏專區
    hidden_dir = root["children"][".hidden_dir"]
    hidden_dir["children"]["nothing.txt"] = make_file("你能用 ls -a 才看得到我。\n", hidden=True)
    hidden_dir["children"]["deep"] = make_dir(hidden=True)
    hidden_dir["children"]["deep"]["children"]["noway.txt"] = make_file("這裡也沒有提示。\n", hidden=True)

    # 在多個節點灑隨機雜訊
    noise_specs = [
        (user, 3, (2,5)),
        (challenge, 2, (2,5)),
        (usr, 2, (2,4)),
        (opt, 2, (2,4)),
        (mnt, 2, (2,4)),
        (sandbox, 2, (2,4)),
        (root, 2, (2,4)),
        (var, 1, (2,3)),
        (etc, 1, (1,2)),
    ]
    for base, depth, breadth in noise_specs:
        add_noise_dirs(rng, base, depth=depth, breadth=breadth)

    return root

# 依 session 維護每位玩家的檔案樹
SESSIONS: Dict[str, Dict[str, Any]] = {}

def get_session_id() -> str:
    return session.get("player_name")

def get_or_create_state() -> Dict[str, Any]:
    sid = get_session_id()
    if sid not in SESSIONS:
        SESSIONS[sid] = {"cwd": "/home/user", "fs": build_initial_fs(seed=sid)}
    return SESSIONS[sid]

# ------------------ Path Utilities ------------------
def split_path(p: str) -> List[str]:
    return [seg for seg in p.split("/") if seg not in ("", ".")]

def resolve_path(state: Dict[str, Any], path: str) -> Tuple[Dict[str, Any], str, Any]:
    fs = state["fs"]
    cwd = state["cwd"]
    if path.startswith("/"):
        parts = split_path(path)
    else:
        parts = split_path(cwd) + split_path(path)

    stack = []
    for seg in parts:
        if seg == "..":
            if stack: stack.pop()
        else:
            stack.append(seg)

    parent = fs
    node = fs
    name = "/"
    for seg in stack:
        if node["type"] != "dir":
            return (parent, seg, None)
        parent = node
        name = seg
        node = node["children"].get(seg)
        if node is None:
            return (parent, seg, None)
    return (parent, name, node)

def list_dir(node: Dict[str, Any], show_all: bool = False) -> List[str]:
    if node["type"] != "dir":
        return []
    names = []
    for name, child in node["children"].items():
        if not show_all and child.get("hidden"):
            continue
        names.append(name + ("/" if child["type"] == "dir" else ""))
    return sorted(names)

# ------------------ Command Handlers ------------------
def cmd_cwd(state, args):
    return state["cwd"] + "\n"

def cmd_ls(state, args):
    show_all = False
    target = state["cwd"]
    for a in args:
        if a == "-a":
            show_all = True
        elif a.startswith("-"):
            return f"ls: 不支援的參數 {a}\n"
        else:
            target = a
    parent, name, node = resolve_path(state, target)
    if node is None:
        return f"ls: 無此檔案或目錄: {target}\n"
    if node["type"] == "file":
        return name + "\n"
    out = list_dir(node, show_all=show_all)
    return "\n".join(out) + ("\n" if out else "")

def cmd_cd(state, args):
    target = "/" if not args else args[0]
    parent, name, node = resolve_path(state, target)
    if node is None or node["type"] != "dir":
        return f"cd: {target}: 不是目錄或不存在\n"
    if target.startswith("/"):
        parts = split_path(target)
    else:
        parts = split_path(state["cwd"]) + split_path(target)
    stack = []
    for seg in parts:
        if seg == "..":
            if stack: stack.pop()
        elif seg == ".":
            continue
        else:
            stack.append(seg)
    state["cwd"] = "/" + "/".join(stack)
    if state["cwd"] == "": state["cwd"] = "/"
    return ""

def cmd_cat(state, args):
    if not args:
        return "cat: 需要指定檔案\n"
    outputs = []
    for path in args:
        parent, name, node = resolve_path(state, path)
        if node is None or node["type"] != "file":
            outputs.append(f"cat: {path}: 無法開啟檔案\n")
        else:
            outputs.append(node["content"])
    return "".join(outputs)

PROTECTED_PATHS = {
    "/", "/var", "/var/ctf", "/var/log", "/home", "/home/user",
    "/challenge", "/challenge/folder1", "/etc", "/etc/hints", "/tmp", "/sandbox",
    "/usr", "/usr/share", "/usr/local", "/opt", "/mnt"
}

def canonical(state, path: str) -> str:
    if path.startswith("/"):
        parts = split_path(path)
    else:
        parts = split_path(state["cwd"]) + split_path(path)
    stack = []
    for seg in parts:
        if seg == "..":
            if stack: stack.pop()
        elif seg == ".":
            continue
        else:
            stack.append(seg)
    return "/" + "/".join(stack)

def cmd_rm(state, args):
    if not args:
        return "rm: 需要指定檔案\n"
    msgs = []
    for path in args:
        can = canonical(state, path)
        if can in PROTECTED_PATHS:
            msgs.append(f"rm: 無法刪除受保護的路徑: {path}\n")
            continue
        parent, name, node = resolve_path(state, path)
        if node is None:
            msgs.append(f"rm: 無此檔案或目錄: {path}\n")
            continue
        if node["type"] == "dir":
            msgs.append(f"rm: 無法刪除目錄: {path}\n")
            continue
        del parent["children"][name]
    return "".join(msgs)

def cmd_help(state, args):
    return (
        "支援的指令：\n"
        "  cwd                 顯示目前路徑\n"
        "  ls [-a] [DIR]       列出檔案與目錄，加上 -a 顯示隱藏項目\n"
        "  cd [DIR]            切換目錄（預設 / ）\n"
        "  cat FILE...         顯示檔案內容\n"
        "  rm FILE...          刪除檔案（部分路徑受保護）\n"
        "  help                顯示這個說明\n"
        "  reset               重置環境（會重新隨機產生迷宮）\n"
        "\n"
        "任務提示：\n"
        "  1) 找到名為 hint1 的提示。\n"
        "  3) 讀取 hint2 了解 flag 路徑並最終找到我們的flag。\n"
    )

COMMANDS = {
    "cwd": cmd_cwd,
    "ls": cmd_ls,
    "cd": cmd_cd,
    "cat": cmd_cat,
    "rm": cmd_rm,
    "help": cmd_help,
}

def run_command(state, line: str) -> str:
    line = line.strip()
    if not line:
        return ""
    if line == "reset":
        st = get_or_create_state()
        sid = get_session_id()
        st["cwd"] = "/home/user"
        st["fs"] = build_initial_fs(seed=sid)
        return "環境已重置（新的隨機檔案結構已生成）。\n"
    parts = line.split()
    cmd, args = parts[0], parts[1:]
    handler = COMMANDS.get(cmd)
    if handler is None:
        return f"{cmd}: 指令不支援（試試 help）\n"
    return handler(state, args)
