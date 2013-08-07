<?php

// Authenticate first
if (!isset($_REQUEST['login']) || !isset($_REQUEST['password'])) {
    echo "<form method=\"post\" action=\"\">\n";
    echo "Login: <input type=\"text\" name=\"login\" value=\"\" /><br />\n";
    echo "Password: <input type=\"password\" name=\"password\" value=\"\" /><br />\n";
    echo "<input type=\"submit\" value=\"login\" />\n";
    echo "</form>\n";
    exit;
} else {
    $passwd = json_decode(file_get_contents('.passwd'), true);
    if (!is_array($passwd)) {
        echo '<html><body>Authentication error</body></html>';
        exit;
    }
    if (!in_array(array($_REQUEST['login'] => sha1($_REQUEST['password'])), $passwd)) {
        setcookie('login', '');
        setcookie('password', '');
        echo '<html><body>Invalid login</body></html>';
        exit;
    }
    setcookie('login', $_REQUEST['login']);
    setcookie('password', $_REQUEST['password']);
}
