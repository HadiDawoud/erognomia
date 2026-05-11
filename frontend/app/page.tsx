"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  ExternalLink,
  Loader2,
  MessageSquare,
  Plus,
  Send,
  ShieldCheck,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: { url: string; title: string }[];
}

function getApiBase(): string {
  if (typeof process.env.NEXT_PUBLIC_API_BASE === "string" && process.env.NEXT_PUBLIC_API_BASE) {
    return process.env.NEXT_PUBLIC_API_BASE.replace(/\/$/, "");
  }
  return "http://127.0.0.1:8001";
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hallo! Ich bin Ergonomia, dein KI-Assistent für das Immersive Reality Lab. Wie kann ich dir heute helfen?",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [health, setHealth] = useState<"ok" | "error" | "loading">("loading");
  const scrollRef = useRef<HTMLDivElement>(null);
  const API_BASE = getApiBase();

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch(`${API_BASE}/health`);
        if (res.ok) setHealth("ok");
        else setHealth("error");
      } catch {
        setHealth("error");
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, [API_BASE]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await fetch(
        `${API_BASE}/api/chat/stream?message=${encodeURIComponent(userMessage)}`,
      );
      if (!response.ok) throw new Error("Failed to connect to API");

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No reader available");

      const currentAssistantMessage: Message = {
        role: "assistant",
        content: "",
        sources: [],
      };
      setMessages((prev) => [...prev, { ...currentAssistantMessage }]);

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() ?? "";

        for (const raw of parts) {
          let eventType: string | null = null;
          let dataPayload: unknown = undefined;
          for (const rawLine of raw.split("\n")) {
            const line = rawLine.trim();
            if (!line) continue;
            if (line.startsWith("event:")) {
              eventType = line.slice(6).trim();
            }
            if (line.startsWith("data:")) {
              const jsonSlice = line.slice(5).trim();
              try {
                dataPayload = JSON.parse(jsonSlice);
              } catch {
                continue;
              }
            }
          }
          if (!eventType) continue;

          setMessages((prev) => {
            const next = [...prev];
            const idx = next.length - 1;
            const last = next[idx];
            if (!last || last.role !== "assistant") return prev;

            if (eventType === "answer" && typeof dataPayload === "string") {
              next[idx] = { ...last, content: last.content + dataPayload };
            } else if (eventType === "sources" && Array.isArray(dataPayload)) {
              next[idx] = { ...last, sources: dataPayload as Message["sources"] };
            }
            return next;
          });
        }
      }
    } catch (error) {
      console.error("Error streaming:", error);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Entschuldigung, es gab einen Fehler bei der Verbindung zum Server.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50 text-gray-900">
      <div className="flex w-64 flex-col bg-gray-900 text-white">
        <div className="flex items-center gap-2 border-b border-gray-800 p-4">
          <ShieldCheck className="text-blue-400" />
          <span className="text-lg font-bold">Ergonomia</span>
        </div>
        <button
          type="button"
          className="m-4 flex items-center justify-center gap-2 rounded bg-blue-600 p-2 transition hover:bg-blue-700"
        >
          <Plus size={18} /> New Chat
        </button>
        <div className="flex-1 space-y-1 overflow-y-auto p-2">
          <div className="flex cursor-pointer items-center gap-2 rounded bg-gray-800 p-2">
            <MessageSquare size={16} />
            <span className="truncate text-sm">Aktuelles Gespräch</span>
          </div>
        </div>
        <div className="flex items-center gap-2 border-t border-gray-800 p-4 text-xs text-gray-400">
          <div
            className={`h-2 w-2 rounded-full ${health === "ok" ? "bg-green-500" : "bg-red-500"}`}
          />
          API: {health === "ok" ? "Online" : "Offline"} · {API_BASE}
        </div>
      </div>

      <div className="relative flex flex-1 flex-col">
        <div ref={scrollRef} className="flex-1 space-y-6 overflow-y-auto p-4 pb-32">
          {messages.map((m, i) => (
            <div
              key={`${i}-${m.role}-${m.content.slice(0, 20)}`}
              className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-2xl rounded-2xl p-4 shadow-sm ${
                  m.role === "user"
                    ? "bg-blue-600 text-white"
                    : "border border-gray-200 bg-white"
                }`}
              >
                <div className="prose prose-sm max-w-none dark:prose-invert">
                  <ReactMarkdown rehypePlugins={[rehypeSanitize]}>{m.content}</ReactMarkdown>
                </div>
                {m.sources && m.sources.length > 0 && (
                  <div className="mt-4 border-t border-gray-100 pt-4">
                    <p className="mb-2 text-xs font-semibold text-gray-500">Quellen:</p>
                    <div className="flex flex-wrap gap-2">
                      {m.sources.map((s, si) => (
                        <a
                          key={`${si}-${s.url}`}
                          href={s.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 rounded bg-gray-100 px-2 py-1 text-xs text-blue-600 transition hover:bg-gray-200"
                        >
                          <ExternalLink size={10} /> {s.title}
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="flex items-center gap-2 rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
                <Loader2 className="animate-spin text-blue-600" size={18} />
                <span className="text-sm text-gray-500">Ergonomia denkt nach...</span>
              </div>
            </div>
          )}
        </div>

        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-gray-50 via-gray-50 to-transparent p-4">
          <form onSubmit={handleSubmit} className="relative mx-auto max-w-3xl">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Frag mich etwas zum IRL..."
              className="w-full rounded-xl border border-gray-300 p-4 pr-12 shadow-lg outline-none transition focus:border-transparent focus:ring-2 focus:ring-blue-500"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="absolute right-3 top-1/2 -translate-y-1/2 p-2 text-blue-600 transition hover:text-blue-800 disabled:text-gray-400"
            >
              <Send size={24} />
            </button>
          </form>
          <p className="mt-2 text-center text-[10px] text-gray-400">
            Ergonomia kann Fehler machen. Überprüfe wichtige Informationen auf der Website.
          </p>
        </div>
      </div>
    </div>
  );
}
