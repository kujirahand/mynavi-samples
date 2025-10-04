<?php
// index.php
require_once 'config.php';
require_once 'database.php';

// --- セッション管理 ---
session_name(SESSION_NAME);
session_start();

// --- CSRF対策 ---
if (empty($_SESSION['csrf_token'])) {
    $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
}
$csrf_token = $_SESSION['csrf_token'];

// --- 認証 ---
$is_logged_in = isset($_SESSION['is_logged_in']) && $_SESSION['is_logged_in'] === true;
$error_message = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['login'])) {
    if (isset($_POST['username'], $_POST['password']) &&
        $_POST['username'] === USER_NAME &&
        $_POST['password'] === PASSWORD) {
        $_SESSION['is_logged_in'] = true;
        header('Location: index.php');
        exit;
    } else {
        $error_message = 'ユーザー名またはパスワードが違います。';
    }
}

if (isset($_GET['action']) && $_GET['action'] === 'logout') {
    $_SESSION = [];
    session_destroy();
    header('Location: index.php');
    exit;
}

// ログインしていない場合はログインフォームを表示
if (!$is_logged_in) {
    // --- ログインフォームの表示 ---
    header('Content-Type: text/html; charset=utf-8');
?>
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>ログイン - My Notepad</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <h1>ログイン</h1>
        <?php if ($error_message): ?>
            <p class="error"><?php echo htmlspecialchars($error_message, ENT_QUOTES, 'UTF-8'); ?></p>
        <?php endif; ?>
        <form action="index.php" method="post">
            <div>
                <label for="username">ユーザー名:</label>
                <input type="text" id="username" name="username" required>
            </div>
            <div>
                <label for="password">パスワード:</label>
                <input type="password" id="password" name="password" required>
            </div>
            <div>
                <input type="submit" name="login" value="ログイン">
            </div>
        </form>
    </div>
</body>
</html>
<?php
    exit;
}

// --- アプリケーションロジック (ログイン後) ---

// アクションの決定
$action = $_GET['action'] ?? 'list'; // デフォルトは一覧表示

// データベース接続
$pdo = get_db_connection();

// --- 各アクションの処理 ---

// POSTリクエストの処理 (CSRF検証を含む)
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!isset($_POST['csrf_token']) || $_POST['csrf_token'] !== $_SESSION['csrf_token']) {
        die('CSRF token validation failed.');
    }

    $post_action = $_POST['action'] ?? 'list';

    if ($post_action === 'create') {
        $title = $_POST['title'] ?? '';
        $content = $_POST['content'] ?? '';
        if (!empty($title)) { // contentは空でも良い
            $stmt = $pdo->prepare("INSERT INTO notes (title, content, created_at, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)");
            $stmt->execute([$title, $content]);
        }
        header('Location: index.php');
        exit;
    } elseif ($post_action === 'update') {
        $id = $_POST['id'] ?? null;
        $title = $_POST['title'] ?? '';
        $content = $_POST['content'] ?? '';
        if ($id && !empty($title)) {
            $stmt = $pdo->prepare("UPDATE notes SET title = ?, content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?");
            $stmt->execute([$title, $content, $id]);
        }
        header('Location: index.php');
        exit;
    } elseif ($post_action === 'delete') {
        $id = $_POST['id'] ?? null;
        if ($id) {
            $stmt = $pdo->prepare("DELETE FROM notes WHERE id = ?");
            $stmt->execute([$id]);
        }
        header('Location: index.php');
        exit;
    } elseif ($post_action === 'upload') {
        if (isset($_FILES['image']) && $_FILES['image']['error'] === UPLOAD_ERR_OK) {
            $image = $_FILES['image'];
            $allowed_types = ['image/jpeg' => '.jpg', 'image/png' => '.png', 'image/gif' => '.gif'];
            $image_type = mime_content_type($image['tmp_name']);

            if (isset($allowed_types[$image_type])) {
                // 次のファイル番号を決定
                $files = glob('image/*.*');
                $max_num = 0;
                foreach ($files as $file) {
                    $basename = basename($file);
                    $num_str = preg_replace('/[^0-9]/', '', $basename);
                    if ($num_str !== '') {
                        $num = intval($num_str);
                        if ($num > $max_num) {
                            $max_num = $num;
                        }
                    }
                }
                $next_num = $max_num + 1;
                $new_filename = sprintf("%04d", $next_num) . $allowed_types[$image_type];
                $destination = __DIR__ . '/image/' . $new_filename;

                if (move_uploaded_file($image['tmp_name'], $destination)) {
                    // データベースにファイル名を保存
                    $stmt = $pdo->prepare("INSERT INTO images (filename) VALUES (?)");
                    $stmt->execute([$new_filename]);
                    $upload_message = 'アップロード成功！ Markdownリンク: `![画像](image/' . $new_filename . ')`';
                } else {
                    $upload_message = 'アップロードに失敗しました。ファイルの移動中にエラーが発生しました。';
                }
            } else {
                $upload_message = '許可されていないファイル形式です。(JPEG, PNG, GIFのみ)';
            }
        } else {
            $upload_message = 'アップロードエラーが発生しました。エラーコード: ' . ($_FILES['image']['error'] ?? 'Unknown');
        }
    }
}

