<div class="page-header justify-between">
    <h1 class="page-title">📜 ご利用履歴</h1>
    <a href="?action=select_members" class="btn btn-primary">新しく配車する</a>
</div>

<?php if (empty($latest)): ?>
    <div class="card text-center text-muted py-5">
        <p>履歴はまだありません。</p>
        <a href="?action=select_members" class="btn btn-primary mt-4">新しく配車を開始する</a>
    </div>
<?php else: ?>

    <div class="card mb-4" style="background:#f8fafc; border: 2px solid var(--primary);">
        <h2 class="card-title" style="margin-bottom:0.5rem; color: var(--primary);">🎉 最新の組合せ</h2>
        <p class="text-muted mb-4">保存日時: <?= htmlspecialchars($latest['date']) ?></p>

        <div class="cars-grid">
            <?php $carIndex = 1; ?>
            <?php foreach ($latest['cars'] as $car): ?>
            <div class="car-card">
                <div class="car-header">
                    <h3>🚗 車 <?= $carIndex++ ?></h3>
                    <span class="badge"><?= count($car) ?>人</span>
                </div>
                <ul class="passenger-list">
                    <?php foreach ($car as $p): ?>
                    <li class="<?= $p['is_driver'] === '1' ? 'is-driver' : 'is-passenger' ?>">
                        <div class="passenger-info">
                            <strong><?= htmlspecialchars($p['name']) ?></strong>
                            <div class="passenger-meta">
                                <span class="family-tag float"><?= htmlspecialchars($p['family_id']) ?></span>
                                <?= $p['gender'] === 'M' ? '<span class="gender-m">♂</span>' : '<span class="gender-f">♀</span>' ?>
                            </div>
                        </div>
                        <?php if ($p['is_driver'] === '1'): ?>
                            <span class="driver-icon" title="ドライバー">🔑</span>
                        <?php endif; ?>
                    </li>
                    <?php endforeach; ?>
                </ul>
            </div>
            <?php endforeach; ?>
        </div>
    </div>

    <?php if (!empty($pastHistories)): ?>
        <h3 class="mt-5 mb-4">過去の組合せ (直近5件)</h3>
        <div class="stack">
            <?php foreach ($pastHistories as $history): ?>
                <div class="card" style="padding: 1.5rem;">
                    <h4 style="margin-bottom: 1rem; color: #475569;">🕒 <?= htmlspecialchars($history['date']) ?></h4>
                    <ul style="list-style-type: disc; margin-left: 1.5rem; color: var(--text-main); font-size: 0.95rem;">
                        <?php foreach ($history['cars'] as $i => $car): ?>
                            <li style="margin-bottom: 0.5rem;">
                                <strong>車 <?= $i + 1 ?>:</strong> 
                                <?= implode('、', array_map(function($p) {
                                    return htmlspecialchars($p['name']) . ($p['is_driver'] === '1' ? ' (🔑)' : '');
                                }, $car)) ?>
                            </li>
                        <?php endforeach; ?>
                    </ul>
                </div>
            <?php endforeach; ?>
        </div>
    <?php endif; ?>

<?php endif; ?>
