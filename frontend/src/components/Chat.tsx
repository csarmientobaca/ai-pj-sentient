import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import type { Message } from "../types";
import { sendMessage } from "../services/api";

export function Chat() {
  const { characterId } = useParams<{ characterId: string }>();
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [characterName, setCharacterName] = useState("Character");
  const bottomRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSend() {
    if (!input.trim() || loading) return;
    const text = input;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text }]);
    setLoading(true);

    try {
      const data = await sendMessage(Number(characterId), text);
      setCharacterName(data.character);
      setMessages((prev) => [...prev, { role: "character", text: data.response }]);
    } catch (err: any) {
      const msg = err?.response?.data?.error || "Error — is Django running?";
      setMessages((prev) => [...prev, { role: "character", text: msg }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="chat-container">
      <header className="chat-header">
        <button className="btn-ghost back-btn" onClick={() => navigate("/dashboard")}>
          ← Back
        </button>
        <span className="chat-header-name">{characterName}</span>
      </header>

      <div className="chat-messages">
        {messages.length === 0 && (
          <p className="chat-empty">Say something to start the conversation.</p>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`bubble-row ${msg.role}`}>
            <div className={`bubble ${msg.role}`}>{msg.text}</div>
          </div>
        ))}
        {loading && (
          <div className="bubble-row character">
            <div className="bubble character typing">
              <span /><span /><span />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="chat-input-row">
        <input
          className="chat-input"
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Type a message..."
          disabled={loading}
        />
        <button className="chat-send" onClick={handleSend} disabled={loading}>
          Send
        </button>
      </div>
    </div>
  );
}
