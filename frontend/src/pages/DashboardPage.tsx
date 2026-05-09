import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getCharacters } from "../services/api";
import { useAuth } from "../context/AuthContext";
import type { Character } from "../types";

export function DashboardPage() {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);
  const { logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    getCharacters()
      .then(setCharacters)
      .catch(() => logout())
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>Your Characters</h1>
        <div className="dashboard-header-actions">
          <button className="btn-primary" onClick={() => navigate("/characters/create")}>
            + New Character
          </button>
          <button className="btn-ghost" onClick={() => navigate("/profile")}>
            Profile
          </button>
          <button className="btn-ghost" onClick={logout}>
            Log out
          </button>
        </div>
      </header>

      {loading ? (
        <p className="dashboard-empty">Loading...</p>
      ) : characters.length === 0 ? (
        <p className="dashboard-empty">No characters yet. Create your first one!</p>
      ) : (
        <div className="character-grid">
          {characters.map((c) => (
            <div
              key={c.id}
              className="character-card"
              onClick={() => navigate(`/characters/${c.id}/chat`)}
            >
              <h2>{c.name}</h2>
              <p className="character-mood">Mood: {c.mood}</p>
              {c.description && <p className="character-desc">{c.description}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
