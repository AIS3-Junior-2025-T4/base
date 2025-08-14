<?php
header('Content-Type: text/html; charset=utf-8');

// 檢查是否有 sessionid 的 Cookie
if (!isset($_COOKIE['sessionid'])) {
    header("Location: login.html"); // 沒有 Cookie 就導回登入頁面
    exit();
}

// 解碼 Cookie 值
$username = base64_decode($_COOKIE['sessionid']);

// 根據使用者名稱顯示不同內容
echo "<h1>歡迎回來, " . htmlspecialchars($username) . "</h1>";
echo "<p>這是一個會員專屬的頁面。</p>";

if ($username === 'root') {
    echo "<h2>恭喜你！</h2>";
    echo "<p>你成功冒充了管理員！這是旗標：<b>flag{c00k13_h4ck_succc3ss}</b></p>";
}
?>