from celery import shared_task
from sqlalchemy.orm import Session
from cache.redis_cache import cache
import models

@shared_task
def refresh_show_cache():
    from main import get_db
    # Open a new DB session
    db: Session = next(get_db())

    try:
        shows = db.query(models.Show).all()
        result = [
            {
                "id": s.id,
                "title": s.title,
                "description": s.description,
                "cover_url": s.cover,
            }
            for s in shows
        ]
        # Update Redis cache with TTL 5 minutes
        cache.set("all_shows", result, ttl_seconds=300)
    finally:
        db.close()

    return True
