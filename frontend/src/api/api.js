const BASE = "http://127.0.0.1:8000";

export async function getShows() {
  return fetch(`${BASE}/shows`).then(res => res.json());
}

export async function getEpisodes(showId) {
  return fetch(`${BASE}/shows/${showId}/episodes`).then(res => res.json());
}

export async function uploadEpisode(formData) {
  return fetch(`${BASE}/episodes/upload`, {
    method: "POST",
    body: formData
  }).then(res => res.json());
}

export function getPlaylistUrl(showId, episodeId) {
  return `${BASE}/shows/${showId}/playlist/${episodeId}`;
}
