import { useEffect, useRef, useState } from "react";
import { Send, Sparkles, X } from "lucide-react";
import type { Message } from "@/hooks/useChat";
import { BrandMark } from "./BrandMark";

type Props = {
  messages: Message[];
  isLoading: boolean;
  /** Below the xl breakpoint the panel is a slide-over. From xl up it is always visible. */
  isOpen: boolean;
  onSend: (text: string) => void;
  onClose: () => void;
};

// Renders **bold** segments from the assistant's reply as <strong>. Everything else stays plain
// text, so a reply can never inject HTML into the page.
function FormattedText({ text }: { text: string }) {
  return (
    <>
      {text.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
        part.startsWith("**") && part.endsWith("**") ? (
          <strong key={i} className="font-bold text-gray-900">
            {part.slice(2, -2)}
          </strong>
        ) : (
          <span key={i}>{part}</span>
        ),
      )}
    </>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex flex-col motion-safe:animate-fade-up ${isUser ? "items-end" : "items-start"}`}>
      {!isUser && (
        <div className="mb-1.5 ml-1 flex items-center gap-2">
          <BrandMark size="sm" />
          <span className="text-xs font-bold text-gray-700">AI Assistant</span>
          {message.time && <span className="text-[11px] text-gray-500">{message.time}</span>}
        </div>
      )}
      <div
        className={`max-w-[85%] px-4 py-3 text-sm shadow-xs ${
          isUser
            ? "rounded-2xl rounded-tr-sm bg-ink text-white"
            : "rounded-2xl rounded-tl-sm border border-gray-200 bg-white text-gray-800"
        }`}
      >
        <p className="whitespace-pre-wrap leading-relaxed">
          {isUser ? message.text : <FormattedText text={message.text} />}
        </p>
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div role="status" className="flex flex-col items-start">
      <span className="sr-only">AI Assistant is typing</span>
      <div className="flex items-center gap-1.5 rounded-2xl rounded-tl-sm border border-gray-200 bg-white px-5 py-4 shadow-xs">
        {[0, 150, 300].map((delay) => (
          <span
            key={delay}
            className="h-2 w-2 animate-bounce rounded-full bg-gray-300"
            style={{ animationDelay: `${delay}ms` }}
          />
        ))}
      </div>
    </div>
  );
}

export function ChatPanel({ messages, isLoading, isOpen, onSend, onClose }: Props) {
  const [input, setInput] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, isLoading]);

  const canSend = input.trim() !== "" && !isLoading;

  function submit() {
    if (!canSend) return;
    onSend(input);
    setInput("");
  }

  return (
    <aside
      aria-label="AI Assistant"
      onKeyDown={(e) => {
        if (e.key === "Escape") onClose();
      }}
      className={`fixed inset-0 z-40 flex flex-col bg-white transition-[transform,visibility] duration-300 ${
        isOpen ? "visible translate-x-0" : "invisible translate-x-full"
      } xl:visible xl:static xl:z-auto xl:w-[400px] xl:shrink-0 xl:translate-x-0 xl:border-l xl:border-gray-200`}
    >
      <header className="flex h-16 shrink-0 items-center justify-between border-b border-gray-100 px-4 xl:h-20 xl:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-brand/10 text-brand">
            <Sparkles size={18} aria-hidden="true" />
          </div>
          <div>
            <h2 className="text-sm font-bold">AI Assistant</h2>
            <p className="text-xs text-gray-500">Baggage, check-in and your booking</p>
          </div>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close chat"
          className="rounded-lg p-2 text-gray-500 hover:bg-gray-100 xl:hidden"
        >
          <X size={20} aria-hidden="true" />
        </button>
      </header>

      <div
        role="log"
        aria-label="Conversation"
        className="flex-1 space-y-5 overflow-y-auto overscroll-contain bg-gray-50/60 p-4 xl:p-6"
      >
        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} />
        ))}
        {isLoading && <TypingIndicator />}
        <div ref={endRef} />
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
        className="shrink-0 border-t border-gray-100 bg-white p-4"
      >
        <div className="flex items-end gap-2 rounded-2xl border border-gray-300 bg-white p-2 transition focus-within:border-brand focus-within:ring-2 focus-within:ring-brand/20">
          <textarea
            aria-label="Message"
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submit();
              }
            }}
            placeholder="Type your message..."
            className="field-sizing-content max-h-32 min-h-11 flex-1 resize-none bg-transparent py-2.5 pl-3 text-sm font-medium outline-none placeholder:text-gray-500"
          />
          <button
            type="submit"
            disabled={!canSend}
            aria-label="Send message"
            className={`shrink-0 rounded-xl p-3 transition ${
              canSend ? "bg-brand text-white hover:bg-brand/90" : "cursor-not-allowed bg-gray-100 text-gray-400"
            }`}
          >
            <Send size={18} aria-hidden="true" />
          </button>
        </div>
        <p className="mt-2 text-center text-[11px] text-gray-500">
          Academic prototype, not an official Kenya Airways service. Booking data is simulated.
        </p>
      </form>
    </aside>
  );
}
