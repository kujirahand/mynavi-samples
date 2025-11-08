from flask import Flask, render_template, request, redirect, url_for, session
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)
DATA_DIR = 'data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# パスワードからキーを生成する関数
def get_key(password, salt):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key

# 暗号化関数
def encrypt_data(data, password):
    salt = os.urandom(16)
    key = get_key(password, salt)
    f = Fernet(key)
    encrypted_data = f.encrypt(json.dumps(data).encode())
    return salt + encrypted_data

# 復号関数
def decrypt_data(encrypted_data_with_salt, password):
    try:
        salt = encrypted_data_with_salt[:16]
        encrypted_data = encrypted_data_with_salt[16:]
        key = get_key(password, salt)
        f = Fernet(key)
        decrypted_data = f.decrypt(encrypted_data)
        return json.loads(decrypted_data.decode())
    except Exception:
        return None

# すべての日記ファイルのパスを取得するヘルパー関数
def get_all_diary_files():
    all_files = []
    for root, _, files in os.walk(DATA_DIR):
        for file in files:
            if file.endswith('.encrypted'):
                all_files.append(os.path.join(root, file))
    return all_files

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = request.args.get('error')
    if request.method == 'POST':
        password = request.form['password']
        
        all_diary_files = get_all_diary_files()
        
        if all_diary_files:
            try:
                # 最新のファイルで試す
                latest_file = max(all_diary_files, key=os.path.getctime)
                with open(latest_file, 'rb') as f:
                    encrypted_data = f.read()
                if decrypt_data(encrypted_data, password) is not None:
                    session['password'] = password
                    return redirect(url_for('index'))
                else:
                    return render_template('login.html', error='パスワードが間違っています。')
            except Exception:
                 return render_template('login.html', error='パスワードの検証中にエラーが発生しました。')
        # 日記がまだない場合は、どんなパスワードでも受け入れる
        session['password'] = password
        return redirect(url_for('index'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('password', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'password' not in session:
        return redirect(url_for('login'))

    password = session['password']
    diaries = []
    
    # 年のリストを取得
    try:
        years = sorted([d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))], reverse=True)
    except FileNotFoundError:
        years = []

    selected_year = request.args.get('year')
    display_title = ""

    try:
        all_diary_files = get_all_diary_files()
        
        if selected_year:
            # 年が指定されている場合、その年のファイルのみを対象にする
            display_title = f"{selected_year}年の日記"
            target_files = [f for f in all_diary_files if f.startswith(os.path.join(DATA_DIR, selected_year))]
            sorted_files = sorted(target_files, key=os.path.getctime, reverse=True)
        else:
            # 年が指定されていない場合、最新30件を表示
            display_title = "最新30件の日記"
            sorted_files = sorted(all_diary_files, key=os.path.getctime, reverse=True)
            sorted_files = sorted_files[:30]

        for filename in sorted_files:
            with open(filename, 'rb') as f:
                encrypted_data = f.read()
            decrypted_data = decrypt_data(encrypted_data, password)
            if decrypted_data:
                # IDとしてdataディレクトリからの相対パスを使用
                diary_id = os.path.relpath(filename, DATA_DIR)
                diaries.append({'data': decrypted_data, 'id': diary_id})
            else:
                return redirect(url_for('login', error='データの復号に失敗しました。再度ログインしてください。'))
    except Exception as e:
        print(f"日記の読み込み中にエラーが発生しました: {e}")
        pass

    return render_template('index.html', diaries=diaries, years=years, display_title=display_title, selected_year=selected_year)

@app.route('/new', methods=['POST'])
def new_diary():
    if 'password' not in session:
        return redirect(url_for('login'))

    now = datetime.now()
    password = session['password']
    
    title = request.form['title']
    content = request.form['content']
    date = now.strftime('%Y-%m-%d %H:%M:%S')

    data = {'title': title, 'content': content, 'date': date}
    encrypted_data = encrypt_data(data, password)

    year_dir = os.path.join(DATA_DIR, now.strftime('%Y'))
    os.makedirs(year_dir, exist_ok=True)

    filename = f"{now.strftime('%Y%m%d%H%M%S%f')}.json.encrypted"
    filepath = os.path.join(year_dir, filename)
    
    with open(filepath, 'wb') as f:
        f.write(encrypted_data)

    return redirect(url_for('index'))

@app.route('/edit/<path:diary_id>', methods=['GET', 'POST'])
def edit(diary_id):
    if 'password' not in session:
        return redirect(url_for('login'))
    
    password = session['password']
    
    # 安全なファイルパスを構築
    filepath = os.path.abspath(os.path.join(DATA_DIR, diary_id))
    if not filepath.startswith(os.path.abspath(DATA_DIR)):
        return "不正なリクエストです", 400

    if not os.path.exists(filepath):
        return "日記が見つかりません", 404

    if request.method == 'POST':
        with open(filepath, 'rb') as f:
            encrypted_data = f.read()
        
        decrypted_data = decrypt_data(encrypted_data, password)
        if not decrypted_data:
            return redirect(url_for('login', error='データの復号に失敗しました。'))

        # データを更新
        decrypted_data['title'] = request.form['title']
        decrypted_data['content'] = request.form['content']
        
        # 更新したデータを暗号化して上書き保存
        new_encrypted_data = encrypt_data(decrypted_data, password)
        with open(filepath, 'wb') as f:
            f.write(new_encrypted_data)
            
        return redirect(url_for('index'))

    # GETリクエストの場合
    with open(filepath, 'rb') as f:
        encrypted_data = f.read()
    
    decrypted_data = decrypt_data(encrypted_data, password)
    if not decrypted_data:
        return redirect(url_for('login', error='データの復号に失敗しました。'))

    return render_template('edit.html', diary=decrypted_data, diary_id=diary_id)


if __name__ == '__main__':
    app.run(debug=True, port=5001)
