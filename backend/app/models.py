from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base  # assuming database.py defines Base

class Show(Base):
    __tablename__ = "shows"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True, nullable=False)
    description = Column(String)
    cover_url = Column(String)

    # One show → many episodes
    episodes = relationship("Episode", back_populates="show")


class Episode(Base):
    __tablename__ = "episodes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    duration = Column(String)
    playlist_path = Column(String, nullable=False)

    # Foreign key to link episodes to their show
    show_id = Column(Integer, ForeignKey("shows.id"))

    show = relationship("Show", back_populates="episodes")



