<div class="page-header">
    <h1 class="page-title">👥 今回の参加者を選択</h1>
</div>
<style>
.table tbody tr.selected-row {
    background-color: #eff6ff !important;
}
.table tbody tr.selected-row td {
    border-bottom-color: #bfdbfe;
}
</style>

<div class="card form-card">
    <?php if (!empty($error)): ?>
        <div class="alert alert-danger mb-4"><?= htmlspecialchars($error) ?></div>
    <?php endif; ?>

    <form action="?action=select_members" method="post" id="select-members-form">
        <div class="table-responsive">
            <table class="table hover-table">
                <thead>
                    <tr>
                        <th width="50" class="text-center">
                            <input type="checkbox" id="check-all" title="すべて選択">
                        </th>
                        <th class="sortable" data-sort="name" style="cursor: pointer; user-select: none;" title="クリックでソート">名前 <span class="sort-icon text-muted" style="font-size: 0.8em; margin-left: 4px;">↕</span></th>
                        <th>家族ID</th>
                        <th>タイプ</th>
                        <th class="sortable" data-sort="count" style="cursor: pointer; user-select: none;" title="クリックでソート">参加回数 <span class="sort-icon text-muted" style="font-size: 0.8em; margin-left: 4px;">↓</span></th>
                    </tr>
                </thead>
                <tbody>
                    <?php if (empty($members)): ?>
                    <tr><td colspan="5" class="text-center text-muted py-5">名簿がありません。「名簿編集」から登録してください。</td></tr>
                    <?php else: ?>
                    <?php foreach ($members as $m): ?>
                    <tr>
                        <td class="text-center checkbox-cell">
                            <input type="checkbox" name="selected_ids[]" value="<?= htmlspecialchars($m['id']) ?>" class="member-checkbox">
                        </td>
                        <td class="name-cell"><?= htmlspecialchars($m['name']) ?></td>
                        <td><span class="family-tag"><?= htmlspecialchars($m['family_id']) ?></span></td>
                        <td>
                            <?php if ($m['is_driver'] === '1'): ?>
                            <span class="badge-driver">🚗 ドライバー</span>
                            <?php else: ?>
                            <span class="badge-passenger">👤 乗客</span>
                            <?php endif; ?>
                            <span class="badge-gender-<?= strtolower($m['gender']) ?>">
                                <?= $m['gender'] === 'M' ? '男' : '女' ?>
                            </span>
                        </td>
                        <td class="count-val"><strong><?= htmlspecialchars($m['participation_count']) ?></strong> 回</td>
                    </tr>
                    <?php endforeach; ?>
                    <?php endif; ?>
                </tbody>
            </table>
        </div>
        
        <div class="form-actions sticky-actions">
            <div class="selection-summary">
                選択中: <span id="selected-count" class="badge">0</span> 人
            </div>
            <button type="submit" class="btn btn-primary btn-lg pulse-hover">乗りあわせを決定する ⚡</button>
        </div>
    </form>
</div>

<script>
document.addEventListener('DOMContentLoaded', () => {
    const checkAll = document.getElementById('check-all');
    const checkboxes = document.querySelectorAll('.member-checkbox');
    const countSpan = document.getElementById('selected-count');

    const updateCount = () => {
        const count = Array.from(checkboxes).filter(cb => {
            const tr = cb.closest('tr');
            if (cb.checked) {
                tr.classList.add('selected-row');
            } else {
                tr.classList.remove('selected-row');
            }
            return cb.checked;
        }).length;
        countSpan.textContent = count;
        countSpan.classList.toggle('active-count', count > 0);
    };

    if (checkAll) {
        checkAll.addEventListener('change', (e) => {
            checkboxes.forEach(cb => cb.checked = e.target.checked);
            updateCount();
        });
    }

    checkboxes.forEach(cb => {
        cb.addEventListener('change', updateCount);
        // Also toggle row selection style class
        cb.closest('tr').addEventListener('click', function(e) {
            if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'LABEL') {
                cb.checked = !cb.checked;
                updateCount();
            }
        });
    });

    // ソート機能
    const tableBody = document.querySelector('.hover-table tbody');
    const sortHeaders = document.querySelectorAll('.sortable');
    let currentSort = 'count';
    let currentDir = -1; // -1: 降順, 1: 昇順

    sortHeaders.forEach(th => {
        th.addEventListener('click', () => {
            const sortType = th.getAttribute('data-sort');
            if (currentSort === sortType) {
                currentDir *= -1; // 順序を反転
            } else {
                currentSort = sortType;
                currentDir = sortType === 'count' ? -1 : 1; // 回数は降順、名前は昇順がデフォルト
            }

            // アイコンの更新
            sortHeaders.forEach(header => {
                const icon = header.querySelector('.sort-icon');
                if (header.getAttribute('data-sort') === currentSort) {
                    icon.textContent = currentDir === 1 ? '↑' : '↓';
                } else {
                    icon.textContent = '↕';
                }
            });

            // 行のソート
            const rows = Array.from(tableBody.querySelectorAll('tr'));
            if (rows.length === 0 || rows[0].querySelector('td').colSpan > 1) return; // 空のデータ表示時はスキップ

            rows.sort((a, b) => {
                let valA, valB;
                if (currentSort === 'name') {
                    valA = a.querySelector('.name-cell').textContent.trim();
                    valB = b.querySelector('.name-cell').textContent.trim();
                    return valA.localeCompare(valB, 'ja') * currentDir;
                } else if (currentSort === 'count') {
                    valA = parseInt(a.querySelector('.count-val strong').textContent, 10) || 0;
                    valB = parseInt(b.querySelector('.count-val strong').textContent, 10) || 0;
                    if (valA === valB) {
                        const nameA = a.querySelector('.name-cell').textContent.trim();
                        const nameB = b.querySelector('.name-cell').textContent.trim();
                        return nameA.localeCompare(nameB, 'ja');
                    }
                    return (valA - valB) * currentDir;
                }
                return 0;
            });

            // DOMへ再配置
            rows.forEach(row => tableBody.appendChild(row));
        });
    });
});
</script>
