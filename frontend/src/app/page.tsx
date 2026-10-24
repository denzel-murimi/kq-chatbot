"use client";

import { useState } from "react";
import { MessageCircle, User } from "lucide-react";
import { BrandMark } from "@/components/BrandMark";
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

  // Quick actions and forms hand a question to the assistant. Below xl the chat is a slide-over, so open it too.
  function ask(question: string) {
    setIsChatOpen(true);
    void send(question);
  }

  return (
    <div className="flex h-dvh w-full overflow-hidden bg-gray-50 font-sans text-gray-900">
      <Sidebar active={activeTab} onChange={setActiveTab} />

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 shrink-0 items-center justify-between gap-3 border-b border-gray-200 bg-white px-4 xl:h-20 xl:px-8">
          <div className="flex items-center gap-3">
            <div className="xl:hidden">
              <BrandMark />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight xl:text-2xl">{current.title}</h1>
              <p className="hidden text-sm text-gray-500 sm:block">{current.subtitle}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="text-sm font-bold">
                {DEMO_PASSENGER.firstName} {DEMO_PASSENGER.lastName}
              </p>
              <p className="text-[11px] font-semibold uppercase tracking-wider text-brand">Demo passenger</p>
            </div>
            <div className="flex h-10 w-10 items-center justify-center rounded-full border border-gray-200 bg-gray-100 text-gray-500">
              <User size={20} aria-hidden="true" />
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-4 pb-28 xl:p-8 xl:pb-8">
          <div className="mx-auto w-full max-w-4xl">
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
          aria-label="Open AI Assistant"
          className="fixed bottom-20 right-4 z-30 flex h-14 w-14 items-center justify-center rounded-full bg-brand text-white shadow-lg transition hover:bg-brand/90 xl:hidden"
        >
          <MessageCircle size={24} aria-hidden="true" />
        </button>
      )}
    </div>
  );
}
