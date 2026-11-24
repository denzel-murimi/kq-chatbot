import { useEffect, useRef, useState } from "react";
import { ArrowUp, Sparkles, X } from "lucide-react";
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

// Shown until the passenger sends their first message. Each maps to a document in the corpus.
const STARTERS = [
  "How much checked baggage can I take?",
  "Can I carry a power bank on board?",
  "Do I need a visa to fly to London?",
  "When does check-in close?",
];

// Renders **bold** segments from the assistant's reply as <strong>. Everything else stays plain
// text, so a reply can never inject HTML into the page.
function FormattedText({ text }: { text: string }) {
  return (
    <>
      {text.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
        part.startsWith("**") && part.endsWith("**") ? (
          <strong key={i} className="font-bold text-ink">
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

  if (isUser) {
    return (
      <div className="flex justify-end motion-safe:animate-fade-up">
        <p className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-md bg-night px-4 py-3 text-[15px] leading-relaxed text-on-night">
          {message.text}
        </p>
      </div>
    );
  }

  return (
    <div className="flex gap-3 motion-safe:animate-fade-up">
      <BrandMark size="sm" />
      <div className="min-w-0 max-w-[88%]">
        <p className="mb-1 flex items-baseline gap-2 text-xs">
          <span className="font-bold text-ink-2">Assistant</span>
          {message.time && <span className="text-ink-3">{message.time}</span>}
        </p>
        <div className="rounded-2xl rounded-tl-md border border-line bg-surface px-4 py-3 text-[15px] leading-relaxed text-ink-2">
          <p className="whitespace-pre-wrap">
            <FormattedText text={message.text} />
          </p>
        </div>
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div role="status" className="flex gap-3">
      <BrandMark size="sm" />
      <span className="sr-only">Assistant is typing</span>
      <div className="flex items-center gap-1.5 rounded-2xl rounded-tl-md border border-line bg-surface px-4 py-3.5">
        {[0, 150, 300].map((delay) => (
          <span
            key={delay}
            aria-hidden="true"
            className="h-2 w-2 animate-bounce rounded-full bg-ink-3/60"
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
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, isLoading]);

  // When the slide-over opens on small screens, move focus into it.
  useEffect(() => {
    if (isOpen) inputRef.current?.focus({ preventScroll: true });
  }, [isOpen]);

  const canSend = input.trim() !== "" && !isLoading;
  const showStarters = messages.every((m) => m.role === "bot") && !isLoading;

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
      className={`fixed inset-0 z-40 flex flex-col bg-canvas transition-[transform,visibility] duration-300 ease-out ${
        isOpen ? "visible translate-x-0" : "invisible translate-x-full"
      } xl:visible xl:static xl:z-auto xl:w-[420px] xl:shrink-0 xl:translate-x-0 xl:border-l xl:border-line`}
    >
      <header className="flex h-16 shrink-0 items-center justify-between border-b border-line bg-surface px-4 xl:h-20 xl:px-6">
        <div className="flex items-center gap-3">
          <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-brand-soft text-brand-ink">
            <Sparkles size={18} aria-hidden="true" />
            <span
              aria-hidden="true"
              className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-surface bg-ok"
            />
          </div>
          <div>
            <h2 className="font-bold leading-tight">AI Assistant</h2>
            <p className="text-sm text-ink-3">Baggage, check-in and your booking</p>
          </div>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close chat"
          className="flex h-11 w-11 items-center justify-center rounded-lg text-ink-2 hover:bg-surface-2 xl:hidden"
        >
          <X size={20} aria-hidden="true" />
        </button>
      </header>

      <div
        role="log"
        aria-label="Conversation"
        aria-live="polite"
        className="flex-1 space-y-5 overflow-y-auto overscroll-contain p-4 xl:p-6"
      >
        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} />
        ))}
        {showStarters && (
          <div className="pl-9 motion-safe:animate-fade-up">
            <p className="mb-2 text-xs font-bold uppercase tracking-wider text-ink-3">Try asking</p>
            <ul className="flex flex-col items-start gap-2">
              {STARTERS.map((q) => (
                <li key={q}>
                  <button
                    type="button"
                    onClick={() => onSend(q)}
                    className="min-h-10 rounded-xl border border-line bg-surface px-3.5 py-2 text-left text-sm font-semibold text-ink-2 transition-colors hover:border-brand/40 hover:text-brand-ink"
                  >
                    {q}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
        {isLoading && <TypingIndicator />}
        <div ref={endRef} />
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
        className="shrink-0 border-t border-line bg-surface p-4 pb-[calc(1rem+env(safe-area-inset-bottom))]"
      >
        <div className="flex items-end gap-2 rounded-2xl border border-line-strong bg-surface p-1.5 transition focus-within:border-brand focus-within:ring-4 focus-within:ring-brand/15">
          <textarea
            ref={inputRef}
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
            placeholder="Ask about baggage, check-in…"
            className="field-sizing-content max-h-32 min-h-11 flex-1 resize-none bg-transparent px-3 py-2.5 text-[15px] text-ink outline-none placeholder:text-ink-3 focus-visible:outline-none"
          />
          <button
            type="submit"
            disabled={!canSend}
            aria-label="Send message"
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-brand text-on-brand transition hover:bg-brand-hover active:scale-95 disabled:cursor-not-allowed disabled:bg-surface-2 disabled:text-ink-3"
          >
            <ArrowUp size={20} aria-hidden="true" />
          </button>
        </div>
        <p className="mt-2 text-center text-xs text-ink-3">
          Academic prototype, not an official Kenya Airways service. Booking data is simulated.
        </p>
      </form>
    </aside>
  );
}
