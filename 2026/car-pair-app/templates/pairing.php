<div class="page-header justify-between">
    <h1 class="page-title">✨ 乗りあわせ候補</h1>
    
    <div class="action-buttons header-actions">
        <a href="?action=pairing" class="btn btn-outline">🔄 もう一回</a>
        <?php if (!isset($result['error'])): ?>
        <form action="?action=pairing" method="post" style="margin:0">
            <input type="hidden" name="pairing_result" value="<?= htmlspecialchars(json_encode($result['cars'])) ?>">
            <button type="submit" name="decide" class="btn btn-success">✅ この組合せで決定</button>
        </form>
        <?php endif; ?>
    </div>
</div>

<?php if (isset($result['error'])): ?>
    <div class="card error-card">
        <div class="alert alert-danger" style="margin-bottom:0">
            <strong>エラー:</strong> <?= htmlspecialchars($result['error']) ?>
        </div>
        <div class="text-center mt-4">
            <a href="?action=select_members" class="btn btn-primary">戻って選択し直す</a>
        </div>
    </div>
<?php else: ?>
    
    <div class="alert alert-info">
        <strong>スコア (履歴重複度):</strong> <?= $result['score'] ?> （小さいほど良い組合せです）
        <span class="float-right text-muted" style="float: right; font-size: 0.85em;">処理時間: <strong><?= $executionTime ?></strong> ms</span>
    </div>

    <div class="cars-grid">
        <?php $carIndex = 1; ?>
        <?php foreach ($result['cars'] as $car): ?>
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

    <!-- Bottom Actions -->
    <div class="bottom-actions mt-5 text-center">
        <a href="?action=pairing" class="btn btn-outline btn-lg mr-3">🔄 もう一回</a>
        <form action="?action=pairing" method="post" class="inline-block">
            <input type="hidden" name="pairing_result" value="<?= htmlspecialchars(json_encode($result['cars'])) ?>">
            <button type="submit" name="decide" class="btn btn-success btn-lg shadow-hover">✅ この組合せで決定</button>
        </form>
    </div>

<?php endif; ?>
