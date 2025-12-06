// src/App.jsx
import { useState } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import ShowsPage from "./pages/ShowsPage";
import EpisodesPage from "./pages/EpisodesPage";
import AdminPage from "./pages/AdminPage";

export default function App() {
  const [selectedShow, setSelectedShow] = useState(null);

  return (
    <Router>
      <Routes>
        <Route 
          path="/" 
          element={<ShowsPage onOpenShow={setSelectedShow} />} 
        />

        <Route 
          path="/episodes/:showId" 
          element={
            selectedShow ? (
              <EpisodesPage 
                show={selectedShow} 
                onBack={() => setSelectedShow(null)}   // ✅ back button works now
              />
            ) : (
              <ShowsPage onOpenShow={setSelectedShow} />
            )
          } 
        />

        <Route path="/admin" element={<AdminPage />} />
      </Routes>
    </Router>
  );
}
