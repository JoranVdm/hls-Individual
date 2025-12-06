import { useEffect, useState } from "react";
import { getEpisodes } from "../api/api";
import EpisodeCard from "../components/EpisodeCard";
import VideoPlayer from "../components/VideoPlayer";
import { useNavigate } from "react-router-dom";

export default function EpisodesPage({ show, onBack }) {
    const navigate = useNavigate();
  const [episodes, setEpisodes] = useState([]);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    fetchEpisodes();

    // Polling every 5 seconds (like your old frontend)
    const interval = setInterval(fetchEpisodes, 5000);
    return () => clearInterval(interval);

  }, [show]);

  function fetchEpisodes() {
    getEpisodes(show.id).then(data => {
      setEpisodes(data.episodes || []);
    });
  }

  return (
    <div>
      <button 
        onClick={() => {
          onBack();        // updates openShow
          navigate("/");   // sends user back to the shows page
        }} 
        className="mb-4 px-4 py-2 bg-blue-500 text-white rounded"
      >
        ← Back
      </button>

      <h1 className="text-xl mb-4">{show.title}</h1>

      <div className="grid gap-2">
        {episodes.map(ep => (
          <EpisodeCard 
            key={ep.id} 
            episode={ep} 
            onClick={() => setSelected(ep)}
          />
        ))}
      </div>

      {selected && (
        <div className="mt-4">
          <VideoPlayer episode={selected} showId={show.id} />
        </div>
      )}
    </div>
  );
}
