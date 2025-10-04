<?php
// database.php
require_once 'config.php';

function get_db_connection() {
    try {
        $pdo = new PDO('sqlite:' . DB_PATH);
        $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
        return $pdo;
    } catch (PDOException $e) {
        die("データベース接続に失敗しました: " . $e->getMessage());
    }
}

function initialize_database() {
    $schema_path = __DIR__ . '/data/schema.sql';
    if (!file_exists(DB_PATH) || filesize(DB_PATH) === 0) {
        if (file_exists($schema_path)) {
            $pdo = get_db_connection();
            $sql = file_get_contents($schema_path);
            $pdo->exec($sql);
        }
    }
}

// データベースの初期化を実行
initialize_database();
