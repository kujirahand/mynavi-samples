from __future__ import annotations

import textwrap
import time
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from moviepy import AudioFileClip, ImageClip
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont, ImageOps

APP_DIR = Path(__file__).parent
STATIC_DIR = APP_DIR / "static"
BG_IMAGE = APP_DIR / "background.png"
TITLE_IMG = STATIC_DIR / "title.png"
TTS_MP3 = STATIC_DIR / "speech.mp3"
OUTPUT_MP4 = STATIC_DIR / "output.mp4"

app = Flask(__name__)
client = OpenAI()


FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in FONT_CANDIDATES:
        p = Path(path)
        if p.exists():
            return ImageFont.truetype(str(p), size=size)
    return ImageFont.load_default()


def create_title_image(title: str, out_path: Path) -> None:
    width, height = 1280, 720
    if BG_IMAGE.exists():
        bg = Image.open(BG_IMAGE).convert("RGB")
        bg = ImageOps.fit(bg, (width, height), method=Image.LANCZOS, centering=(0.5, 0.5))
        img = bg
    else:
        img = Image.new("RGB", (width, height), color=(18, 22, 28))
    draw = ImageDraw.Draw(img)

    max_width_px = int(width * 0.85)
    font_size = 96
    font = _load_font(font_size)

    wrapped = title.strip() or "(no title)"
    while True:
        lines = textwrap.wrap(wrapped, width=18)
        line_heights = []
        max_line_width = 0
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            max_line_width = max(max_line_width, bbox[2] - bbox[0])
            line_heights.append(bbox[3] - bbox[1])
        total_height = sum(line_heights) + (len(lines) - 1) * 10
        if max_line_width <= max_width_px and total_height <= height * 0.7:
            break
        font_size -= 4
        if font_size < 28:
            break
        font = _load_font(font_size)

    y = (height - total_height) // 2
    box_padding_x = 70
    box_padding_y = 40
    box_width = min(max_line_width + box_padding_x * 2, int(width * 0.9))
    box_height = total_height + box_padding_y * 2
    box_x = (width - box_width) // 2
    box_y = max((height - box_height) // 2, 30)

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rounded_rectangle(
        (box_x, box_y, box_x + box_width, box_y + box_height),
        radius=28,
        fill=(8, 12, 18, 170),
    )
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        x = (width - line_width) // 2
        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, 160))
        draw.text((x, y), line, font=font, fill=(236, 240, 245))
        y += line_heights[i] + 10

    img.save(out_path)


def generate_speech(text: str, out_path: Path) -> None:
    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="coral",
        input=text,
    ) as response:
        response.stream_to_file(out_path)


def compose_video(image_path: Path, audio_path: Path, out_path: Path) -> None:
    audio = AudioFileClip(str(audio_path))
    clip = ImageClip(str(image_path)).with_duration(audio.duration).with_audio(audio)
    clip.write_videofile(
        str(out_path),
        fps=24,
        codec="libx264",
        audio_codec="aac",
        threads=2,
        logger=None,
    )
    clip.close()
    audio.close()


@app.route("/", methods=["GET"])
def index():
    video_url = None
    if OUTPUT_MP4.exists():
        video_url = f"/static/output.mp4?v={int(OUTPUT_MP4.stat().st_mtime)}"

    return render_template("index.html", video_url=video_url)


@app.route("/generate", methods=["POST"])
def generate():
    title = request.form.get("title", "").strip()
    text = request.form.get("text", "").strip()
    if not title or not text:
        return jsonify({"ok": False, "error": "タイトルとテキストを入力してください。"}), 400

    create_title_image(title, TITLE_IMG)
    generate_speech(text, TTS_MP3)
    compose_video(TITLE_IMG, TTS_MP3, OUTPUT_MP4)
    video_url = f"/static/output.mp4?v={int(time.time())}"
    return jsonify({"ok": True, "video_url": video_url})


if __name__ == "__main__":
    app.run(debug=True)
