import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from app.database import SessionLocal
from app.models import Show, Episode

# Initialize FastAPI app
app = FastAPI()

# Allow your frontend origin
origins = [
    "http://localhost:3000",  # React dev server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to static video directory
COVER_DIR = os.path.join(os.path.dirname(__file__), "Cover")
app.mount("/covers", StaticFiles(directory=COVER_DIR), name="covers")

VIDEO_DIR = os.path.join(os.path.dirname(__file__), "videos")

# Mount static file serving for videos (e.g. HLS .m3u8 + .ts files)
app.mount("/videos", StaticFiles(directory=VIDEO_DIR), name="videos")

# Database session dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"message": "✅ HLS backend with PostgreSQL is running"}


# -------------------------
# SHOW ENDPOINTS
# -------------------------

@app.get("/shows")
def list_shows(db: Session = Depends(get_db)):
    """
    Returns a list of all shows.
    """
    shows = db.query(Show).all()
    return {
        "shows": [
            {
                "id": s.id,
                "title": s.title,
                "description": s.description,
                "cover_url": s.cover_url,
            }
            for s in shows
        ]
    }


@app.get("/shows/{show_id}/episodes")
def list_episodes(show_id: int, db: Session = Depends(get_db)):
    """
    Returns all episodes for a given show.
    """
    show = (
        db.query(Show)
        .options(joinedload(Show.episodes))
        .filter(Show.id == show_id)
        .first()
    )

    if not show:
        raise HTTPException(status_code=404, detail="Show not found")

    episodes = [
        {
            "id": ep.id,
            "title": ep.title,
            "duration": ep.duration,
            "playlist_path": ep.playlist_path,
        }
        for ep in show.episodes
    ]

    return {"show": show.title, "episodes": episodes}


@app.get("/shows/{show_id}/playlist/{episode_id}")
def get_episode_playlist(show_id: int, episode_id: int, db: Session = Depends(get_db)):
    """
    Returns the playlist URL (.m3u8) for a specific episode.
    """
    episode = (
        db.query(Episode)
        .filter(Episode.id == episode_id, Episode.show_id == show_id)
        .first()
    )

    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    # The playlist path is stored relative to the /videos directory
    playlist_url = f"/videos/{episode.playlist_path}"
    return {"episode": episode.title, "playlist": playlist_url}
