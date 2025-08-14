<?php
header('Content-Type: text/html; charset=utf-8');

$users = [
    'admin' => 'password123',
    'root'  => 'supersecretpassword' // 這個帳號的密碼你不需要給使用者
];

if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $username = $_POST['username'];
    $password = $_POST['password'];

    if (isset($users[$username]) && $users[$username] === $password) {
        // 成功登入
        // 使用 Base64 編碼使用者名稱，並設定為 Cookie
        setcookie('sessionid', base64_encode($username), time() + 3600, "/");
        header("Location: member.php"); // 導向會員頁面
        exit();
    } else {
        echo "<h1>登入失敗！</h1><p>帳號或密碼錯誤，請再試一次。</p>";
    }
}
?>