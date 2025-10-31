from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .database import Base

class Show(Base):
    __tablename__ = "shows"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    cover = Column(String, nullable=True)  # path like "covers/Naruto.jpg"
    episodes = relationship("Episode", back_populates="show", cascade="all, delete-orphan")

class Episode(Base):
    __tablename__ = "episodes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    season_number = Column(Integer, default=1)
    episode_number = Column(Integer, default=1)
    duration = Column(String, nullable=True)
    master_path = Column(String, nullable=True)   # e.g. "SouthPark/Season1/Episode1/master.m3u8"
    base_folder = Column(String, nullable=True)   # e.g. "SouthPark/Season1/Episode1/"
    status = Column(String, default="pending")    # pending, processing, ready, failed
    renditions = Column(JSON, nullable=True)
    show_id = Column(Integer, ForeignKey("shows.id"))
    show = relationship("Show", back_populates="episodes")
    last_error = Column(String, nullable=True)
