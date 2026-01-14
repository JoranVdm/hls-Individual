import os
import subprocess
from pathlib import Path
from celery_app import cel
from database import SessionLocal
import crud
from utils import make_paths
from storage.uploader import upload_file
import json
from datetime import datetime

# renditions: label, resolution, video bitrate (k), audio bitrate
RENDITIONS = [
    ("1080p", "1920x1080", "4000k", "128k"),
    ("720p",  "1280x720",  "2500k", "128k"),
    ("480p",  "854x480",   "1200k", "96k"),
    ("360p",  "640x360",   "700k", "64k"),
]

VIDEO_ROOT = os.path.join(os.path.dirname(__file__), "videos")


def run(cmd):
    proc = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    return proc.returncode, proc.stdout, proc.stderr


def log_message(work_dir, message):
    print(message)
    if work_dir:
        log_path = Path(work_dir) / "transcode.log"
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} {message}\n")


def get_english_audio_index(source_abs_path, work_dir=None):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "stream=index,codec_type,channels:stream_tags=language,title",
        "-of", "json",
        str(source_abs_path)
    ]
    code, out, err = run(cmd)
    if code != 0:
        raise RuntimeError(f"ffprobe failed: {err}")

    info = json.loads(out)
    audio_streams = [s for s in info.get("streams", []) if s["codec_type"] == "audio"]
    if not audio_streams:
        log_message(work_dir, "⚠️ No audio streams found.")
        return None

    best_stream = None
    best_score = -999
    for s in audio_streams:
        tags = s.get("tags", {})
        lang = tags.get("language", "").lower()
        title = tags.get("title", "").lower()
        score = 0
        if lang == "eng":
            score += 3
        if "english" in title or "main" in title:
            score += 2
        if any(x in title for x in ["commentary", "director", "alt", "behind"]):
            score -= 3
        if not title and lang == "eng":
            score += 1
        if score > best_score:
            best_score = score
            best_stream = s

    return best_stream["index"] if best_stream else None


@cel.task(bind=True)
def transcode_job(self, show_title, season, episode_number, source_abs_path, episode_id):
    db = SessionLocal()
    show_slug, season_folder, episode_folder, base = make_paths(show_title, season, episode_number)
    work_dir = Path(VIDEO_ROOT) / base
    work_dir.mkdir(parents=True, exist_ok=True)

    try:
        eng_audio_idx = get_english_audio_index(source_abs_path, work_dir)
        rendition_meta = {}

        # 🎬 TRANSCODING
        for label, resolution, vbit, abitrate in RENDITIONS:
            subfolder = work_dir / label
            subfolder.mkdir(parents=True, exist_ok=True)

            playlist = subfolder / "index.m3u8"
            segment_pattern = str(subfolder / f"{label}_%03d.ts")
            audio_map = f"0:{eng_audio_idx}" if eng_audio_idx is not None else "0:a:0"

            log_message(work_dir, f"🎬 Transcoding {label}")

            cmd = [
                "ffmpeg", "-y", "-i", str(source_abs_path),
                "-map", "0:v:0",
                "-map", audio_map,
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                "-vf", f"scale={resolution}",
                "-b:v", vbit,
                "-c:a", "aac", "-b:a", abitrate,
                "-hls_time", "4",
                "-hls_list_size", "0",
                "-hls_segment_filename", segment_pattern,
                str(playlist)
            ]

            self.update_state(state="PROGRESS", meta={"current": label})
            code, _, err = run(cmd)
            if code != 0:
                crud.mark_episode_failed(db, episode_id, err[:200])
                raise RuntimeError(err)

            rendition_meta[label] = {
                "playlist": str(Path(base) / label / "index.m3u8"),
                "bitrate": vbit,
                "resolution": resolution
            }

        # 📜 MASTER PLAYLIST
        master_path = work_dir / "master.m3u8"
        with open(master_path, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for label, info in rendition_meta.items():
                bw = int(info["bitrate"].replace("k", "")) * 1000
                f.write(f"#EXT-X-STREAM-INF:BANDWIDTH={bw},RESOLUTION={info['resolution']}\n")
                f.write(f"{label}/index.m3u8\n")

        master_rel = str(Path(base) / "master.m3u8")

        # ☁️ UPLOAD ALL PLAYLISTS AND SEGMENTS
        uploaded_renditions = {}
        for label, info in rendition_meta.items():
            local_rendition_dir = Path(VIDEO_ROOT) / Path(info["playlist"]).parent

            # Upload all .ts segment files
            for ts_file in local_rendition_dir.glob("*.ts"):
                remote_ts_path = str(Path(info["playlist"]).parent / ts_file.name)
                upload_file(ts_file, remote_ts_path)
                log_message(work_dir, f"☁️ Uploaded segment: {remote_ts_path}")

            # Upload the rendition playlist
            local_playlist = Path(VIDEO_ROOT) / info["playlist"]
            remote_playlist_path = info["playlist"]
            playlist_url = upload_file(local_playlist, remote_playlist_path)
            log_message(work_dir, f"☁️ Uploaded playlist: {remote_playlist_path}")

            uploaded_renditions[label] = {
                **info,
                "playlist_url": playlist_url
            }

        # Upload master playlist
        master_url = upload_file(master_path, master_rel)
        log_message(work_dir, f"☁️ Uploaded master playlist: {master_rel}")

        # 💾 STORE URLS IN DB
        crud.update_episode_ready(db, episode_id, master_url, uploaded_renditions)
        log_message(work_dir, f"🎉 Done! Master URL: {master_url}")

        return {"status": "ok", "master": master_url}

    except Exception as e:
        crud.mark_episode_failed(db, episode_id, str(e))
        log_message(work_dir, f"❌ Failed: {e}")
        raise

    finally:
        db.close()
