# rust-reversi

リバーシの作り方を解説します。

```text
├── human-vs-human ---- 人間 vs 人間 リバーシのルールを実装しただけ
│   ├── src
├── human-vs-ai --- 簡単なAI対戦を実装したもの
│   └── src
├── negamax-ai --- negamax探索を利用したもの
│   └── src
└── web-app --- リバーシをWebアプリにしたもの
    ├── Makefile  --- 手軽にビルドするためのMakefile
    ├── public --- HTMLとWebAssembly
    └── src --- Rustのコード
```

