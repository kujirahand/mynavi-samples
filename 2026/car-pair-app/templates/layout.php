<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Car Pairing App</title>
    <!-- Modern font -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="public/style.css">
</head>
<body>
    <div class="app-container">
        <?php if ($auth->isLoggedIn()): ?>
        <nav class="navbar">
            <div class="nav-brand">🚗 Car Pairing</div>
            <ul class="nav-links">
                <li><a href="?action=select_members" class="<?= $action === 'select_members' ? 'active' : '' ?>">配車する</a></li>
                <li><a href="?action=history" class="<?= $action === 'history' ? 'active' : '' ?>">履歴</a></li>
                <li><a href="?action=edit_list" class="<?= $action === 'edit_list' ? 'active' : '' ?>">名簿編集</a></li>
                <li><a href="?action=logout" class="logout-btn">ログアウト</a></li>
            </ul>
        </nav>
        <?php endif; ?>

        <main class="content-area">
            <?php if (isset($_SESSION['flash_message'])): ?>
                <div class="flash-message">
                    <?= htmlspecialchars($_SESSION['flash_message'], ENT_QUOTES, 'UTF-8') ?>
                </div>
                <?php unset($_SESSION['flash_message']); ?>
            <?php endif; ?>

            <?php
            if (isset($contentView) && file_exists(__DIR__ . '/' . $contentView)) {
                require __DIR__ . '/' . $contentView;
            }
            ?>
        </main>
    </div>
</body>
</html>
