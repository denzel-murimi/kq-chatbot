"use client";

import { useState } from "react";
import { MessageCircle } from "lucide-react";
import { Logo } from "@/components/Logo";
import { ThemeToggle } from "@/components/ThemeToggle";
import { ChatPanel } from "@/components/ChatPanel";
import { BottomNav, NAV_ITEMS, Sidebar, type TabId } from "@/components/Navigation";
import { CheckInView } from "@/components/views/CheckInView";
import { DashboardView } from "@/components/views/DashboardView";
import { FlightStatusView } from "@/components/views/FlightStatusView";
import { useChat } from "@/hooks/useChat";
import { DEMO_PASSENGER } from "@/lib/demo-data";

// "use client" sits here, at the top of the tree. Everything imported below is client code too,
// so the components and hooks do not each need their own directive.
export default function Home() {
  const [activeTab, setActiveTab] = useState<TabId>("dashboard");
  const [isChatOpen, setIsChatOpen] = useState(false);
  const { messages, isLoading, send } = useChat();

  const current = NAV_ITEMS.find((item) => item.id === activeTab) ?? NAV_ITEMS[0];
  const initials = `${DEMO_PASSENGER.firstName[0]}${DEMO_PASSENGER.lastName[0]}`;

  // Quick actions and forms hand a question to the assistant. Below xl the chat is a slide-over, so open it too.
  function ask(question: string) {
    setIsChatOpen(true);
    void send(question);
  }

  return (
    <div className="flex h-dvh w-full overflow-hidden bg-canvas text-ink">
      <Sidebar active={activeTab} onChange={setActiveTab} />

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 shrink-0 items-center justify-between gap-3 border-b border-line bg-surface px-4 xl:h-20 xl:px-10">
          <div className="flex min-w-0 items-center gap-3">
            <div className="shrink-0 xl:hidden">
              <Logo className="h-7 w-auto sm:h-8 dark:brightness-0 dark:invert" priority />
            </div>
            <div className="hidden min-w-0 sm:block xl:block">
              <h1 className="truncate text-lg font-bold tracking-tight xl:text-2xl">{current.title}</h1>
              <p className="hidden truncate text-sm text-ink-3 xl:block">{current.subtitle}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <div className="hidden text-right sm:block">
              <p className="text-sm font-bold">
                {DEMO_PASSENGER.firstName} {DEMO_PASSENGER.lastName}
              </p>
              <p className="text-xs font-semibold text-ink-3">Demo passenger</p>
            </div>
            <div
              aria-label={`${DEMO_PASSENGER.firstName} ${DEMO_PASSENGER.lastName}, demo passenger`}
              role="img"
              className="flex h-10 w-10 items-center justify-center rounded-full bg-night text-sm font-bold text-on-night ring-2 ring-surface"
            >
              {initials}
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto px-4 pb-32 pt-6 xl:px-10 xl:pb-10 xl:pt-8">
          {/* On phones the header has no room for the title, so it sits at the top of the content. */}
          <div className="mx-auto mb-5 w-full max-w-4xl sm:hidden">
            <h1 className="text-2xl font-bold tracking-tight">{current.title}</h1>
            <p className="mt-1 text-sm text-ink-3">{current.subtitle}</p>
          </div>
          <div key={activeTab} className="mx-auto w-full max-w-4xl">
            {activeTab === "dashboard" && <DashboardView onAsk={ask} />}
            {activeTab === "checkin" && <CheckInView onAsk={ask} />}
            {activeTab === "status" && <FlightStatusView onAsk={ask} />}
          </div>
        </main>
      </div>

      <ChatPanel
        messages={messages}
        isLoading={isLoading}
        isOpen={isChatOpen}
        onSend={(text) => void send(text)}
        onClose={() => setIsChatOpen(false)}
      />

      <BottomNav active={activeTab} onChange={setActiveTab} />

      {!isChatOpen && (
        <button
          type="button"
          onClick={() => setIsChatOpen(true)}
          className="fixed bottom-[calc(5rem+env(safe-area-inset-bottom))] right-4 z-30 flex h-14 items-center gap-2 rounded-full bg-brand pl-4 pr-5 font-bold text-on-brand shadow-lg shadow-brand/25 transition hover:bg-brand-hover active:scale-[0.97] xl:hidden"
        >
          <MessageCircle size={22} aria-hidden="true" />
          Ask assistant
        </button>
      )}
    </div>
  );
}
