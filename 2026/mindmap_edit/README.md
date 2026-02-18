# AI対応のマインドマップエディタ

実行には、Pythonが必要です。
ターミナルを起動して、次のコマンドを一つずつ実行しましょう。

```bash
# アプリの起動手順(デスクトップに配置した場合)
cd ~/Desktop/MindmapEdit
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

アプリの実行にはOpenAIのAPIを利用します。OpenAIのAPIキーが必要になります。OpenAIの[開発者サイト](https://platform.openai.com/api-keys)からAPIキーを取得して環境変数へ登録しましょう。

具体的な取得方法や設定方法は、本連載の[14回目](https://news.mynavi.jp/techplus/article/zerovibecoding-14/)をご覧ください。

そして、ブラウザで「http://127.0.0.1:5000」にアクセスしましょう。すると、テーマを入力するテキストボックスが表示されます。テーマを入力してEnterキーを押すと、ChatGPTのAPIにリクエストが送信され、関連するアイデアがマインドマップとして表示されます。

