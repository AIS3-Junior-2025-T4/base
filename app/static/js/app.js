async function postJSON(url, data) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

const term = document.getElementById("terminal");
const form = document.getElementById("cmdForm");
const input = document.getElementById("cmdInput");
const cwdEl = document.getElementById("cwd");
const resetBtn = document.getElementById("resetBtn");

function appendLine(text, cls = "output") {
  const p = document.createElement("div");
  p.className = `line ${cls}`;
  p.textContent = text;
  term.appendChild(p);
  term.scrollTop = term.scrollHeight;
}

function appendPrompt(cmd) {
  appendLine(`$ ${cmd}`, "prompt");
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const cmd = input.value.trim();
  if (!cmd) return;
  appendPrompt(cmd);
  input.value = "";
  try {
    const data = await postJSON("/api/exec", { cmd });
    if (data.output) appendLine(data.output);
    if (data.cwd) cwdEl.textContent = data.cwd;
  } catch (err) {
    appendLine("連線失敗，請稍後再試。", "error");
  }
});

resetBtn.addEventListener("click", async () => {
  try {
    const data = await postJSON("/api/reset", {});
    appendLine("環境已重置。");
    cwdEl.textContent = data.cwd || "/";
  } catch {
    appendLine("重置失敗。", "error");
  }
});

// Welcome banner
appendLine("歡迎來到 Linux 指令練習環境！輸入 help 查看可用指令。");