// --- Markdown変換関数 ---
function convert_markdown_to_html($text) {
    $text = htmlspecialchars($text, ENT_QUOTES, 'UTF-8');
    // # 見出し
    $text = preg_replace('/^# (.*)$/m', '<h3>$1</h3>', $text);
    // 画像 ![text](url)
    $text = preg_replace('/\!\[(.*)\]\((.*)\)/U', '<img src="$2" alt="$1" style="max-width: 100%;">', $text);
    // リンク [text](url)
    $text = preg_replace('/\[(.*)\]\((.*)\)/U', '<a href="$2">$1</a>', $text);
    return nl2br($text, false);
}


// --- HTMLのレンダリング ---
?>
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>My Notepad</title>
    <link rel="stylesheet" href="style.css">
    <script>
        function confirmDelete() {
            return confirm('本当にこのメモを削除しますか？');
        }
    </script>
</head>
<body>
    <div class="container">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h1>My Notepad</h1>
            <a href="index.php?action=logout">ログアウト</a>
        </div>

        <div style="margin-bottom: 15px;">
            <a href="index.php?action=list">メモ一覧</a> |
            <a href="index.php?action=new">新しいメモを作成</a> |
            <a href="index.php?action=upload">画像をアップロード</a> |
            <a href="index.php?action=images">画像一覧</a>
        </div>

        <?php if ($action === 'new'): ?>
            <h2>新しいメモ</h2>
            <form action="index.php" method="post">
                <input type="hidden" name="action" value="create">
                <input type="hidden" name="csrf_token" value="<?php echo $csrf_token; ?>">
                <div>
                    <label for="title">タイトル:</label>
                    <input type="text" id="title" name="title" required>
                </div>
                <div>
                    <label for="content">内容 (Markdown対応):</label>
                    <textarea id="content" name="content" rows="10"></textarea>
                </div>
                <div>
                    <input type="submit" value="作成">
                </div>
            </form>
        <?php elseif ($action === 'edit'): ?>
            <h2>メモを編集</h2>
            <?php
            $id = $_GET['id'] ?? null;
            $note = null;
            if ($id) {
                $stmt = $pdo->prepare("SELECT * FROM notes WHERE id = ?");
                $stmt->execute([$id]);
                $note = $stmt->fetch();
            }
            if ($note):
            ?>
            <form action="index.php" method="post">
                <input type="hidden" name="action" value="update">
                <input type="hidden" name="id" value="<?php echo $note['id']; ?>">
                <input type="hidden" name="csrf_token" value="<?php echo $csrf_token; ?>">
                <div>
                    <label for="title">タイトル:</label>
                    <input type="text" id="title" name="title" value="<?php echo htmlspecialchars($note['title'], ENT_QUOTES, 'UTF-8'); ?>" required>
                </div>
                <div>
                    <label for="content">内容 (Markdown対応):</label>
                    <textarea id="content" name="content" rows="10"><?php echo htmlspecialchars($note['content'], ENT_QUOTES, 'UTF-8'); ?></textarea>
                </div>
                <div>
                    <input type="submit" value="更新">
                </div>
            </form>
            <?php else: ?>
                <p>編集するメモが見つかりません。</p>
            <?php endif; ?>
        <?php elseif ($action === 'upload'): ?>
            <h2>画像をアップロード</h2>
            <?php if (isset($upload_message)): ?>
                <p><?php echo htmlspecialchars($upload_message, ENT_QUOTES, 'UTF-8'); ?></p>
            <?php endif; ?>
            <form action="index.php?action=upload" method="post" enctype="multipart/form-data">
                <input type="hidden" name="action" value="upload">
                <input type="hidden" name="csrf_token" value="<?php echo $csrf_token; ?>">
                <div>
                    <label for="image">画像ファイル (JPEG, PNG, GIF):</label>
                    <input type="file" id="image" name="image" accept="image/jpeg,image/png,image/gif" required>
                </div>
                <div>
                    <input type="submit" value="アップロード">
                </div>
            </form>
        <?php elseif ($action === 'images'): ?>
            <h2>画像一覧</h2>
            <div class="image-gallery">
                <?php
                $stmt = $pdo->query("SELECT * FROM images ORDER BY uploaded_at DESC");
                $images = $stmt->fetchAll();
                if ($images):
                    foreach ($images as $image):
                        $image_path = 'image/' . $image['filename'];
                        $markdown_link = '![画像](' . $image_path . ')';
                ?>
                <div class="image-item">
                    <img src="<?php echo htmlspecialchars($image_path, ENT_QUOTES, 'UTF-8'); ?>" alt="<?php echo htmlspecialchars($image['filename'], ENT_QUOTES, 'UTF-8'); ?>">
                    <input type="text" value="<?php echo htmlspecialchars($markdown_link, ENT_QUOTES, 'UTF-8'); ?>" readonly>
                </div>
                <?php
                    endforeach;
                else:
                ?>
                    <p>アップロードされた画像はありません。</p>
                <?php endif; ?>
            </div>
        <?php else: // 'list' action ?>
            <h2>メモ一覧</h2>

            <!-- 検索・並び替えフォーム -->
            <form action="index.php" method="get" style="margin-bottom: 20px;">
                <input type="hidden" name="action" value="list">
                <input type="text" name="search" placeholder="検索キーワード" value="<?php echo htmlspecialchars($_GET['search'] ?? '', ENT_QUOTES, 'UTF-8'); ?>">
                <select name="sort">
                    <option value="updated_at" <?php if (($_GET['sort'] ?? 'updated_at') === 'updated_at') echo 'selected'; ?>>更新日時順</option>
                    <option value="created_at" <?php if (($_GET['sort'] ?? '') === 'created_at') echo 'selected'; ?>>作成日時順</option>
                </select>
                <input type="submit" value="検索・並び替え">
            </form>

            <?php
            $search = $_GET['search'] ?? '';
            $sort = $_GET['sort'] ?? 'updated_at';
            $sort_column = ($sort === 'created_at') ? 'created_at' : 'updated_at';

            $sql = "SELECT * FROM notes";
            $params = [];
            if (!empty($search)) {
                $sql .= " WHERE title LIKE ? OR content LIKE ?";
                $params[] = '%' . $search . '%';
                $params[] = '%' . $search . '%';
            }
            $sql .= " ORDER BY $sort_column DESC";

            $stmt = $pdo->prepare($sql);
            $stmt->execute($params);
            $notes = $stmt->fetchAll();

            if ($notes):
                foreach ($notes as $note):
            ?>
                <div class="note">
                    <h3><?php echo htmlspecialchars($note['title'], ENT_QUOTES, 'UTF-8'); ?></h3>
                    <div class="note-content">
                        <?php echo convert_markdown_to_html($note['content']); ?>
                    </div>
                    <p class="note-meta">
                        作成日時: <?php echo $note['created_at']; ?> |
                        更新日時: <?php echo $note['updated_at']; ?>
                    </p>
                    <a href="index.php?action=edit&id=<?php echo $note['id']; ?>">編集</a>
                    <form action="index.php" method="post" style="display: inline;" onsubmit="return confirmDelete();">
                        <input type="hidden" name="action" value="delete">
                        <input type="hidden" name="id" value="<?php echo $note['id']; ?>">
                        <input type="hidden" name="csrf_token" value="<?php echo $csrf_token; ?>">
                        <input type="submit" value="削除" style="background: #dc3545; color: white; border: none; padding: 5px 10px; cursor: pointer; border-radius: 3px;">
                    </form>
                </div>
            <?php
                endforeach;
            else:
            ?>
                <p>該当するメモはありません。</p>
            <?php endif; ?>
        <?php endif; ?>

    </div>
</body>
</html>
