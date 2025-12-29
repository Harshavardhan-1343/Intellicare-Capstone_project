import React, { useState, useRef, useEffect } from "react";
import { Send, User, Bot, RotateCcw, FileText, ChevronDown } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function Chatbot() {
  const [messages, setMessages] = useState([
    { role: "bot", text: "Hello! I'm your medical assistant. Describe your symptoms and I'll help assess and triage your condition." }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [latestReport, setLatestReport] = useState(null);
  const [isComplete, setIsComplete] = useState(false);  // NEW: Track if diagnosis is complete
  const scrollRef = useRef(null);
  const textareaRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = textareaRef.current.scrollHeight + "px";
    }
  }, [input]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text) return;
    setInput("");
    setError(null);
    setMessages(m => [...m, { role: "user", text }]);
    setLoading(true);

    try {
      const requestBody = { message: text };
      if (sessionId) {
        requestBody.session_id = sessionId;
      }

      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      });

      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}));
        throw new Error(errBody.error || `Server ${res.status}`);
      }

      const data = await res.json();
      console.log("Backend response:", data);

      const botText = data.response || "No response.";
      const isFinal = data.is_final || false;
      const diagnosisData = data.diagnosis_data;
      const report = data.report;

      if (data.session_id && !sessionId) {
        setSessionId(data.session_id);
      }

      // NEW: If diagnosis is complete, show custom message instead of diagnosis
      if (isFinal) {
        setMessages(m => [...m, {
          role: "bot",
          text: "Your conditions have been analyzed and results are ready. Please click the 'View Report' button below to see your detailed medical assessment.",
          isFinal: true
        }]);
        
        setLatestReport({
          report,
          diagnosisData,
          timestamp: new Date().toISOString(),
          patientData: diagnosisData?.patient || {}
        });
        
        setIsComplete(true);  // Mark as complete
      } else {
        // Normal conversation message
        setMessages(m => [...m, {
          role: "bot",
          text: botText,
          isFinal: false
        }]);
      }

    } catch (err) {
      console.error("Chat error:", err);
      setError(err.message || "Network error");
      setMessages(m => [...m, { role: "bot", text: "Sorry — failed to fetch reply. Please try again." }]);
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

  const resetConversation = () => {
    setMessages([
      { role: "bot", text: "Hello! I'm your medical assistant. Describe your symptoms and I'll help assess and triage your condition." }
    ]);
    setSessionId(null);
    setError(null);
    setLatestReport(null);
    setIsComplete(false);  // Reset completion state
  };

  const viewFullReport = () => {
    if (latestReport) {
      sessionStorage.setItem('medicalReport', JSON.stringify(latestReport));
      navigate('/report');
    }
  };

  return (
    <>
      {/* Global Dark Blue Background Wrapper */}
      <div className="chatbot-page-wrapper">
        
        {/* Centered Chat Container */}
        <div className="chatbot-container">
          
          {/* Header */}
          <div className="flex-shrink-0 backdrop-blur-xl bg-black/30 border-b border-white/10">
            <div className="px-4 md:px-6 py-4 flex justify-between items-center gap-3">
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-10 h-10 md:w-12 md:h-12 rounded-2xl bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/50 flex-shrink-0">
                  <Bot className="w-5 h-5 md:w-6 md:h-6 text-white" />
                </div>
                <div className="min-w-0">
                  <h1 className="text-lg md:text-xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent truncate">
                    Intellicare AI Assistant
                  </h1>
                  <p className="text-[10px] md:text-xs text-gray-400 truncate">Powered by IntelliCare</p>
                </div>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <button
                  onClick={resetConversation}
                  className="flex items-center gap-2 px-3 md:px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 transition-all duration-300 hover:scale-105 group"
                >
                  <RotateCcw className="w-4 h-4 group-hover:rotate-180 transition-transform duration-500 text-white" />
                  <span className="text-sm font-medium hidden md:inline text-white">New Chat</span>
                </button>
              </div>
            </div>
          </div>

          {/* Chat Messages Container */}
          <div className="flex-1 overflow-y-auto px-4 md:px-6 py-6">
            <div className="space-y-6">
              {messages.map((m, i) => (
                <div
                  key={i}
                  className={`message-fade-in flex gap-3 md:gap-4 ${m.role === "user" ? "flex-row-reverse" : "flex-row"}`}
                >
                  {/* Avatar */}
                  <div className={`flex-shrink-0 w-8 h-8 md:w-10 md:h-10 rounded-xl flex items-center justify-center ${
                    m.role === "user"
                      ? "bg-gradient-to-br from-purple-500 to-pink-600 shadow-lg shadow-purple-500/50"
                      : "bg-gradient-to-br from-cyan-400 to-blue-600 shadow-lg shadow-cyan-500/50"
                  }`}>
                    {m.role === "user" ? (
                      <User className="w-4 h-4 md:w-5 md:h-5 text-white" />
                    ) : (
                      <Bot className="w-4 h-4 md:w-5 md:h-5 text-white" />
                    )}
                  </div>

                  {/* Message Content */}
                  <div className={`flex-1 ${m.role === "user" ? "items-end" : "items-start"} flex flex-col gap-3 min-w-0`}>
                    {/* Main Message Bubble */}
                    <div
                      className={`relative px-4 md:px-6 py-3 md:py-4 rounded-2xl max-w-[85%] md:max-w-[75%] ${
                        m.role === "user"
                          ? "bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-xl shadow-purple-500/30 ml-auto"
                          : "bg-white/5 backdrop-blur-xl border border-white/10 text-gray-100 shadow-xl"
                      }`}
                    >
                      <div className="whitespace-pre-wrap break-words leading-relaxed text-sm md:text-[15px]">
                        {m.text}
                      </div>
                    </div>
                  </div>
                </div>
              ))}

              {/* Typing Indicator */}
              {loading && (
                <div className="flex gap-3 md:gap-4 message-fade-in">
                  <div className="w-8 h-8 md:w-10 md:h-10 rounded-xl bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/50">
                    <Bot className="w-4 h-4 md:w-5 md:h-5 text-white" />
                  </div>
                  <div className="glassmorphism-card px-4 md:px-6 py-3 md:py-4 rounded-2xl">
                    <div className="flex gap-1.5 md:gap-2 items-center">
                      <div className="typing-dot"></div>
                      <div className="typing-dot" style={{ animationDelay: "0.2s" }}></div>
                      <div className="typing-dot" style={{ animationDelay: "0.4s" }}></div>
                    </div>
                  </div>
                </div>
              )}

              <div ref={scrollRef} />
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="px-4 md:px-6 pb-2 flex-shrink-0">
              <div className="glassmorphism-card border-l-4 border-red-500 p-3 md:p-4 rounded-xl flex items-center gap-3 animate-shake">
                <span className="text-red-400 text-lg md:text-xl flex-shrink-0">⚠️</span>
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-red-400 text-sm md:text-base">Error</div>
                  <div className="text-xs md:text-sm text-gray-300 truncate">{error}</div>
                </div>
              </div>
            </div>
          )}

          {/* Input Area or View Report Button */}
          <div className="flex-shrink-0 backdrop-blur-xl bg-black/30 border-t border-white/10">
            <div className="px-4 md:px-6 py-3 md:py-4">
              {!isComplete ? (
                // Show input area during conversation
                <>
                  <div className="relative flex items-end gap-2 md:gap-3">
                    <div className="flex-1 relative">
                      <textarea
                        ref={textareaRef}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={onKeyDown}
                        placeholder="Describe your symptoms..."
                        disabled={loading}
                        rows={1}
                        className="w-full px-4 md:px-6 py-3 md:py-4 pr-12 md:pr-16 bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl md:rounded-2xl 
                                 text-gray-100 placeholder-gray-500 resize-none focus:outline-none focus:ring-2 
                                 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all duration-300
                                 disabled:opacity-50 disabled:cursor-not-allowed max-h-32 md:max-h-48 overflow-y-auto text-sm md:text-[15px]"
                        style={{ minHeight: "48px" }}
                      />
                      <div className="absolute bottom-3 md:bottom-4 right-3 md:right-4 text-[10px] md:text-xs text-gray-500">
                        {input.length}/4000
                      </div>
                    </div>
                    <button
                      onClick={sendMessage}
                      disabled={loading || !input.trim()}
                      className="flex-shrink-0 w-12 h-12 md:w-14 md:h-14 rounded-xl md:rounded-2xl bg-gradient-to-r from-cyan-500 to-blue-600 
                               hover:from-cyan-400 hover:to-blue-500 disabled:from-gray-600 disabled:to-gray-700
                               flex items-center justify-center transition-all duration-300 hover:scale-105 
                               disabled:scale-100 disabled:cursor-not-allowed shadow-lg shadow-cyan-500/50 
                               disabled:shadow-none group"
                    >
                      <Send className="w-5 h-5 md:w-6 md:h-6 text-white group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                    </button>
                  </div>
                  {sessionId && (
                    <div className="mt-2 text-[10px] md:text-xs text-gray-500 flex items-center gap-2">
                      <div className="w-1.5 h-1.5 md:w-2 md:h-2 rounded-full bg-green-400 animate-pulse"></div>
                      <span className="truncate">Session: {sessionId.slice(0, 8)}...</span>
                    </div>
                  )}
                </>
              ) : (
                // Show View Report button after diagnosis
                <button
                  onClick={viewFullReport}
                  className="w-full py-4 md:py-5 rounded-2xl bg-gradient-to-r from-green-500 to-emerald-600 
                           hover:from-green-400 hover:to-emerald-500 transition-all duration-300 hover:scale-[1.02]
                           shadow-lg shadow-green-500/50 hover:shadow-green-500/70 flex items-center justify-center gap-3 group"
                >
                  <FileText className="w-6 h-6 md:w-7 md:h-7 text-white group-hover:scale-110 transition-transform" />
                  <span className="text-lg md:text-xl font-bold text-white">View Detailed Report</span>
                  <ChevronDown className="w-5 h-5 md:w-6 md:h-6 text-white -rotate-90 group-hover:translate-x-1 transition-transform" />
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Global Styles */}
      <style jsx>{`
  /* Global Page Wrapper - Dark Blue Background */
  .chatbot-page-wrapper {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    width: 100vw;
    height: 100vh;
    background: linear-gradient(135deg, #1a2332 0%, #243447 50%, #2d3e54 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
    overflow: hidden;
    z-index: 0;
  }

  /* Chat Container - Centered Dark Card */
  .chatbot-container {
    position: relative;
    width: 100%;
    max-width: 1000px;
    height: calc(100vh - 2rem);
    display: flex;
    flex-direction: column;
    background: linear-gradient(135deg, #0f172a 0%, #1e1e2e 50%, #1a1a2e 100%);
    border-radius: 1.5rem;
    box-shadow: 
      0 25px 50px -12px rgba(0, 0, 0, 0.6),
      0 0 0 1px rgba(255, 255, 255, 0.05),
      0 0 100px rgba(6, 182, 212, 0.1);
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.05);
  }

  /* Mobile: Full screen */
  @media (max-width: 768px) {
    .chatbot-page-wrapper {
      padding: 0;
    }
    
    .chatbot-container {
      max-width: 100%;
      height: 100vh;
      border-radius: 0;
      box-shadow: none;
    }
  }

  /* Animations */
  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  @keyframes bounce {
    0%, 60%, 100% {
      transform: translateY(0);
    }
    30% {
      transform: translateY(-8px);
    }
  }

  @keyframes shake {
    0%, 100% { transform: translateX(0); }
    25% { transform: translateX(-5px); }
    75% { transform: translateX(5px); }
  }

  .message-fade-in {
    animation: fadeIn 0.4s ease-out;
  }

  .animate-slide-up {
    animation: slideUp 0.5s ease-out;
  }

  .animate-shake {
    animation: shake 0.3s ease-in-out;
  }

  .typing-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: linear-gradient(135deg, #06b6d4, #3b82f6);
    animation: bounce 1.4s infinite ease-in-out;
  }

  .glassmorphism-card {
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
  }

  /* Custom Scrollbar */
  ::-webkit-scrollbar {
    width: 8px;
  }

  ::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
  }

  ::-webkit-scrollbar-thumb {
    background: rgba(6, 182, 212, 0.5);
    border-radius: 4px;
  }

  ::-webkit-scrollbar-thumb:hover {
    background: rgba(6, 182, 212, 0.7);
  }
`}</style>
    </>
  );
}