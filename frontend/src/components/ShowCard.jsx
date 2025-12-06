// src/components/ShowCard.jsx

const API_URL = "http://127.0.0.1:8000";

export default function ShowCard({ show, onClick }) {
  return (
    <div
      className="border rounded-xl cursor-pointer shadow-sm hover:shadow-md transition overflow-hidden bg-white"
      onClick={onClick}
    >
      {/* Cover image */}
      {show.cover_url ? (
        <img
          src={`${API_URL}${show.cover_url}`}
          alt={show.title}
          className="w-full h-48 object-cover"
        />
      ) : (
        <div className="w-full h-48 bg-gray-200 flex items-center justify-center text-gray-500">
          No Image
        </div>
      )}

      {/* Info */}
      <div className="p-4">
        <h2 className="font-bold text-xl mb-1">{show.title}</h2>
        <p className="text-gray-600 text-sm">{show.description}</p>
      </div>
    </div>
  );
}
