<div class="login-container">
    <div class="card login-card">
        <h2 class="card-title text-center">🔐 管理者ログイン</h2>
        <?php if (!empty($error)): ?>
            <div class="alert alert-danger"><?= htmlspecialchars($error) ?></div>
        <?php endif; ?>
        <form action="?action=login" method="post" class="stack">
            <div class="form-group">
                <label for="username">ユーザー名</label>
                <input type="text" name="username" id="username" class="form-control" required autofocus>
            </div>
            <div class="form-group">
                <label for="password">パスワード</label>
                <input type="password" name="password" id="password" class="form-control" required>
            </div>
            <button type="submit" class="btn btn-primary btn-block btn-lg">ログイン</button>
        </form>
    </div>
</div>
