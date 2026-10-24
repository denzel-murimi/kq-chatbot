import { useRef, useState } from "react";
import { sendChatMessage } from "@/lib/chat-api";

export type Message = {
  id: number;
  role: "user" | "bot";
  text: string;
  /** Set when a message is created in the browser. The greeting has none, which avoids a server/client time mismatch. */
  time?: string;
};

const GREETING: Message = {
  id: 0,
  role: "bot",
  text: "Hello! 👋 How can I help with your trip today?",
};

const timeNow = () => new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

// All chat state lives here, so components only render and never call fetch themselves.
export function useChat() {
  const [messages, setMessages] = useState<Message[]>([GREETING]);
  const [isLoading, setIsLoading] = useState(false);
  const nextId = useRef(1);
  const sessionId = useRef("");
  const inFlight = useRef(false); // a ref, not state: it must block a double-click within the same render

  function add(role: Message["role"], text: string) {
    const message: Message = { id: nextId.current++, role, text, time: timeNow() };
    setMessages((prev) => [...prev, message]);
  }

  async function send(text: string) {
    const question = text.trim();
    if (!question || inFlight.current) return;

    inFlight.current = true;
    setIsLoading(true);
    add("user", question);

    try {
      // One id per page load: a new page load starts a new, empty conversation.
      sessionId.current ||= crypto.randomUUID();
      const { reply } = await sendChatMessage(question, sessionId.current);
      add("bot", reply || "Sorry, I did not get an answer back. Please try again.");
    } catch (error) {
      // The technical detail goes to the console; the passenger gets a plain sentence.
      console.error("Chat request failed:", error);
      add("bot", "Sorry, I could not reach the assistant just now. Please try again in a moment.");
    } finally {
      inFlight.current = false;
      setIsLoading(false);
    }
  }

  return { messages, isLoading, send };
}
