<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>領収書発行システム</title>
    <style>
        :root {
            --primary: #4f46e5;
            --bg: #f8fafc;
            --card: #ffffff;
            --text: #1e293b;
        }
        body {
            font-family: 'Helvetica Neue', Arial, 'Hiragino Kaku Gothic ProN', 'Hiragino Sans', Meiryo, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 2rem;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        .container {
            background: var(--card);
            padding: 2.5rem;
            border-radius: 1rem;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 500px;
        }
        h1 {
            font-size: 1.5rem;
            margin-bottom: 2rem;
            text-align: center;
            color: var(--primary);
        }
        .form-group {
            margin-bottom: 1.5rem;
        }
        label {
            display: block;
            font-size: 0.875rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        input, select {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid #e2e8f0;
            border-radius: 0.5rem;
            font-size: 1rem;
            box-sizing: border-box;
            transition: border-color 0.2s;
        }
        input:focus {
            outline: none;
            border-color: var(--primary);
            ring: 2px solid var(--primary);
        }
        button {
            width: 100%;
            padding: 1rem;
            background-color: var(--primary);
            color: white;
            border: none;
            border-radius: 0.5rem;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: background-color 0.2s, transform 0.1s;
        }
        button:hover {
            background-color: #4338ca;
        }
        button:active {
            transform: scale(0.98);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>領収書データ入力</h1>
        <form action="generate.php" method="POST">
            <div class="form-group">
                <label for="date">日付</label>
                <input type="date" id="date" name="date" value="<?php echo date('Y-m-d'); ?>" required>
            </div>
            <div class="form-group">
                <label for="address">宛名</label>
                <input type="text" id="address" name="address" placeholder="例：株式会社〇〇 御中" required>
            </div>
            <div class="form-group">
                <label for="amount">金額 (税込)</label>
                <input type="number" id="amount" name="amount" placeholder="例：11000" required>
            </div>
            <div class="form-group">
                <label for="proviso">但し書き</label>
                <input type="text" id="proviso" name="proviso" placeholder="例：お品代として" required>
            </div>
            <div class="form-group">
                <label for="tax_rate">税率</label>
                <select id="tax_rate" name="tax_rate">
                    <option value="10" selected>10%</option>
                    <option value="8">8%</option>
                </select>
            </div>
            <div class="form-group">
                <label for="password">パスワード</label>
                <input type="password" id="password" name="password" required>
            </div>
            <button type="submit">領収書を生成する</button>
        </form>
    </div>
</body>
</html>
