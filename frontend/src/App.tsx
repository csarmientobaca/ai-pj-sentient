import "./App.css";
import { useState, useEffect, useRef } from "react";
import axios from "axios";

interface Message {
  role: "user" | "character";
  text: string;
}

interface ApiResponse {
  character: string;
  response: string;
}



function App() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  const bottomRef = useRef<HTMLDivElement>(null);


  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function sendMessage() {
    if (!input.trim() || loading) return;
    const text = input;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text }]);
    setLoading(true);

    try {
      const { data } = await axios.post<ApiResponse>(
        `http://localhost:8000/characters/1/talk/`,
        { message: text }
      );
      setMessages((prev) => [...prev, { role: "character", text: data.response }]);
    } catch{
      setMessages((prev) => [...prev, { role: "character", text: "Error: Django up?" }]);
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
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Type a message..."
          disabled={loading}
        />
        <button className="chat-send" onClick={sendMessage} disabled={loading}>
          Send
        </button>
      </div>
    </div>
  );
}



export default App;