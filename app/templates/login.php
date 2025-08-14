<?php
$correct_username = "admin";
$correct_password = "password123";
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $username = $_POST['username'];
    $password = $_POST['password'];
    if ($username === $correct_username && $password === $correct_password) {
        echo "<h1>登入成功！</h1>";
        echo "<p>恭喜你！這是你的旗標：<b>flag{easy_brute_force}</b></p>";
    } else {
        echo "<h1>登入失敗！</h1>";
        echo "<p>帳號或密碼錯誤，請再試一次。</p>";
    }
}

?>
