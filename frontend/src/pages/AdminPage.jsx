import { useState, useEffect } from "react";

export default function AdminPage() {
  const [shows, setShows] = useState([]);
  const [newShowTitle, setNewShowTitle] = useState("");
  const [newShowDescription, setNewShowDescription] = useState("");
  const [newShowCover, setNewShowCover] = useState(null);

  const [selectedShow, setSelectedShow] = useState("");
  const [season, setSeason] = useState("");
  const [episodeNumber, setEpisodeNumber] = useState("");
  const [episodeTitle, setEpisodeTitle] = useState("");
  const [episodeFile, setEpisodeFile] = useState(null);

  const API_URL = "http://127.0.0.1:8000";

  useEffect(() => {
    fetch(`${API_URL}/shows`)
      .then((res) => res.json())
      .then((data) => setShows(data.shows || []));
  }, []);

  function handleCreateShow(e) {
    e.preventDefault();
    const form = new FormData();
    form.append("title", newShowTitle);
    form.append("description", newShowDescription);
    if (newShowCover) {
      form.append("cover", newShowCover);
    }

    fetch(`${API_URL}/shows`, {
      method: "POST",
      body: form,
    })
      .then((res) => res.json())
      .then(() => {
        alert("Show created!");
        window.location.reload();
      })
      .catch((err) => console.error(err));
  }

  function handleCreateEpisode(e) {
    e.preventDefault();

    if (!selectedShow) {
      alert("Select a show first!");
      return;
    }

    const form = new FormData();
    form.append("show_title", selectedShow);
    form.append("season", season);
    form.append("episode_number", episodeNumber);
    form.append("title", episodeTitle);
    form.append("file", episodeFile);

    fetch(`${API_URL}/episodes/upload`, {
      method: "POST",
      body: form,
    })
      .then((res) => res.json())
      .then(() => {
        alert("Episode uploaded & transcoding started!");
      })
      .catch((err) => console.error(err));
  }

  return (
    <div className="p-10 max-w-3xl mx-auto space-y-12">

      {/* CREATE SHOW */}
      <section className="border p-6 rounded-xl shadow bg-white">
        <h2 className="text-2xl font-bold mb-4">Create New Show</h2>

        <form onSubmit={handleCreateShow} className="space-y-4">
          <input
            type="text"
            placeholder="Show Title"
            value={newShowTitle}
            onChange={(e) => setNewShowTitle(e.target.value)}
            className="w-full p-2 border rounded"
            required
          />

          <textarea
            placeholder="Description"
            value={newShowDescription}
            onChange={(e) => setNewShowDescription(e.target.value)}
            className="w-full p-2 border rounded"
          />

          <div>
            <p className="mb-1">Cover Image:</p>
            <input
              type="file"
              accept="image/*"
              onChange={(e) => setNewShowCover(e.target.files[0])}
            />
          </div>

          <button className="px-4 py-2 bg-blue-600 text-white rounded">
            Create Show
          </button>
        </form>
      </section>

      {/* CREATE EPISODE */}
      <section className="border p-6 rounded-xl shadow bg-white">
        <h2 className="text-2xl font-bold mb-4">Upload Episode</h2>

        <form onSubmit={handleCreateEpisode} className="space-y-4">
          {/* Show dropdown */}
          <select
            value={selectedShow}
            onChange={(e) => setSelectedShow(e.target.value)}
            className="w-full p-2 border rounded"
            required
          >
            <option value="">Select Show</option>
            {shows.map((s) => (
              <option key={s.id} value={s.title}>
                {s.title}
              </option>
            ))}
          </select>

          <input
            type="number"
            placeholder="Season"
            value={season}
            onChange={(e) => setSeason(e.target.value)}
            className="w-full p-2 border rounded"
            required
          />

          <input
            type="number"
            placeholder="Episode Number"
            value={episodeNumber}
            onChange={(e) => setEpisodeNumber(e.target.value)}
            className="w-full p-2 border rounded"
            required
          />

          <input
            type="text"
            placeholder="Episode Title"
            value={episodeTitle}
            onChange={(e) => setEpisodeTitle(e.target.value)}
            className="w-full p-2 border rounded"
            required
          />

          <div>
            <p className="mb-1">Episode File (MP4):</p>
            <input
              type="file"
              accept="video/mp4"
              onChange={(e) => setEpisodeFile(e.target.files[0])}
              required
            />
          </div>

          <button className="px-4 py-2 bg-green-600 text-white rounded">
            Upload Episode
          </button>
        </form>
      </section>
    </div>
  );
}

