<div class="page-header">
    <h1 class="page-title">📝 名簿マスター編集</h1>
</div>

<div class="grid layout-grid">
    <div class="card edit-form-card">
        <h3 class="card-title">新規追加</h3>
        <form action="?action=edit_list" method="post" class="stack form-inline-custom">
            <div class="form-group">
                <label>名前</label>
                <input type="text" name="name" class="form-control" required placeholder="例: 山田太郎">
            </div>
            <div class="form-group">
                <label>家族ID</label>
                <input type="text" name="family_id" class="form-control" required placeholder="例: F01">
            </div>
            <div class="form-group">
                <label>性別</label>
                <select name="gender" class="form-control">
                    <option value="M">男性</option>
                    <option value="F">女性</option>
                </select>
            </div>
            <div class="form-group checkbox-group">
                <label>
                    <input type="checkbox" name="is_driver" value="1">
                    ドライバー
                </label>
            </div>
            <button type="submit" name="add" class="btn btn-primary" style="margin-top: 1.5rem;">登録する</button>
        </form>
    </div>

    <div class="card table-card list-card">
        <h3 class="card-title">現在の名簿 <span class="badge"><?= count($members) ?> 名</span></h3>
        <div class="table-responsive">
            <table class="table">
                <thead>
                    <tr>
                        <th>名前</th>
                        <th>家族ID</th>
                        <th>性別</th>
                        <th>ドライバー</th>
                        <th>参加回数</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    <?php if (empty($members)): ?>
                    <tr><td colspan="6" class="text-center text-muted">データがありません。</td></tr>
                    <?php else: ?>
                    <?php foreach ($members as $m): ?>
                    <tr>
                        <td><?= htmlspecialchars($m['name']) ?></td>
                        <td><span class="family-tag"><?= htmlspecialchars($m['family_id']) ?></span></td>
                        <td><?= $m['gender'] === 'M' ? '<span class="gender-m">男性</span>' : '<span class="gender-f">女性</span>' ?></td>
                        <td><?= $m['is_driver'] === '1' ? '🚗' : '-' ?></td>
                        <td><?= htmlspecialchars($m['participation_count']) ?> 回</td>
                        <td class="action-cell">
                            <form action="?action=edit_list" method="post" style="display:inline;" onsubmit="return confirm('本当に削除しますか？');">
                                <input type="hidden" name="id" value="<?= htmlspecialchars($m['id']) ?>">
                                <button type="submit" name="delete" class="btn btn-sm btn-danger">削除</button>
                            </form>
                        </td>
                    </tr>
                    <?php endforeach; ?>
                    <?php endif; ?>
                </tbody>
            </table>
        </div>
    </div>
</div>
