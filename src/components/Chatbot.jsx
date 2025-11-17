// // src/components/Chatbot.jsx
// import React, { useState, useRef, useEffect } from "react";

// export default function Chatbot() {
//   const [messages, setMessages] = useState([
//     { role: "bot", text: "Hello — describe your symptoms and I'll help triage." }
//   ]);
//   const [input, setInput] = useState("");
//   const [loading, setLoading] = useState(false);
//   const scrollRef = useRef(null);

//   useEffect(() => {
//     scrollRef.current?.scrollIntoView({ behavior: "smooth" });
//   }, [messages, loading]);

//   const sendMessage = async () => {
//     if (!input.trim()) return;
//     const text = input.trim();
//     setInput("");
//     setMessages((m) => [...m, { role: "user", text }]);
//     setLoading(true);

//     try {
//       const res = await fetch("http://localhost:5000/api/chat", {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({ message: text }),
//       });
//       const data = await res.json();
//       const reply = data.reply || "Sorry, no reply.";
//       setMessages((m) => [...m, { role: "bot", text: reply }]);
//     } catch (err) {
//       setMessages((m) => [
//         ...m,
//         { role: "bot", text: "Server error — try again later." },
//       ]);
//       console.error(err);
//     } finally {
//       setLoading(false);
//     }
//   };

//   const onKeyDown = (e) => {
//     if (e.key === "Enter" && !e.shiftKey) {
//       e.preventDefault();
//       sendMessage();
//     }
//   };

//   return (
//     <div className="max-w-3xl mx-auto bg-white shadow-md rounded-lg p-6">
//       <div className="text-center mb-4">
//         <h2 className="text-2xl font-bold">Symptom Checker</h2>
//       </div>

//       <div className="h-80 overflow-y-auto border rounded p-3 mb-3">
//         {messages.map((m, i) => (
//           <div
//             key={i}
//             className={`my-2 p-2 rounded ${m.role === "user" ? "text-right" : "text-left"}`}
//           >
//             <div
//               className={`inline-block px-3 py-1 rounded ${
//                 m.role === "user" ? "bg-blue-100" : "bg-gray-100"
//               }`}
//             >
//               {m.text}
//             </div>
//           </div>
//         ))}
//         <div ref={scrollRef} />
//         {loading && <div className="italic text-sm">Assistant is typing…</div>}
//       </div>

//       <div className="flex gap-2">
//         <textarea
//           value={input}
//           onChange={(e) => setInput(e.target.value)}
//           onKeyDown={onKeyDown}
//           placeholder="Describe symptoms..."
//           className="flex-1 border rounded p-2"
//           rows={2}
//         />
//         <button onClick={sendMessage} className="bg-primary-500 text-white px-4 py-2 rounded">
//           Send
//         </button>
//       </div>
//     </div>
//   );
// }
// src/components/Chatbot.jsx
import React, { useState, useRef, useEffect } from "react";

export default function Chatbot() {
  const [messages, setMessages] = useState([
    { role: "bot", text: "Hello — describe your symptoms and I'll help triage." }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const scrollRef = useRef(null);

  useEffect(() => { scrollRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text) return;
    setInput("");
    setError(null);
    setMessages(m => [...m, { role: "user", text }]);
    setLoading(true);

    try {
      // If you used Vite proxy use "/api/chat", otherwise use "http://localhost:5000/api/chat"
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });

      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}));
        throw new Error(errBody.error || `Server ${res.status}`);
      }

      const data = await res.json();
      // backend returns: { plain_text, candidates, recommended_action, follow_up_questions, disclaimer }
      const botText = data.plain_text || data.recommended_action || "No response.";
      setMessages(m => [...m, { role: "bot", text: botText, structured: data }]);
    } catch (err) {
      console.error("Chat error:", err);
      setError(err.message || "Network error");
      setMessages(m => [...m, { role: "bot", text: "Sorry — failed to fetch reply." }]);
    } finally {
      setLoading(false);
    }
  };

  const onKeyDown = (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } };

  return (
    <div className="max-w-3xl mx-auto bg-white shadow-md rounded-lg p-6">
      <div className="text-center mb-4"><h2 className="text-2xl font-bold">Symptom Checker</h2></div>

      <div className="h-80 overflow-y-auto border rounded p-3 mb-3">
        {messages.map((m, i) => (
          <div key={i} className={`my-2 p-2 rounded ${m.role === "user" ? "text-right" : "text-left"}`}>
            <div className={`inline-block px-3 py-1 rounded ${m.role === "user" ? "bg-blue-100" : "bg-gray-100"}`}>
              {m.text}
            </div>

            {m.structured && m.role === "bot" && (
              <div className="mt-2 text-left text-sm bg-gray-50 p-2 rounded">
                {m.structured.candidates?.length > 0 && (
                  <div className="mb-2">
                    <b>Possible conditions:</b>
                    <ul className="list-disc ml-6">
                      {m.structured.candidates.map((c, idx) => (
                        <li key={idx}>
                          {c.condition} — {(c.confidence ?? 0).toFixed(2)}
                          {c.evidence?.length > 0 && <div className="text-xs text-gray-600">evidence: {c.evidence.join(", ")}</div>}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {m.structured.recommended_action && <div className="mb-1"><b>Recommended:</b> {m.structured.recommended_action}</div>}
                {m.structured.follow_up_questions?.length > 0 && <div><b>Follow-up:</b> {m.structured.follow_up_questions.join(" · ")}</div>}
                {m.structured.disclaimer && <div className="mt-2 text-xs text-gray-500">{m.structured.disclaimer}</div>}
              </div>
            )}
          </div>
        ))}
        <div ref={scrollRef} />
        {loading && <div className="italic text-sm">Assistant is typing…</div>}
      </div>

      {error && <div className="text-red-600 mb-2">Error: {error}</div>}

      <div className="flex gap-2">
        <textarea value={input} onChange={(e)=>setInput(e.target.value)} onKeyDown={onKeyDown}
          placeholder="Describe symptoms..." className="flex-1 border rounded p-2" rows={2}/>
        <button onClick={sendMessage} className="bg-primary-500 text-white px-4 py-2 rounded" disabled={loading}>Send</button>
      </div>
    </div>
  );
}
