# web-app

リバーシAIをWebAssemblyで動かすWebアプリです。
[こちら](https://kujirahand.github.io/mynavi-samples/2026/reversi/index.html)から、実際にリバーシを遊ぶことができます。


## ビルド方法

初回だけ `wasm-pack` をインストールします。

```bash
cargo install wasm-pack
```

```bash
wasm-pack build --target web --out-dir public/pkg
cargo run
```

ブラウザで次のURLを開きます。

```text
http://127.0.0.1:7878
```

## 確認

```bash
cargo check
cargo test
```
