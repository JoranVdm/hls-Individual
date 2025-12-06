import { useEffect, useState } from "react";
import { getShows } from "../api/api";
import ShowCard from "../components/ShowCard";
import { useNavigate } from "react-router-dom";

export default function ShowsPage({ onOpenShow }) {
  const [shows, setShows] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    getShows().then(data => setShows(data.shows || []));
  }, []);

  const handleClick = (show) => {
    onOpenShow(show);
    navigate(`/episodes/${show.id}`);
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Shows</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {shows.map(show => (
          <ShowCard 
            key={show.id} 
            show={show} 
            onClick={() => handleClick(show)}
          />
        ))}
      </div>
    </div>
  );
}
