import { useState, useEffect, useRef } from "react";
import type { Message } from "../types";
import { sendMessage } from "../services/api";

export function Chat() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

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
      const data = await sendMessage(1, text);
      setMessages((prev) => [...prev, { role: "character", text: data.response }]);
    } catch {
      setMessages((prev) => [...prev, { role: "character", text: "Error — is Django running?" }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="chat-container">
      <header className="chat-header">
        <h1>Spider-Man</h1>
      </header>

      <div className="chat-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`bubble-row ${msg.role}`}>
            <div className={`bubble ${msg.role}`}>{msg.text}</div>
          </div>
        ))}
        {loading && (
          <div className="bubble-row character">
            <div className="bubble character">...</div>
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
