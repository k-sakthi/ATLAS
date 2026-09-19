"use client";

import { useState, useRef, useEffect } from "react";
import { MessageSquare, X, Send, Bot, Sparkles } from "lucide-react";
import { api } from "@/lib/api";

export default function AIChatPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<{ role: "user" | "bot"; content: string }[]>([
    { role: "bot", content: "ATLAS Intelligence initialized. Evidence-grounded clinical data assistant ready." }
  ]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading, isOpen]);

  const handleSend = async () => {
    if (!query.trim()) return;

    const userMessage = query.trim();
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setQuery("");
    setLoading(true);

    try {
      const res = await api.post("/chat", { question: userMessage });
      setMessages((prev) => [...prev, { role: "bot", content: res.data.answer }]);
    } catch (error) {
      setMessages((prev) => [...prev, { role: "bot", content: "Error: The deterministic analysis service could not be reached." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Toggle Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 bg-blue-600 hover:bg-blue-500 text-white p-4 rounded-full shadow-[0_0_20px_rgba(37,99,235,0.4)] transition-all hover:scale-105 z-40 flex items-center justify-center group"
          aria-label="Open AI Chat"
        >
          <Sparkles size={22} className="absolute -top-1 -right-1 text-blue-300 opacity-0 group-hover:opacity-100 transition-opacity" />
          <MessageSquare size={24} />
        </button>
      )}

      {/* Chat Panel */}
      {isOpen && (
        <div className="fixed top-0 right-0 w-[400px] max-w-[100vw] h-screen bg-[#111113] border-l border-zinc-800 shadow-2xl flex flex-col z-50 slide-in-right">
          {/* Header */}
          <div className="p-4 border-b border-zinc-800/80 flex items-center justify-between bg-[#09090b]">
            <div className="flex items-center gap-3">
              <div className="bg-blue-900/30 p-2 rounded-lg border border-blue-800/50">
                <Bot className="text-blue-400" size={20} />
              </div>
              <div>
                <h3 className="font-bold text-zinc-100 tracking-tight text-sm">ATLAS Intelligence</h3>
                <p className="text-[11px] text-zinc-500 font-medium">Evidence-grounded assistant</p>
              </div>
            </div>
            <button 
              onClick={() => setIsOpen(false)} 
              className="text-zinc-500 hover:text-zinc-300 bg-zinc-900 hover:bg-zinc-800 p-2 rounded-md transition-colors"
            >
              <X size={18} />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-5 bg-[#0a0a0c]">
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                {msg.role === "bot" && (
                  <div className="w-6 h-6 rounded bg-blue-900/40 border border-blue-800/50 flex items-center justify-center mr-2 mt-1 shrink-0">
                    <Bot size={14} className="text-blue-400" />
                  </div>
                )}
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 text-[13px] leading-relaxed shadow-sm ${
                    msg.role === "user"
                      ? "bg-blue-600 text-white rounded-br-sm shadow-blue-900/20"
                      : "bg-[#18181b] text-zinc-300 border border-zinc-800 rounded-bl-sm"
                  }`}
                  style={{ whiteSpace: "pre-wrap" }}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="w-6 h-6 rounded bg-blue-900/40 border border-blue-800/50 flex items-center justify-center mr-2 shrink-0">
                  <Bot size={14} className="text-blue-400" />
                </div>
                <div className="bg-[#18181b] border border-zinc-800 px-4 py-3 rounded-2xl rounded-bl-sm flex items-center gap-2">
                  <div className="flex gap-1">
                    <div className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                    <div className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                    <div className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="p-4 border-t border-zinc-800 bg-[#09090b]">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="flex items-center gap-2 relative"
            >
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask about deterministic findings..."
                className="flex-1 bg-zinc-900/80 border border-zinc-700/60 text-zinc-100 text-sm rounded-xl pl-4 pr-12 py-3 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 outline-none placeholder-zinc-500 transition-colors shadow-inner"
              />
              <button
                type="submit"
                disabled={loading || !query.trim()}
                className="absolute right-2 top-1/2 -translate-y-1/2 bg-blue-600 hover:bg-blue-500 text-white p-2 rounded-lg disabled:opacity-40 disabled:hover:bg-blue-600 transition-colors shadow-sm"
              >
                <Send size={16} />
              </button>
            </form>
            <p className="text-[10px] text-zinc-500 font-medium text-center mt-3">
              Deterministic analysis engine provides the clinical findings. AI explains the returned evidence.
            </p>
          </div>
        </div>
      )}
    </>
  );
}
