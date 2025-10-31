from sqlalchemy.orm import Session
from . import models

def get_show_by_title(db: Session, title: str):
    return db.query(models.Show).filter(models.Show.title == title).first()

def create_show(db: Session, title: str, description: str = None, cover: str = None):
    show = models.Show(title=title, description=description, cover=cover)
    db.add(show)
    db.commit()
    db.refresh(show)
    return show

def create_episode(db: Session, show_id: int, title: str, season:int, episode_num:int, base_folder:str):
    ep = models.Episode(title=title, season_number=season, episode_number=episode_num,
                        show_id=show_id, base_folder=base_folder, status="pending")
    db.add(ep)
    db.commit()
    db.refresh(ep)
    return ep

def update_episode_ready(db: Session, episode_id: int, master_path: str, renditions: dict):
    ep = db.query(models.Episode).filter(models.Episode.id==episode_id).first()
    ep.master_path = master_path
    ep.renditions = renditions
    ep.status = "ready"
    db.commit()
    return ep

def mark_episode_failed(db: Session, episode_id: int, reason: str):
    ep = db.query(models.Episode).filter(models.Episode.id==episode_id).first()
    ep.status = "failed"
    ep.last_error = reason[:1000]
    db.commit()
    return ep
