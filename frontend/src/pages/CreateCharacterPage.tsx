import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createCharacter } from "../services/api";

export function CreateCharacterPage() {
  const [name, setName] = useState("");
  const [personality, setPersonality] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const character = await createCharacter(name, personality, description);
      navigate(`/characters/${character.id}/chat`);
    } catch {
      setError("Failed to create character.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-container">
      <div className="auth-box" style={{ maxWidth: 520 }}>
        <h1 className="auth-title">New Character</h1>
        <form onSubmit={handleSubmit} className="auth-form">
          <input
            className="auth-input"
            type="text"
            placeholder="Name (e.g. Spider-Man)"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <textarea
            className="auth-input"
            placeholder="Personality (e.g. witty, sarcastic, heroic)"
            value={personality}
            onChange={(e) => setPersonality(e.target.value)}
            rows={3}
          />
          <textarea
            className="auth-input"
            placeholder="Description (optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
          />
          {error && <p className="auth-error">{error}</p>}
          <button className="auth-button" type="submit" disabled={loading}>
            {loading ? "Creating..." : "Create & Start Chatting"}
          </button>
          <button
            type="button"
            className="btn-ghost"
            style={{ width: "100%" }}
            onClick={() => navigate("/dashboard")}
          >
            Cancel
          </button>
        </form>
      </div>
    </div>
  );
}
