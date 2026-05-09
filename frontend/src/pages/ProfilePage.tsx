import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getProfile, saveApiKey } from "../services/api";
import type { UserProfile } from "../types";

export function ProfilePage() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    getProfile()
      .then(setProfile)
      .finally(() => setLoading(false));
  }, []);

  async function handleSaveKey(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSaved(false);
    try {
      await saveApiKey(apiKey);
      setSaved(true);
      setApiKey("");
      const updated = await getProfile();
      setProfile(updated);
    } catch {
      setError("Failed to save API key.");
    }
  }

  if (loading) return <div className="auth-container"><p style={{ color: "#666" }}>Loading...</p></div>;

  return (
    <div className="auth-container">
      <div className="auth-box" style={{ maxWidth: 480 }}>
        <button className="btn-ghost" style={{ marginBottom: 20 }} onClick={() => navigate("/dashboard")}>
          ← Back
        </button>

        <h1 className="auth-title">Profile</h1>

        {profile && (
          <>
            <p style={{ color: "#888", marginBottom: 24 }}>
              Logged in as <strong style={{ color: "#e0e0e0" }}>{profile.username}</strong>
            </p>

            <div className="profile-trial-box">
              <p className="profile-trial-label">Free trial</p>
              <div className="profile-trial-remaining">
                <span className="profile-trial-number">{profile.trial_remaining}</span>
                <span className="profile-trial-of"> / {profile.trial_limit} interactions remaining</span>
              </div>
              <div className="profile-trial-bar-bg">
                <div
                  className="profile-trial-bar-fill"
                  style={{ width: `${(profile.trial_interactions_used / profile.trial_limit) * 100}%` }}
                />
              </div>
              <p className="profile-trial-count">
                {profile.trial_interactions_used} used
                {profile.trial_remaining === 0 && " — Trial exhausted, add your API key below"}
              </p>
            </div>

            <div className="profile-key-status">
              {profile.has_own_key ? (
                <p className="profile-key-ok">✓ Your OpenAI API key is saved</p>
              ) : (
                <p className="profile-key-missing">No API key — add yours below to continue after the trial</p>
              )}
            </div>
          </>
        )}

        <form onSubmit={handleSaveKey} className="auth-form" style={{ marginTop: 20 }}>
          <input
            className="auth-input"
            type="password"
            placeholder="sk-..."
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            required
          />
          {error && <p className="auth-error">{error}</p>}
          {saved && <p style={{ color: "#4ade80", fontSize: "0.85rem" }}>API key saved.</p>}
          <button className="auth-button" type="submit">
            Save API Key
          </button>
        </form>
      </div>
    </div>
  );
}
