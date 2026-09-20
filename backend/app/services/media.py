"""Reel assembly. All text is rendered with Pillow to avoid ImageMagick deps."""
from __future__ import annotations

import logging
import textwrap
import uuid
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from app.config import get_settings
from app.services.tts import media_root

logger = logging.getLogger(__name__)

WIDTH, HEIGHT = 1080, 1920
BRAND_BG = (12, 23, 42)
BRAND_FG = (255, 255, 255)
ACCENT = (94, 234, 212)


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
    ):
        try:
            return ImageFont.truetype(candidate, size)
        except Exception:
            continue
    return ImageFont.load_default()


def render_scene_card(
    text: str,
    index: int,
    total: int,
    brand: str,
    out_path: Path,
) -> Path:
    """Render one 1080x1920 caption card."""
    image = Image.new("RGB", (WIDTH, HEIGHT), BRAND_BG)
    draw = ImageDraw.Draw(image)

    # Accent bar
    draw.rectangle([0, 0, WIDTH, 14], fill=ACCENT)

    # Brand label
    draw.text((80, 120), brand.replace("_", " ").upper(), font=_font(46), fill=ACCENT)

    # Main text, wrapped
    wrapped = textwrap.fill(text, width=22)
    draw.multiline_text(
        (80, HEIGHT // 2 - 220),
        wrapped,
        font=_font(96),
        fill=BRAND_FG,
        spacing=28,
    )

    # Progress dots
    for i in range(total):
        x = 80 + i * 60
        colour = ACCENT if i == index else (60, 75, 100)
        draw.ellipse([x, HEIGHT - 180, x + 34, HEIGHT - 146], fill=colour)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path)
    return out_path


def _render_storyboard(
    scenes: list[dict[str, Any]], title: str, brand: str
) -> list[Path]:
    frames_dir = media_root() / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for i, scene in enumerate(scenes):
        label = scene.get("on_screen_text") or scene.get("voiceover") or title
        path = frames_dir / f"frame_{uuid.uuid4().hex[:10]}_{i:02d}.png"
        paths.append(render_scene_card(label, i, len(scenes), brand, path))
    return paths


def assemble_reel(
    scenes: list[dict[str, Any]],
    title: str,
    audio_path: str | None = None,
    brand: str = "ja_assure",
) -> list[str]:
    """Render frames with MoviePy and return public URLs. Returns [] on failure."""
    settings = get_settings()
    try:
        from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips
    except Exception as exc:  # pragma: no cover - optional dependency
        logger.warning("moviepy unavailable (%s); skipping reel render", exc)
        return []

    try:
        frame_paths = _render_storyboard(scenes, title, brand)
        clips = []
        for path, scene in zip(frame_paths, scenes):
            duration = float(scene.get("duration_seconds", 4) or 4)
            clips.append(ImageClip(str(path)).set_duration(duration))

        video = concatenate_videoclips(clips, method="compose")

        if audio_path:
            try:
                audio = AudioFileClip(audio_path)
                video = video.set_audio(audio)
                if audio.duration < video.duration:
                    video = video.subclip(0, audio.duration)
            except Exception as exc:
                logger.warning("could not attach audio: %s", exc)

        out_dir = media_root() / "video"
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = f"reel_{uuid.uuid4().hex[:12]}.mp4"
        out_path = out_dir / filename

        video.write_videofile(
            str(out_path),
            fps=24,
            codec="libx264",
            audio_codec="aac",
            verbose=False,
            logger=None,
        )
        video.close()

        return [f"{settings.public_media_base_url}/video/{filename}"]
    except Exception as exc:
        logger.warning("reel assembly failed: %s", exc)
        return []