import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { createCharacter, getPresetCharacters, generateCharacter } from "../services/api";

type Mode = "select" | "preset" | "generate" | "manual";
type Preset = { name: string; personality: string; description: string };

export function CreateCharacterPage() {
  const [mode, setMode] = useState<Mode>("select");
  const [presets, setPresets] = useState<Preset[]>([]);
  const [name, setName] = useState("");
  const [personality, setPersonality] = useState("");
  const [description, setDescription] = useState("");
  const [generateName, setGenerateName] = useState("");
  const [generated, setGenerated] = useState<Preset | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    getPresetCharacters().then(setPresets).catch(() => {});
  }, []);

  async function handleGenerate() {
    if (!generateName.trim()) return;
    setError("");
    setLoading(true);
    try {
      const result = await generateCharacter(generateName.trim());
      setGenerated(result);
    } catch {
      setError("Failed to generate character. Try again.");
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate(p: Preset) {
    setError("");
    setLoading(true);
    try {
      const character = await createCharacter(p.name, p.personality, p.description);
      navigate(`/characters/${character.id}/chat`);
    } catch {
      setError("Failed to create character.");
      setLoading(false);
    }
  }

  async function handleManualSubmit(e: React.FormEvent) {
    e.preventDefault();
    await handleCreate({ name, personality, description });
  }

  if (mode === "select") {
    return (
      <div className="auth-container">
        <div className="auth-box" style={{ maxWidth: 560 }}>
          <button className="btn-ghost" style={{ marginBottom: 20 }} onClick={() => navigate("/dashboard")}>
            ← Back
          </button>
          <h1 className="auth-title">New Character</h1>
          <p style={{ color: "#888", marginBottom: 32, textAlign: "center" }}>How do you want to create your character?</p>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <button className="auth-button" onClick={() => setMode("preset")}>
              Pick a preset character
            </button>
            <button className="auth-button" style={{ background: "#1e293b" }} onClick={() => setMode("generate")}>
              Generate from name with AI
            </button>
            <button className="btn-ghost" onClick={() => setMode("manual")}>
              Build manually
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (mode === "preset") {
    return (
      <div className="auth-container">
        <div className="auth-box" style={{ maxWidth: 600 }}>
          <button className="btn-ghost" style={{ marginBottom: 20 }} onClick={() => setMode("select")}>
            ← Back
          </button>
          <h1 className="auth-title">Pick a Character</h1>
          {error && <p className="auth-error">{error}</p>}
          <div style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 16 }}>
            {presets.map((p) => (
              <div key={p.name} style={{ background: "#1e293b", borderRadius: 10, padding: "16px 20px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <p style={{ color: "#e0e0e0", fontWeight: 600, marginBottom: 4 }}>{p.name}</p>
                  <p style={{ color: "#888", fontSize: "0.82rem", maxWidth: 380 }}>{p.personality.slice(0, 100)}...</p>
                </div>
                <button
                  className="auth-button"
                  style={{ width: "auto", padding: "8px 20px", marginLeft: 16, flexShrink: 0 }}
                  disabled={loading}
                  onClick={() => handleCreate(p)}
                >
                  {loading ? "..." : "Select"}
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (mode === "generate") {
    return (
      <div className="auth-container">
        <div className="auth-box" style={{ maxWidth: 520 }}>
          <button className="btn-ghost" style={{ marginBottom: 20 }} onClick={() => { setMode("select"); setGenerated(null); }}>
            ← Back
          </button>
          <h1 className="auth-title">Generate from Name</h1>
          <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
            <input
              className="auth-input"
              style={{ margin: 0, flex: 1 }}
              type="text"
              placeholder="e.g. Darth Vader, Sherlock Holmes..."
              value={generateName}
              onChange={(e) => { setGenerateName(e.target.value); setGenerated(null); }}
              onKeyDown={(e) => e.key === "Enter" && handleGenerate()}
            />
            <button className="auth-button" style={{ width: "auto", padding: "0 20px", margin: 0 }} onClick={handleGenerate} disabled={loading || !generateName.trim()}>
              {loading ? "..." : "Generate"}
            </button>
          </div>
          {error && <p className="auth-error" style={{ marginTop: 8 }}>{error}</p>}

          {generated && (
            <div style={{ marginTop: 24, background: "#1e293b", borderRadius: 10, padding: 20 }}>
              <p style={{ color: "#e0e0e0", fontWeight: 600, fontSize: "1.1rem", marginBottom: 12 }}>{generated.name}</p>
              <p style={{ color: "#aaa", fontSize: "0.85rem", marginBottom: 8 }}><strong style={{ color: "#e0e0e0" }}>Personality:</strong> {generated.personality}</p>
              <p style={{ color: "#aaa", fontSize: "0.85rem", marginBottom: 20 }}><strong style={{ color: "#e0e0e0" }}>Description:</strong> {generated.description}</p>
              <div style={{ display: "flex", gap: 8 }}>
                <button className="auth-button" disabled={loading} onClick={() => handleCreate(generated)}>
                  {loading ? "Creating..." : "Create & Start Chatting"}
                </button>
                <button className="btn-ghost" onClick={() => setGenerated(null)}>
                  Regenerate
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="auth-container">
      <div className="auth-box" style={{ maxWidth: 520 }}>
        <button className="btn-ghost" style={{ marginBottom: 20 }} onClick={() => setMode("select")}>
          ← Back
        </button>
        <h1 className="auth-title">Build Manually</h1>
        <form onSubmit={handleManualSubmit} className="auth-form">
          <input
            className="auth-input"
            type="text"
            placeholder="Name"
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
        </form>
      </div>
    </div>
  );
}
