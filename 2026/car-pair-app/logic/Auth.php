<?php
class Auth {
    private $adminFile;

    public function __construct($adminFile = null) {
        if ($adminFile === null) {
            $adminFile = __DIR__ . '/../data/admin.json';
        }
        $this->adminFile = $adminFile;
    }

    public function login($username, $password) {
        if (!file_exists($this->adminFile)) {
            return false;
        }

        $json = file_get_contents($this->adminFile);
        $admins = json_decode($json, true);

        if (isset($admins[$username]) && $admins[$username] === $password) {
            $_SESSION['logged_in'] = true;
            $_SESSION['username'] = $username;
            return true;
        }

        return false;
    }

    public function logout() {
        unset($_SESSION['logged_in']);
        unset($_SESSION['username']);
        session_destroy();
    }

    public function isLoggedIn() {
        return isset($_SESSION['logged_in']) && $_SESSION['logged_in'] === true;
    }
}
