#!/usr/bin/env python3
"""
顔匿名化CLIツール
人物の顔にパンダやウサギのマスクを被せて匿名化します。
"""

import argparse
import os
import sys
import random
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from openai import OpenAI
from dotenv import load_dotenv


def detect_faces(image_path, debug_output_path=None):
    """
    OpenCVを使用して画像から顔を検出します。
    
    Args:
        image_path: 画像ファイルのパス
        debug_output_path: デバッグ画像の出力パス（Noneの場合は出力しない）
        
    Returns:
        検出された顔の座標リスト [(x, y, w, h), ...]
    """
    # 画像を読み込む
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"画像を読み込めませんでした: {image_path}")
    
    # グレースケールに変換
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # ヒストグラム均等化で明るさを調整（検出精度向上）
    gray = cv2.equalizeHist(gray)
    
    # Haar Cascade分類器を読み込む
    cascade_dir = cv2.data.haarcascades
    face_cascade = cv2.CascadeClassifier(cascade_dir + 'haarcascade_frontalface_default.xml')
    face_cascade_alt = cv2.CascadeClassifier(cascade_dir + 'haarcascade_frontalface_alt2.xml')
    
    # 分類器が正しく読み込まれたか確認
    if face_cascade.empty():
        raise ValueError("Haar Cascade分類器の読み込みに失敗しました")
    
    # 複数のパラメータで顔を検出（精度向上）
    all_faces = []
    
    # パラメータセット1: 標準的な検出
    faces1 = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30),
        flags=cv2.CASCADE_SCALE_IMAGE
    )
    all_faces.extend(faces1)
    
    # パラメータセット2: より感度を高めた検出
    faces2 = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.05,
        minNeighbors=3,
        minSize=(20, 20),
        flags=cv2.CASCADE_SCALE_IMAGE
    )
    all_faces.extend(faces2)
    
    # パラメータセット3: 代替分類器
    faces3 = face_cascade_alt.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=4,
        minSize=(30, 30),
        flags=cv2.CASCADE_SCALE_IMAGE
    )
    all_faces.extend(faces3)
    
    # 重複する顔領域を統合
    if len(all_faces) > 0:
        faces = merge_overlapping_faces(all_faces)
    else:
        faces = np.array([])
    
    # デバッグ画像を出力
    if debug_output_path and len(faces) > 0:
        debug_img = img.copy()
        for (x, y, w, h) in faces:
            # 検出された顔に矩形を描画
            cv2.rectangle(debug_img, (x, y), (x+w, y+h), (0, 255, 0), 3)
            # 楕円も描画（マスク領域の確認用）
            center_x = x + w // 2
            center_y = y + h // 2
            radius_x = int(w * 0.6)
            radius_y = int(h * 0.7)
            cv2.ellipse(debug_img, (center_x, center_y), (radius_x, radius_y), 
                       0, 0, 360, (255, 0, 0), 2)
        cv2.imwrite(debug_output_path, debug_img)
        print(f"デバッグ画像を保存しました: {debug_output_path}")
    
    return faces, img


def merge_overlapping_faces(faces):
    """
    重複する顔領域を統合します。
    
    Args:
        faces: 顔の座標リスト
        
    Returns:
        統合された顔の座標リスト
    """
    if len(faces) == 0:
        return np.array([])
    
    # 重複判定の閾値（IoU）
    iou_threshold = 0.3
    
    faces_list = list(faces)
    merged = []
    used = set()
    
    for i, face1 in enumerate(faces_list):
        if i in used:
            continue
        
        x1, y1, w1, h1 = face1
        merged_face = [x1, y1, w1, h1]
        
        for j, face2 in enumerate(faces_list[i+1:], start=i+1):
            if j in used:
                continue
            
            x2, y2, w2, h2 = face2
            
            # IoU（Intersection over Union）を計算
            x_overlap = max(0, min(x1+w1, x2+w2) - max(x1, x2))
            y_overlap = max(0, min(y1+h1, y2+h2) - max(y1, y2))
            intersection = x_overlap * y_overlap
            union = w1*h1 + w2*h2 - intersection
            iou = intersection / union if union > 0 else 0
            
            # 重複している場合は統合
            if iou > iou_threshold:
                # より大きい領域を採用
                if w2 * h2 > merged_face[2] * merged_face[3]:
                    merged_face = [x2, y2, w2, h2]
                used.add(j)
        
        merged.append(merged_face)
    
    return np.array(merged)


