"use client";

import { useState } from "react";

type Message = { role: "user" | "bot"; text: string };

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");

  async function sendMessage() {
    if (!input.trim()) return;
    const userMessage: Message = { role: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    const res = await fetch("http://localhost:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: userMessage.text }),
    });
    const data = await res.json();
    setMessages((prev) => [...prev, { role: "bot", text: data.reply }]);
  }

  return (
    <main className="mx-auto flex h-screen max-w-md flex-col p-4">
      <div className="flex-1 space-y-2 overflow-y-auto">
        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
            <span className="inline-block rounded-lg bg-gray-100 px-3 py-2">
              {m.text}
            </span>
          </div>
        ))}
      </div>
      <div className="flex gap-2 pt-2">
        <input
          className="flex-1 rounded border px-3 py-2"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Ask about your flight..."
        />
        <button className="rounded bg-blue-600 px-4 py-2 text-white" onClick={sendMessage}>
          Send
        </button>
      </div>
    </main>
  );
}