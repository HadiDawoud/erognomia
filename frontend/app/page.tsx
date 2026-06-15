"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  ArrowUp,
  Check,
  Compass,
  ExternalLink,
  Image as ImageIcon,
  LayoutGrid,
  Loader2,
  Mic,
  PanelLeft,
  Pencil,
  Plus,
  Search,
  SquarePen,
  Trash2,
  X,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: { url: string; title: string }[];
}

interface Session {
  id: string;
  title?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  last_summarized_at?: string | null;
  user_edited?: boolean;
}

const GREETING: Message = {
  role: "assistant",
  content:
    "Hallo! Ich bin Ergonomia, dein KI-Assistent für das Immersive Reality Lab. Wie kann ich dir heute helfen?",
};

function getApiBase(): string {
  if (typeof process.env.NEXT_PUBLIC_API_BASE === "string" && process.env.NEXT_PUBLIC_API_BASE) {
    return process.env.NEXT_PUBLIC_API_BASE.replace(/\/$/, "");
  }
  return "http://127.0.0.1:8001";
}

/**
 * Minimal typings for the browser-native Web Speech API. On macOS Safari this is
 * backed by the on-device Apple speech engine, so no external STT service is needed.
 */
interface SpeechRecognitionAlternativeLike {
  transcript: string;
}
interface SpeechRecognitionResultLike {
  0: SpeechRecognitionAlternativeLike;
  isFinal: boolean;
}
interface SpeechRecognitionResultListLike {
  length: number;
  [index: number]: SpeechRecognitionResultLike;
}
interface SpeechRecognitionEventLike {
  resultIndex: number;
  results: SpeechRecognitionResultListLike;
}
interface SpeechRecognitionLike {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: ((event: { error?: string }) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
}
type SpeechRecognitionCtor = new () => SpeechRecognitionLike;

function getSpeechRecognitionCtor(): SpeechRecognitionCtor | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as {
    SpeechRecognition?: SpeechRecognitionCtor;
    webkitSpeechRecognition?: SpeechRecognitionCtor;
  };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([GREETING]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [health, setHealth] = useState<"ok" | "error" | "loading">("loading");
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [search, setSearch] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const speechBaseRef = useRef("");
  const API_BASE = getApiBase();

  const hasConversation = messages.some((m) => m.role === "user") || isLoading;

  const loadSessions = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/chat/sessions`);
      if (res.ok) setSessions(await res.json());
    } catch {
      // ignore – sidebar simply stays as-is on transient errors
    }
  }, [API_BASE]);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch(`${API_BASE}/health`);
        setHealth(res.ok ? "ok" : "error");
      } catch {
        setHealth("error");
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, [API_BASE]);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, [input]);

  useEffect(() => {
    setSpeechSupported(getSpeechRecognitionCtor() !== null);
    return () => {
      recognitionRef.current?.stop();
    };
  }, []);

  const stopListening = useCallback(() => {
    recognitionRef.current?.stop();
  }, []);

  const toggleListening = () => {
    if (isLoading) return;
    if (isListening) {
      stopListening();
      return;
    }
    const Ctor = getSpeechRecognitionCtor();
    if (!Ctor) return;

    const recognition = new Ctor();
    recognition.lang = "de-DE";
    recognition.interimResults = true;
    recognition.continuous = true;
    // Keep whatever the user already typed and append the dictation to it.
    speechBaseRef.current = input ? `${input.trim()} ` : "";

    recognition.onresult = (event: SpeechRecognitionEventLike) => {
      let transcript = "";
      for (let i = 0; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }
      setInput((speechBaseRef.current + transcript).replace(/\s+/g, " ").trimStart());
    };
    recognition.onerror = () => {
      setIsListening(false);
    };
    recognition.onend = () => {
      setIsListening(false);
      recognitionRef.current = null;
      textareaRef.current?.focus();
    };

    recognitionRef.current = recognition;
    recognition.start();
    setIsListening(true);
  };

  const handleNewChat = () => {
    if (isLoading) return;
    setEditingId(null);
    setCurrentSessionId(null);
    setMessages([GREETING]);
  };

  const handleSelectSession = async (id: string) => {
    if (isLoading || id === currentSessionId) return;
    try {
      const res = await fetch(`${API_BASE}/api/chat/sessions/${id}/messages`);
      if (!res.ok) return;
      const loaded: Message[] = await res.json();
      setCurrentSessionId(id);
      setMessages(loaded.length > 0 ? loaded : [GREETING]);
    } catch {
      // ignore
    }
  };

  const handleDeleteSession = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const res = await fetch(`${API_BASE}/api/chat/sessions/${id}`, { method: "DELETE" });
      if (res.ok) {
        setSessions((prev) => prev.filter((s) => s.id !== id));
        if (id === currentSessionId) {
          setCurrentSessionId(null);
          setMessages([GREETING]);
        }
      }
    } catch {
      // ignore
    }
  };

  const startEditing = (session: Session, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingId(session.id);
    setEditingTitle(session.title || "");
  };

  const cancelEditing = (e?: React.MouseEvent) => {
    e?.stopPropagation();
    setEditingId(null);
    setEditingTitle("");
  };

  const saveTitle = async (id: string) => {
    const title = editingTitle.trim();
    if (!title) {
      cancelEditing();
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/chat/sessions/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title }),
      });
      if (res.ok) {
        const updated: Session = await res.json();
        setSessions((prev) => prev.map((s) => (s.id === id ? updated : s)));
      }
    } catch {
      // ignore
    } finally {
      setEditingId(null);
      setEditingTitle("");
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    if (isListening) stopListening();
    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setIsLoading(true);

    try {
      const params = new URLSearchParams({ message: userMessage });
      if (currentSessionId) params.set("session_id", currentSessionId);
      const response = await fetch(`${API_BASE}/api/chat/stream?${params.toString()}`);
      if (!response.ok) throw new Error("Failed to connect to API");

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No reader available");

      setMessages((prev) => [...prev, { role: "assistant", content: "", sources: [] }]);

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

          if (eventType === "session" && typeof dataPayload === "string") {
            setCurrentSessionId(dataPayload);
            continue;
          }

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
          content: "Entschuldigung, es gab einen Fehler bei der Verbindung zum Server.",
        },
      ]);
    } finally {
      setIsLoading(false);
      loadSessions();
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const filteredSessions = sessions.filter((s) =>
    (s.title || "New Chat").toLowerCase().includes(search.toLowerCase()),
  );

  const featurePills = [
    { icon: Search, label: "Search Online" },
    { icon: ImageIcon, label: "Create Image" },
    { icon: Compass, label: "Deep Research" },
    { icon: LayoutGrid, label: "Chat Presets" },
  ];

  const composer = (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="flex items-end gap-2 rounded-[28px] border border-white/10 bg-[#1b1722]/90 px-3 py-2 shadow-lg shadow-black/30 backdrop-blur transition focus-within:border-violet-500/50">
        <button
          type="button"
          title="Anhänge (bald verfügbar)"
          className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-white/5 text-gray-300 transition hover:bg-white/10"
        >
          <Plus size={18} />
        </button>
        <textarea
          ref={textareaRef}
          rows={1}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Frag mich etwas zum IRL..."
          disabled={isLoading}
          className="max-h-[200px] flex-1 resize-none bg-transparent py-2 text-[15px] text-gray-100 placeholder-gray-500 outline-none"
        />
        <div className="flex shrink-0 items-center gap-1.5 pb-0.5">
          <span className="hidden items-center gap-1 rounded-full px-2 py-1 text-xs text-gray-400 sm:flex">
            Standard
          </span>
          <button
            type="button"
            onClick={toggleListening}
            disabled={!speechSupported || isLoading}
            title={
              !speechSupported
                ? "Spracheingabe wird von diesem Browser nicht unterstützt"
                : isListening
                  ? "Aufnahme stoppen"
                  : "Spracheingabe starten"
            }
            aria-label={isListening ? "Aufnahme stoppen" : "Spracheingabe starten"}
            aria-pressed={isListening}
            className={`grid h-9 w-9 place-items-center rounded-full transition disabled:cursor-not-allowed disabled:text-gray-600 disabled:hover:bg-transparent ${
              isListening
                ? "animate-pulse bg-red-500/20 text-red-400"
                : "text-gray-300 hover:bg-white/10"
            }`}
          >
            <Mic size={18} />
          </button>
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="grid h-9 w-9 place-items-center rounded-full bg-violet-600 text-white transition hover:bg-violet-500 disabled:cursor-not-allowed disabled:bg-white/10 disabled:text-gray-500"
          >
            {isLoading ? <Loader2 size={18} className="animate-spin" /> : <ArrowUp size={18} />}
          </button>
        </div>
      </div>
      <div className="mt-3 flex flex-wrap justify-center gap-2">
        {featurePills.map(({ icon: Icon, label }) => (
          <button
            key={label}
            type="button"
            title="Bald verfügbar"
            className="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-gray-300 transition hover:bg-white/10"
          >
            <Icon size={13} /> {label}
          </button>
        ))}
      </div>
    </form>
  );

  return (
    <div
      className="flex h-screen text-gray-100"
      style={{
        background:
          "radial-gradient(1200px 600px at 18% -10%, #2a1b4d 0%, rgba(42,27,77,0) 55%), #0c0910",
      }}
    >
      {/* Sidebar */}
      {sidebarOpen && (
        <aside className="flex w-72 flex-col border-r border-white/5 bg-black/30 backdrop-blur">
          <div className="flex items-center justify-between p-3">
            <button
              type="button"
              onClick={() => setSidebarOpen(false)}
              className="grid h-9 w-9 place-items-center rounded-lg text-gray-300 transition hover:bg-white/10"
              aria-label="Seitenleiste schließen"
            >
              <PanelLeft size={18} />
            </button>
            <button
              type="button"
              onClick={handleNewChat}
              className="grid h-9 w-9 place-items-center rounded-lg text-gray-300 transition hover:bg-white/10"
              aria-label="Neuer Chat"
            >
              <SquarePen size={18} />
            </button>
          </div>

          <div className="px-3">
            <button
              type="button"
              onClick={handleNewChat}
              className="flex w-full items-center justify-center gap-2 rounded-full bg-violet-600 py-2.5 text-sm font-medium text-white transition hover:bg-violet-500"
            >
              <Plus size={16} /> New Chat
            </button>
          </div>

          <div className="px-3 pt-3">
            <p className="px-1 pb-2 text-xs font-semibold uppercase tracking-wider text-gray-500">
              Chat History
            </p>
            <div className="relative">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search chats..."
                className="w-full rounded-lg border border-white/10 bg-white/5 py-2 pl-9 pr-3 text-sm text-gray-200 placeholder-gray-500 outline-none transition focus:border-violet-500/50"
              />
            </div>
          </div>

          <div className="mt-2 flex-1 space-y-0.5 overflow-y-auto px-2 pb-2">
            {filteredSessions.length === 0 && (
              <p className="px-2 py-3 text-center text-xs text-gray-500">
                {search ? "Keine Treffer" : "Noch keine Gespräche"}
              </p>
            )}
            {filteredSessions.map((session) => {
              const isActive = session.id === currentSessionId;
              const isEditing = session.id === editingId;
              return (
                <div
                  key={session.id}
                  onClick={() => handleSelectSession(session.id)}
                  className={`group flex cursor-pointer items-center gap-2 rounded-lg px-2 py-2 transition ${
                    isActive ? "bg-white/10" : "hover:bg-white/5"
                  }`}
                >
                  {isEditing ? (
                    <input
                      autoFocus
                      value={editingTitle}
                      onChange={(e) => setEditingTitle(e.target.value)}
                      onClick={(e) => e.stopPropagation()}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") saveTitle(session.id);
                        if (e.key === "Escape") cancelEditing();
                      }}
                      className="min-w-0 flex-1 rounded bg-black/40 px-1.5 py-0.5 text-sm text-white outline-none ring-1 ring-violet-500/50"
                    />
                  ) : (
                    <span className="min-w-0 flex-1 truncate text-sm text-gray-200">
                      {session.title || "New Chat"}
                    </span>
                  )}
                  {isEditing ? (
                    <div className="flex shrink-0 items-center gap-1">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          saveTitle(session.id);
                        }}
                        className="text-gray-400 hover:text-green-400"
                        aria-label="Titel speichern"
                      >
                        <Check size={14} />
                      </button>
                      <button
                        type="button"
                        onClick={cancelEditing}
                        className="text-gray-400 hover:text-red-400"
                        aria-label="Abbrechen"
                      >
                        <X size={14} />
                      </button>
                    </div>
                  ) : (
                    <div className="flex shrink-0 items-center gap-1 opacity-0 transition group-hover:opacity-100">
                      <button
                        type="button"
                        onClick={(e) => startEditing(session, e)}
                        className="text-gray-400 hover:text-white"
                        aria-label="Umbenennen"
                      >
                        <Pencil size={13} />
                      </button>
                      <button
                        type="button"
                        onClick={(e) => handleDeleteSession(session.id, e)}
                        className="text-gray-400 hover:text-red-400"
                        aria-label="Löschen"
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <div className="flex items-center gap-2 border-t border-white/5 p-4 text-xs text-gray-400">
            <div
              className={`h-2 w-2 rounded-full ${health === "ok" ? "bg-green-500" : "bg-red-500"}`}
            />
            API: {health === "ok" ? "Online" : "Offline"}
          </div>
        </aside>
      )}

      {/* Main */}
      <main className="relative flex flex-1 flex-col">
        <header className="flex items-center justify-between px-4 py-3">
          {!sidebarOpen ? (
            <button
              type="button"
              onClick={() => setSidebarOpen(true)}
              className="grid h-9 w-9 place-items-center rounded-lg text-gray-300 transition hover:bg-white/10"
              aria-label="Seitenleiste öffnen"
            >
              <PanelLeft size={18} />
            </button>
          ) : (
            <div className="h-9 w-9" />
          )}
          <span className="text-sm font-semibold tracking-wide text-gray-200">Ergonomia</span>
          <button
            type="button"
            onClick={handleNewChat}
            className="grid h-9 w-9 place-items-center rounded-lg text-gray-300 transition hover:bg-white/10"
            aria-label="Neuer Chat"
          >
            <SquarePen size={18} />
          </button>
        </header>

        {hasConversation ? (
          <>
            <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 pb-40">
              <div className="mx-auto max-w-3xl space-y-6 pt-4">
                {messages.map((m, i) => (
                  <div
                    key={`${i}-${m.role}-${m.content.slice(0, 20)}`}
                    className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-2xl rounded-2xl px-4 py-3 ${
                        m.role === "user"
                          ? "bg-violet-600 text-white"
                          : "border border-white/10 bg-white/5 text-gray-100"
                      }`}
                    >
                      <div className="prose prose-sm prose-invert max-w-none">
                        <ReactMarkdown rehypePlugins={[rehypeSanitize]}>{m.content}</ReactMarkdown>
                      </div>
                      {m.sources && m.sources.length > 0 && (
                        <div className="mt-4 border-t border-white/10 pt-3">
                          <p className="mb-2 text-xs font-semibold text-gray-400">Quellen:</p>
                          <div className="flex flex-wrap gap-2">
                            {m.sources.map((s, si) => (
                              <a
                                key={`${si}-${s.url}`}
                                href={s.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center gap-1 rounded-full bg-white/10 px-2 py-1 text-xs text-violet-300 transition hover:bg-white/20"
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
                    <div className="flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                      <Loader2 className="animate-spin text-violet-400" size={18} />
                      <span className="text-sm text-gray-400">Ergonomia denkt nach...</span>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-[#0c0910] via-[#0c0910] to-transparent px-4 pb-4 pt-8">
              <div className="mx-auto max-w-3xl">
                {composer}
                <p className="mt-2 text-center text-[11px] text-gray-500">
                  Ergonomia kann Fehler machen. Überprüfe wichtige Informationen auf der Website.
                </p>
              </div>
            </div>
          </>
        ) : (
          <div className="flex flex-1 flex-col items-center justify-center px-4">
            <div className="mb-8 flex items-center gap-5">
              <h1 className="text-5xl font-bold tracking-tight text-white">Ergonomia</h1>
              <div className="h-12 w-px bg-white/15" />
              <p className="max-w-xs text-sm leading-relaxed text-gray-400">
                Dein KI-Assistent für das Immersive Reality Lab. Frag mich alles rund ums IRL.
              </p>
            </div>
            <div className="w-full max-w-3xl">{composer}</div>
            <p className="mt-4 text-center text-[11px] text-gray-500">
              Ergonomia kann Fehler machen. Überprüfe wichtige Informationen auf der Website.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
