import os
import shutil
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from .database import SessionLocal, engine
from . import models, crud, utils, tasks


# Create tables if they don't exist
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# -------------------------
# CORS Setup
# -------------------------
origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Static files
# -------------------------
VIDEO_DIR = os.path.join(os.path.dirname(__file__), "videos")
COVER_DIR = os.path.join(os.path.dirname(__file__), "Cover")
os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(COVER_DIR, exist_ok=True)

app.mount("/videos", StaticFiles(directory=VIDEO_DIR), name="videos")
app.mount("/covers", StaticFiles(directory=COVER_DIR), name="covers")

# -------------------------
# Database session
# -------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------
# Root
# -------------------------
@app.get("/")
def read_root():
    return {"message": "✅ HLS backend with PostgreSQL is running"}

# -------------------------
# SHOW endpoints
# -------------------------
@app.get("/shows")
def list_shows(db: Session = Depends(get_db)):
    shows = db.query(models.Show).all()
    return {
        "shows": [
            {
                "id": s.id,
                "title": s.title,
                "description": s.description,
                "cover_url": s.cover,
            }
            for s in shows
        ]
    }

@app.post("/shows")
def create_show(
    title: str = Form(...),
    description: str = Form(None),
    cover: UploadFile | None = None,
    db: Session = Depends(get_db),
):
    cover_path = None
    if cover:
        safe_filename = cover.filename.replace(" ", "_")
        target = os.path.join(COVER_DIR, safe_filename)
        with open(target, "wb") as f:
            shutil.copyfileobj(cover.file, f)
        cover_path = f"/covers/{safe_filename}"

    show = crud.create_show(db, title=title, description=description, cover=cover_path)
    return {"show_id": show.id, "title": show.title}

# -------------------------
# EPISODE endpoints
# -------------------------
@app.get("/shows/{show_id}/episodes")
def list_episodes(show_id: int, db: Session = Depends(get_db)):
    show = db.query(models.Show).options(joinedload(models.Show.episodes)).filter(models.Show.id == show_id).first()
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")

    episodes = [
        {
            "id": ep.id,
        "title": ep.title,
        "duration": ep.duration,
        "status": ep.status,
        "renditions": ep.renditions,
        "playlist_path": ep.master_path,
        }
        for ep in show.episodes
    ]
    return {"show": show.title, "episodes": episodes}

@app.get("/shows/{show_id}/playlist/{episode_id}")
def get_episode_playlist(show_id: int, episode_id: int, db: Session = Depends(get_db)):
    episode = db.query(models.Episode).filter(models.Episode.id == episode_id, models.Episode.show_id == show_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    playlist_url = f"/videos/{episode.playlist_path}"
    return {"episode": episode.title, "playlist": playlist_url}

# -------------------------
# Episode upload + enqueue (transcoding)
# -------------------------
@app.post("/episodes/upload")
def upload_and_enqueue(
    show_title: str = Form(...),
    season: int = Form(...),
    episode_number: int = Form(...),
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # Ensure show exists
    show = crud.get_show_by_title(db, show_title)
    if not show:
        show = crud.create_show(db, title=show_title)

    # Compute paths (uses utils.make_paths)
    show_slug, season_folder, episode_folder, base_folder = utils.make_paths(show_title, season, episode_number)
    out_dir = os.path.join(VIDEO_DIR, base_folder)
    os.makedirs(out_dir, exist_ok=True)

    # Save uploaded file
    source_abs = os.path.join(out_dir, file.filename)
    with open(source_abs, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Create DB episode row
    ep = crud.create_episode(
        db,
        show_id=show.id,
        title=title,
        season=season,
        episode_num=episode_number,
        base_folder=base_folder
    )

    # Enqueue transcoding via Celery
    job = tasks.transcode_job.delay(show_title, season, episode_number, source_abs, ep.id)
    return {"task_id": job.id, "episode_id": ep.id}

