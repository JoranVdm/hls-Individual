import os
from slugify import slugify

def make_paths(show_title: str, season: int, episode_num: int):
    show_slug = slugify(show_title)
    season_folder = f"Season{season}"
    episode_folder = f"Episode{episode_num}"
    base = os.path.join(show_slug, season_folder, episode_folder)
    return show_slug, season_folder, episode_folder, base