def create_mask_image(image_shape, faces):
    """
    検出された顔領域に対応するマスク画像を生成します。
    DALL-E 2の仕様: 透明な部分が編集される、不透明な部分が保持される
    
    Args:
        image_shape: 元画像のshape (height, width, channels)
        faces: 顔の座標リスト [(x, y, w, h), ...]
        
    Returns:
        マスク画像 (PIL Image, RGBA)
    """
    height, width = image_shape[:2]
    
    # 完全に不透明な白い画像を作成（背景は保持される）
    mask = Image.new('RGBA', (width, height), (255, 255, 255, 255))
    
    # NumPy配列に変換して楕円を描画
    mask_array = np.array(mask)
    
    for (x, y, w, h) in faces:
        # 顔領域を少し拡大して楕円を描画
        center_x = x + w // 2
        center_y = y + h // 2
        radius_x = int(w * 0.6)
        radius_y = int(h * 0.7)
        
        # 透明な楕円でマスク領域を示す（この部分が編集される）
        cv2.ellipse(
            mask_array,
            (center_x, center_y),
            (radius_x, radius_y),
            0, 0, 360,
            (0, 0, 0, 0),  # 完全に透明
            -1
        )
    
    return Image.fromarray(mask_array)


def prepare_image_for_dalle(image_path, output_path):
    """
    DALL-E 2 API用に画像を準備します（PNG形式、1024x1024、4MB以下）。
    
    Args:
        image_path: 元画像のパス
        output_path: 変換後の画像の保存パス
        
    Returns:
        変換後の画像パス
    """
    from PIL import Image
    
    # 画像を開く
    img = Image.open(image_path)
    
    # RGBAモードに変換（透過情報を保持）
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # 1024x1024にリサイズ（アスペクト比を維持して中央配置）
    target_size = 1024
    
    # アスペクト比を計算
    aspect = img.width / img.height
    
    if aspect > 1:
        # 横長の画像
        new_width = target_size
        new_height = int(target_size / aspect)
    else:
        # 縦長または正方形の画像
        new_height = target_size
        new_width = int(target_size * aspect)
    
    # リサイズ
    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # 1024x1024のキャンバスを作成（白背景）
    canvas = Image.new('RGBA', (target_size, target_size), (255, 255, 255, 255))
    
    # 中央に配置
    offset_x = (target_size - new_width) // 2
    offset_y = (target_size - new_height) // 2
    canvas.paste(img, (offset_x, offset_y), img)
    
    # PNG形式で保存
    canvas.save(output_path, 'PNG', optimize=True)
    
    # ファイルサイズを確認
    file_size = os.path.getsize(output_path)
    if file_size > 4 * 1024 * 1024:  # 4MB
        # 品質を下げて再保存
        canvas.save(output_path, 'PNG', optimize=True, compress_level=9)
    
    return {
        'original_size': (img.width, img.height),
        'scaled_size': (new_width, new_height),
        'offset': (offset_x, offset_y),
        'target_size': target_size
    }


