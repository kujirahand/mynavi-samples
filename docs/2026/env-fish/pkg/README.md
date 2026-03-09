# 癒やしの水槽アプリ (Rust + WebAssembly)

魚の移動ロジックを Rust で計算し、WebAssembly 経由でブラウザ描画に反映する環境アプリです。

## 実装内容

- 背景画像 + 魚画像のレイヤー表示
- Rust 側で魚の位置・向き・速度を更新
- 1/fゆらぎ（ピンクノイズ近似）を使った自然な方向変化
- 気泡・微粒子の前景/背景レイヤー表現
- Web Audio API でホワイトノイズを生成し、控えめな水音に加工

## 必要ツール

- Rust (stable)
- [wasm-pack](https://rustwasm.github.io/wasm-pack/)
- 任意のローカルHTTPサーバー (`python3 -m http.server` など)

## 起動手順

1. Wasm ビルド

```bash
wasm-pack build --target web
```

2. ローカルサーバー起動（プロジェクトルート）

```bash
python3 -m http.server 8080
```

3. ブラウザで開く

```text
http://localhost:8080
```

## ファイル構成

- `src/lib.rs`: 魚のシミュレーション（Rust）
- `main.js`: Wasm呼び出し・描画更新・環境音
- `config.json`: 魚数、速度、環境音、植物モーションの設定
- `style.css`: 水槽UIスタイル
- `assets/*.svg`: 背景と魚画像

## 設定 (`config.json`)

- `fishCount`: メイン魚の数 (`3`〜`28`)
- `schoolFishCount`: 群れる小魚の数 (`0`〜`60`)
- `environmentSound.enabled`: 環境音のON/OFF
- `environmentSound.volume`: 環境音の音量 (`0`〜`0.12`)
- `speed.main`: メイン魚全体の速度倍率
- `speed.school`: 小魚群れの速度倍率
- `speed.round`: 丸い魚の速度倍率
- `speed.shark`: サメ型の速度倍率
- `speed.ray`: エイ型の速度倍率
- `visual.plantMotion`: 水草モーション倍率
