"""Reel assembly. All text is rendered with Pillow to avoid ImageMagick deps."""
from __future__ import annotations

import logging
import textwrap
import uuid
import httpx
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
    """Load a bold TrueType font at the requested size, cross-platform."""
    candidates = [
        # Windows
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf",
        r"C:\Windows\Fonts\calibrib.ttf",
        r"C:\Windows\Fonts\verdanab.ttf",
        # macOS
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        # Linux
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue

    # Last-resort fallback — at least try to honour the size on new Pillow.
    try:
        return ImageFont.load_default(size=size)   # Pillow >= 10.1
    except TypeError:
        logger.warning("No TrueType font found — text will be tiny. "
                       "Install Arial/DejaVu or set a valid font path.")
        return ImageFont.load_default()


def _wrap_and_fit(
    draw: ImageDraw.ImageDraw,
    text: str,
    box_width: int,
    box_height: int,
    initial_size: int = 200,
    min_size: int = 60,
) -> tuple[ImageFont.FreeTypeFont | ImageFont.ImageFont, list[str], int]:
    """Find the largest font size at which `text` fits inside the given box."""
    size = initial_size
    while size >= min_size:
        font = _font(size)
        words = text.split()
        lines: list[str] = []
        current = ""
        for word in words:
            probe = f"{current} {word}".strip()
            bbox = draw.textbbox((0, 0), probe, font=font)
            if bbox[2] - bbox[0] <= box_width:
                current = probe
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)

        line_height = int(size * 1.25)
        total_height = len(lines) * line_height
        if total_height <= box_height:
            return font, lines, line_height

        size -= 12

    font = _font(min_size)
    return font, textwrap.wrap(text, 14), int(min_size * 1.25)


def render_scene_card(
    text: str,
    index: int,
    total: int,
    brand: str,
    out_path: Path,
) -> Path:
    """Render one 1080x1920 caption card with auto-fitted, high-impact text."""
    image = Image.new("RGB", (WIDTH, HEIGHT), BRAND_BG)
    draw = ImageDraw.Draw(image)

    # Top accent bar
    draw.rectangle([0, 0, WIDTH, 18], fill=ACCENT)

    # Brand label — top-left
    draw.text(
        (72, 90),
        brand.replace("_", " ").upper(),
        font=_font(52),
        fill=ACCENT,
    )

    # Scene number — top-right, large and muted
    counter = f"{index + 1}/{total}"
    counter_font = _font(52)
    bbox = draw.textbbox((0, 0), counter, font=counter_font)
    draw.text(
        (WIDTH - 72 - (bbox[2] - bbox[0]), 90),
        counter,
        font=counter_font,
        fill=(90, 110, 145),
    )

    # Main text — auto-fit into the central box
    padding = 72
    box_width = WIDTH - padding * 2
    box_top = 320
    box_height = HEIGHT - box_top - 260          # leave room for progress dots

    font, lines, line_height = _wrap_and_fit(
        draw, text, box_width=box_width, box_height=box_height, initial_size=200
    )

    # Vertically centre the block
    text_height = len(lines) * line_height
    y = box_top + (box_height - text_height) // 2
    for line in lines:
        draw.text((padding, y), line, font=font, fill=BRAND_FG)
        y += line_height

    # Progress dots
    for i in range(total):
        cx = padding + 30 + i * 60
        colour = ACCENT if i == index else (50, 65, 95)
        r = 18 if i == index else 12
        draw.ellipse([cx - r, HEIGHT - 160 - r, cx + r, HEIGHT - 160 + r], fill=colour)

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
    """Render frames and return public URLs. Returns [] on failure."""
    settings = get_settings()
    try:
        from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips
    except Exception as exc:
        logger.warning("moviepy unavailable (%s); skipping reel render", exc)
        return []

    try:
        # 1. Determine target duration from audio (if present)
        audio = None
        target_duration: float | None = None
        if audio_path:
            try:
                audio = AudioFileClip(audio_path)
                target_duration = audio.duration
            except Exception as exc:
                logger.warning("could not load audio: %s", exc)

        # 2. Scale each scene so the video length matches the audio
        raw_durations = [float(s.get("duration_seconds", 4) or 4) for s in scenes]
        total_raw = sum(raw_durations)
        if target_duration and total_raw > 0:
            scale = target_duration / total_raw
        else:
            scale = 1.0
        scaled_durations = [max(1.0, d * scale) for d in raw_durations]

        # 3. Render frames and build clips with the scaled durations
        frame_paths = _render_storyboard(scenes, title, brand)
        clips = []
        for path, duration in zip(frame_paths, scaled_durations):
            clips.append(ImageClip(str(path)).set_duration(duration))

        video = concatenate_videoclips(clips, method="compose")
        if audio is not None:
            video = video.set_audio(audio)

        # 4. Write
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


def fetch_stock_image(query: str) -> str | None:
    """Search Pexels for a commercially-licensed stock image.

    Returns the image URL, or None if no key is configured or nothing is found.
    """
    settings = get_settings()
    api_key = getattr(settings, "pexels_api_key", "")
    if not api_key:
        logger.info("PEXELS_API_KEY not set — skipping image fetch")
        return None

    try:
        response = httpx.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": api_key},
            params={"query": query[:100], "per_page": 3, "orientation": "square"},
            timeout=20.0,
        )
        response.raise_for_status()
        photos = response.json().get("photos", [])
        if photos:
            src = photos[0].get("src", {})
            url = src.get("large") or src.get("medium") or src.get("original")
            if url:
                logger.info("pexels image found: %s", url)
                return url
    except Exception as exc:
        logger.warning("pexels search failed: %s", exc)
    return None