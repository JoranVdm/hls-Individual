import os
import subprocess
from pathlib import Path
from celery_app import cel
from database import SessionLocal
import crud, models
from utils import make_paths
import json
import re
from datetime import datetime

# renditions: label, widthxheight, video bitrate (k), audio bitrate
RENDITIONS = [
    ("1080p", "1920x1080", "4000k", "128k"),
    ("720p",  "1280x720",  "2500k", "128k"),
    ("480p",  "854x480",   "1200k", "96k"),
    ("360p",  "640x360",   "700k", "64k"),
]

VIDEO_ROOT = os.path.join(os.path.dirname(__file__), "videos")


def run(cmd):
    """Run a subprocess and return code, stdout, stderr."""
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def log_message(work_dir, message):
    """Print and also log to file (if work_dir is available)."""
    print(message)
    if work_dir:
        log_path = Path(work_dir) / "transcode.log"
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} {message}\n")


def get_english_audio_index(source_abs_path, work_dir=None):
    """
    Detect the best English audio track by scoring each audio stream.
    Logs every candidate and reasoning.

    Scoring rules:
      +3 → if language is 'eng'
      +2 → if title contains 'english' or 'main'
      -3 → if title contains 'commentary', 'director', 'alt', 'behind', 'discussion'
      +1 → if no title but language=eng (fallback)
    """
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "stream=index,codec_type,codec_name,channels:stream_tags=language,title",
        "-of", "json", str(source_abs_path)
    ]
    code, out, err = run(cmd)
    if code != 0:
        raise RuntimeError(f"ffprobe failed: {err}")

    info = json.loads(out)
    audio_streams = [s for s in info.get("streams", []) if s["codec_type"] == "audio"]

    if not audio_streams:
        log_message(work_dir, "⚠️ No audio streams found.")
        return None

    log_message(work_dir, "\n🔍 Checking available audio tracks:")
    best_stream = None
    best_score = -999

    for s in audio_streams:
        tags = s.get("tags", {})
        lang = tags.get("language", "").lower()
        title = tags.get("title", "").lower()
        score = 0

        # --- scoring logic ---
        if lang == "eng":
            score += 3
        if "english" in title or "main" in title:
            score += 2
        if any(x in title for x in ["commentary", "director", "alt", "behind", "discussion"]):
            score -= 3
        if not title and lang == "eng":
            score += 1

        log_message(work_dir, f"  • index={s['index']} | lang={lang or 'N/A'} | title={tags.get('title', 'N/A')} | score={score}")

        if score > best_score:
            best_score = score
            best_stream = s

    # Fallback
    if not best_stream:
        best_stream = audio_streams[0]
        log_message(work_dir, f"⚠️ No good match found, defaulting to index={best_stream['index']}")
    else:
        log_message(
            work_dir,
            f"✅ Selected best audio track: index={best_stream['index']} | "
            f"lang={best_stream.get('tags', {}).get('language')} | "
            f"title={best_stream.get('tags', {}).get('title', 'N/A')} | score={best_score}"
        )

    return best_stream["index"]


@cel.task(bind=True)
def transcode_job(self, show_title, season, episode_number, source_abs_path, episode_id):
    db = SessionLocal()
    show_slug, season_folder, episode_folder, base = make_paths(show_title, season, episode_number)
    work_dir = Path(VIDEO_ROOT) / base
    work_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Determine audio track
        eng_audio_idx = get_english_audio_index(source_abs_path, work_dir)

        rendition_meta = {}
        for label, resolution, vbit, abitrate in RENDITIONS:
            subfolder = work_dir / label
            subfolder.mkdir(parents=True, exist_ok=True)
            playlist = subfolder / "index.m3u8"
            segment_pattern = str(subfolder / f"{label}_%03d.ts")

            # Use optional map to avoid FFmpeg failing
            audio_map = f"0:{eng_audio_idx}" if eng_audio_idx is not None else "0:a:0"

            log_message(work_dir, f"\n🎬 Starting transcoding for {label} (audio map: {audio_map})")

            cmd = [
                "ffmpeg", "-y", "-i", str(source_abs_path),
                "-map", "0:v:0",              # first video track
                "-map", audio_map,            # English or fallback audio
                "-c:v", "libx264", "-profile:v", "main", "-preset", "veryfast", "-crf", "20",
                "-vf", f"scale={resolution}",
                "-pix_fmt", "yuv420p",
                "-b:v", vbit, "-maxrate", vbit, "-bufsize", "2M",
                "-c:a", "aac", "-b:a", abitrate, "-ac", "2",
                "-start_number", "0",
                "-hls_time", "4",
                "-hls_list_size", "0",
                "-hls_segment_filename", segment_pattern,
                str(playlist)
            ]

            self.update_state(state="PROGRESS", meta={"current": label})
            code, out, err = run(cmd)
            if code != 0:
                crud.mark_episode_failed(db, episode_id, f"ffmpeg failed {label}: {err[:200]}")
                log_message(work_dir, f"\n❌ FFMPEG ERROR ({label}):\n{err}\n========================\n")
                raise RuntimeError(f"ffmpeg failed for {label}: see logs above")

            log_message(work_dir, f"✅ Finished {label}")

            rendition_meta[label] = {
                "playlist": str(Path(base) / label / "index.m3u8"),
                "bitrate": vbit,
                "resolution": resolution
            }

        # Master playlist
        master_path = Path(VIDEO_ROOT) / base / "master.m3u8"
        with open(master_path, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for label, info in rendition_meta.items():
                bw = int(info["bitrate"].replace("k","")) * 1000
                res = info["resolution"]
                f.write(f"#EXT-X-STREAM-INF:BANDWIDTH={bw},RESOLUTION={res}\n")
                f.write(f"{label}/index.m3u8\n")

        master_rel = str(Path(base) / "master.m3u8")
        crud.update_episode_ready(db, episode_id, master_rel, rendition_meta)
        log_message(work_dir, f"\n🎉 Transcoding complete! Master playlist: {master_rel}")

        return {"status": "ok", "master": master_rel}

    except Exception as e:
        crud.mark_episode_failed(db, episode_id, str(e))
        log_message(work_dir, f"❌ Transcoding failed: {str(e)}")
        raise
    finally:
        db.close()
