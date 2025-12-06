export default function EpisodeCard({ episode, onClick }) {
  return (
    <div 
      className="p-3 border rounded cursor-pointer"
      onClick={onClick}
    >
      <p className="font-bold">{episode.title}</p>
      <p>Status: {episode.status}</p>
    </div>
  );
}
