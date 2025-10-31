import os
import subprocess
from pathlib import Path
from .celery_app import cel
from .database import SessionLocal
from . import crud, models
from .utils import make_paths
import json

# renditions: label, widthxheight, video bitrate (k), audio bitrate
RENDITIONS = [
    ("1080p", "1920x1080", "4000k", "128k"),
    ("720p",  "1280x720",  "2500k", "128k"),
    ("480p",  "854x480",   "1200k", "96k"),
    ("360p",  "640x360",   "700k",  "64k"),
]

VIDEO_ROOT = os.path.join(os.path.dirname(__file__), "videos")

def run(cmd):
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return proc.returncode, proc.stdout, proc.stderr

@cel.task(bind=True)
def transcode_job(self, show_title, season, episode_number, source_abs_path, episode_id):
    db = SessionLocal()
    show_slug, season_folder, episode_folder, base = make_paths(show_title, season, episode_number)
    work_dir = Path(VIDEO_ROOT) / base
    work_dir.mkdir(parents=True, exist_ok=True)

    try:
        # generate per-rendition playlists into subfolders
        rendition_meta = {}
        for label, resolution, vbit, abitrate in RENDITIONS:
            subfolder = work_dir / label
            subfolder.mkdir(parents=True, exist_ok=True)
            playlist = subfolder / "index.m3u8"
            segment_pattern = str(subfolder / f"{label}_%03d.ts")

            cmd = [
                "ffmpeg", "-y", "-i", str(source_abs_path),
                "-c:v", "libx264", "-profile:v", "main", "-preset", "veryfast", "-crf", "20",
                "-vf", f"scale={resolution}",
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
                raise RuntimeError(f"ffmpeg failed for {label}: {err}")

            # store meta
            rendition_meta[label] = {"playlist": str(Path(base) / label / "index.m3u8"), "bitrate": vbit, "resolution": resolution}

        # write master playlist (relative paths to sub-playlists)
        master_path = Path(VIDEO_ROOT) / base / "master.m3u8"
        with open(master_path, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for label, info in rendition_meta.items():
                bw = int(info["bitrate"].replace("k","")) * 1000
                res = info["resolution"]
                # EXT-X-STREAM-INF must reference the sub-playlist path relative to master
                f.write(f"#EXT-X-STREAM-INF:BANDWIDTH={bw},RESOLUTION={res}\n")
                f.write(f"{label}/index.m3u8\n")

        # update DB
        master_rel = str(Path(base) / "master.m3u8")  # e.g. "southpark/Season1/Episode1/master.m3u8"
        crud.update_episode_ready(db, episode_id, master_rel, rendition_meta)
        return {"status": "ok", "master": master_rel}

    except Exception as e:
        crud.mark_episode_failed(db, episode_id, str(e))
        raise
    finally:
        db.close()
