#!/usr/bin/env python3
"""Webカメラから画像をキャプチャし、動き検出時と定期的に保存するプログラム"""
import cv2
import os
import shutil
import time
from datetime import datetime

# 設定 --- (*1)
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(ROOT_DIR, "statics", "images")  # 画像保存ディレクトリ
NOW_FILE = os.path.join(SAVE_DIR, "now.jpg")  # 最新画像の保存先
MOTION_THRESHOLD = 5000  # 動き検出の閾値
PERIODIC_SAVE_INTERVAL = 600  # 定期保存の間隔（秒） 10分 = 600秒
FRAME_WIDTH = 640  # フレームの幅
FRAME_HEIGHT = 480  # フレームの高さ

def get_filename():
    """現在の日時をファイル名として取得"""  # --- (*2)
    now = datetime.now()
    filedir = os.path.join(SAVE_DIR, now.strftime("%Y%m%d"))
    if not os.path.exists(filedir):
        os.makedirs(filedir)
    filename = now.strftime("%H%M%S.jpg")
    return os.path.join(filedir, filename)

def save_image(frame, reason=""):
    """画像を保存"""  # --- (*3)
    filename = get_filename()
    cv2.imwrite(filename, frame)
    print(f"保存: {filename} {reason}")
    # 最新画像としてファイルコピー
    shutil.copyfile(filename, NOW_FILE)

    return filename

def detect_motion(frame1, frame2):
    """2つのフレーム間の動きを検出"""  # --- (*4)
    # グレースケールに変換
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    # ガウシアンブラーを適用してノイズを減らす
    gray1 = cv2.GaussianBlur(gray1, (21, 21), 0)
    gray2 = cv2.GaussianBlur(gray2, (21, 21), 0)
    # フレーム差分を計算
    frame_diff = cv2.absdiff(gray1, gray2)
    _, thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)
    # 差分の合計を計算
    diff_sum = thresh.sum()
    return diff_sum > MOTION_THRESHOLD

def main():
    """メイン処理"""
    print("Webカメラ画像キャプチャプログラムを起動します...")
    # 保存ディレクトリの準備
    os.makedirs(SAVE_DIR, exist_ok=True)
    # Webカメラを開く --- (*5)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("エラー: カメラを開けませんでした")
        return
    # カメラの解像度を設定
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    print(f"カメラを起動しました（解像度: {FRAME_WIDTH}x{FRAME_HEIGHT}）")
    print(f"動き検出閾値: {MOTION_THRESHOLD}")
    print(f"定期保存間隔: {PERIODIC_SAVE_INTERVAL}秒（{PERIODIC_SAVE_INTERVAL // 60}分）")
    print("終了する場合は Ctrl+C を押してください")
    # 最初のフレームを取得 --- (*6)
    ret, prev_frame = cap.read()
    if not ret:
        print("エラー: フレームを読み込めませんでした")
        cap.release()
        return
    # 最後に保存した時刻を記録 --- (*7)
    last_save_time = time.time()
    try:
        while True:
            # フレームを取得 --- (*8)
            ret, current_frame = cap.read()
            if not ret:
                print("エラー: フレームを読み込めませんでした")
                break
            # 現在の時刻
            current_time = time.time()
            # 動き検出 --- (*9)
            motion_detected = detect_motion(prev_frame, current_frame)
            if motion_detected:
                save_image(current_frame, "(動き検出)")
                # 保存後は前フレームを更新
                prev_frame = current_frame.copy()
            # 定期保存（10分ごと） --- (*10)
            if current_time - last_save_time >= PERIODIC_SAVE_INTERVAL:
                save_image(current_frame, "(定期保存)")
                last_save_time = current_time
            # プレビューなしの場合は短い待機のみ
            time.sleep(0.1)
            if not motion_detected:
                prev_frame = current_frame.copy()
    except KeyboardInterrupt:
        print("\nプログラムを終了します...")
    finally:
        # リソースを解放
        cap.release()
        cv2.destroyAllWindows()
        print("カメラを解放しました")

if __name__ == "__main__":
    main()