def anonymize_with_dalle(image_path, mask_image, output_path, mask_path):
    """
    DALL-E 2 APIを使用して顔にマスクを被せます。
    
    Args:
        image_path: 元画像のパス
        mask_image: マスク画像 (PIL Image)
        output_path: 出力画像のパス
        mask_path: マスク画像の保存パス
    """
    # OpenAI APIキーを取得
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError(
            "OpenAI APIキーが設定されていません。\n"
            "環境変数 OPENAI_API_KEY を設定するか、.env ファイルを作成してください。"
        )
    
    client = OpenAI(api_key=api_key)
    
    # ランダムにマスクの種類を選択
    mask_types = [
        "A cute panda mask on the face, natural looking, photorealistic, kawaii style",
        "A cute rabbit mask on the face, natural looking, photorealistic, kawaii style"
    ]
    prompt = random.choice(mask_types)
    
    print(f"マスクを生成中: {prompt}")
    
    # 元画像を準備（PNG形式、1024x1024）
    temp_image_path = image_path.replace(Path(image_path).suffix, '_temp.png')
    prep_info = prepare_image_for_dalle(image_path, temp_image_path)
    print(f"画像を変換しました: {temp_image_path}")
    
    # マスク画像も1024x1024にリサイズして保存
    mask_resized = mask_image.resize((1024, 1024), Image.Resampling.LANCZOS)
    mask_resized.save(mask_path, 'PNG')
    print(f"マスク画像を保存しました: {mask_path}")
    
    try:
        # 画像を編集
        print("API呼び出し中...")
        with open(temp_image_path, 'rb') as image_file, open(mask_path, 'rb') as mask_file:
            response = client.images.edit(
                model="gpt-image-1-mini",
                image=image_file,
                mask=mask_file,
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
        
        # 生成された画像のURLまたはBase64データを取得
        if hasattr(response, 'data') and len(response.data) > 0:
            item = response.data[0]
            
            # Base64形式の場合
            if hasattr(item, 'b64_json') and item.b64_json:
                print("Base64形式の画像をデコード中...")
                import base64
                image_data = base64.b64decode(item.b64_json)
                with open(output_path, 'wb') as f:
                    f.write(image_data)
                print(f"匿名化された画像を保存しました: {output_path}")
            
            # URL形式の場合
            elif hasattr(item, 'url') and item.url:
                print(f"URLから画像をダウンロード中: {item.url}")
                import urllib.request
                urllib.request.urlretrieve(item.url, output_path)
                print(f"匿名化された画像を保存しました: {output_path}")
            
            else:
                raise ValueError(f"画像データが見つかりません: {item}")
            
            # 元のサイズに復元
            if os.path.exists(output_path):
                print("画像を元のサイズに復元中...")
                result_img = Image.open(output_path)
                
                # キャンバスから貼り付けられた領域を切り出す
                ox, oy = prep_info['offset']
                sw, sh = prep_info['scaled_size']
                cropped_img = result_img.crop((ox, oy, ox + sw, oy + sh))
                
                # 元のサイズにリサイズ
                final_img = cropped_img.resize(prep_info['original_size'], Image.Resampling.LANCZOS)
                
                # 保存（RGBAからRGBに変換してJPG/PNGとして保存）
                # output_pathの拡張子に合わせて保存
                if output_path.lower().endswith('.png'):
                    final_img.save(output_path, 'PNG')
                else:
                    final_img.convert('RGB').save(output_path, 'JPEG', quality=95)
                
                print(f"サイズ復元完了: {prep_info['original_size'][0]}x{prep_info['original_size'][1]}")
                
        else:
            raise ValueError(f"予期しないレスポンス形式: {response}")
        
    finally:
        # 一時ファイルを削除
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description='人物の顔を匿名化するツール。顔にパンダやウサギのマスクを被せます。'
    )
    parser.add_argument(
        'image',
        help='匿名化する画像ファイルのパス'
    )
    parser.add_argument(
        '-o', '--output',
        help='出力ファイルのパス (デフォルト: 元ファイル名-anon.png)',
        default=None
    )
    
    args = parser.parse_args()
    
    # 入力ファイルの確認
    if not os.path.exists(args.image):
        print(f"エラー: ファイルが見つかりません: {args.image}", file=sys.stderr)
        sys.exit(1)
    
    # 出力ファイル名の決定
    if args.output:
        output_path = args.output
    else:
        path = Path(args.image)
        output_path = str(path.parent / f"{path.stem}-anon.png")
    
    # マスクファイル名の決定
    path = Path(args.image)
    mask_path = str(path.parent / f"{path.stem}-mask.png")
    debug_path = str(path.parent / f"{path.stem}-debug.png")
    
    try:
        # 顔を検出
        print("顔を検出中...")
        faces, img = detect_faces(args.image, debug_output_path=debug_path)
        
        if len(faces) == 0:
            print("警告: 顔が検出されませんでした。", file=sys.stderr)
            sys.exit(1)
        
        print(f"{len(faces)}個の顔を検出しました。")
        
        # マスク画像を生成
        print("マスク画像を生成中...")
        mask_image = create_mask_image(img.shape, faces)
        
        # DALL-E 2で匿名化
        anonymize_with_dalle(args.image, mask_image, output_path, mask_path)
        
        print("完了しました!")
        
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
