// src/components/Chatbot.jsx
import React, { useState, useRef, useEffect } from "react";

export default function Chatbot() {
  const [messages, setMessages] = useState([
    { role: "bot", text: "Hello — describe your symptoms and I'll help triage." }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    const text = input.trim();
    setInput("");
    setMessages((m) => [...m, { role: "user", text }]);
    setLoading(true);

    try {
      const res = await fetch("http://localhost:5000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const data = await res.json();
      const reply = data.reply || "Sorry, no reply.";
      setMessages((m) => [...m, { role: "bot", text: reply }]);
    } catch (err) {
      setMessages((m) => [
        ...m,
        { role: "bot", text: "Server error — try again later." },
      ]);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="max-w-3xl mx-auto bg-white shadow-md rounded-lg p-6">
      <div className="text-center mb-4">
        <h2 className="text-2xl font-bold">Symptom Checker</h2>
      </div>

      <div className="h-80 overflow-y-auto border rounded p-3 mb-3">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`my-2 p-2 rounded ${m.role === "user" ? "text-right" : "text-left"}`}
          >
            <div
              className={`inline-block px-3 py-1 rounded ${
                m.role === "user" ? "bg-blue-100" : "bg-gray-100"
              }`}
            >
              {m.text}
            </div>
          </div>
        ))}
        <div ref={scrollRef} />
        {loading && <div className="italic text-sm">Assistant is typing…</div>}
      </div>

      <div className="flex gap-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Describe symptoms..."
          className="flex-1 border rounded p-2"
          rows={2}
        />
        <button onClick={sendMessage} className="bg-primary-500 text-white px-4 py-2 rounded">
          Send
        </button>
      </div>
    </div>
  );
}
