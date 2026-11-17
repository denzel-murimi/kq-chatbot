"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { FileText, Plus, RefreshCw, Save, Search, Trash2 } from "lucide-react";
import { adminApi, AdminAuthError, type AdminDoc } from "@/lib/admin-api";
import { Button, Notice, Panel, Skeleton } from "./ui";

type Props = { adminKey: string; onAuthError: () => void };
type Note = { tone: "ok" | "error"; text: string } | null;

export function KnowledgeBaseTab({ adminKey, onAuthError }: Props) {
  const [docs, setDocs] = useState<AdminDoc[] | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [savedContent, setSavedContent] = useState("");
  const [isNew, setIsNew] = useState(false);
  const [busy, setBusy] = useState<"save" | "delete" | "reindex" | null>(null);
  const [note, setNote] = useState<Note>(null);
  const [filter, setFilter] = useState("");

  const guard = useCallback(
    async (fn: () => Promise<void>) => {
      setNote(null);
      try {
        await fn();
      } catch (e) {
        if (e instanceof AdminAuthError) onAuthError();
        else setNote({ tone: "error", text: e instanceof Error ? e.message : "Something went wrong." });
      }
    },
    [onAuthError],
  );

  const loadDocs = useCallback(
    () =>
      guard(async () => {
        setDocs(await adminApi.listDocuments(adminKey));
      }),
    [adminKey, guard],
  );

  useEffect(() => {
    void loadDocs();
  }, [loadDocs]);

  const isDirty = content !== savedContent;
  const totalChunks = docs?.reduce((a, d) => a + d.chunks, 0) ?? 0;
  const visibleDocs = useMemo(() => {
    const q = filter.trim().toLowerCase();
    return (docs ?? []).filter((d) => !q || d.title.toLowerCase().includes(q));
  }, [docs, filter]);

  function confirmDiscard() {
    return !isDirty || window.confirm("You have unsaved changes. Discard them?");
  }

  function openDoc(docTitle: string) {
    if (docTitle === selected || !confirmDiscard()) return;
    void guard(async () => {
      const doc = await adminApi.getDocument(adminKey, docTitle);
      setSelected(doc.title);
      setTitle(doc.title);
      setContent(doc.content);
      setSavedContent(doc.content);
      setIsNew(false);
    });
  }

  function startNew() {
    if (!confirmDiscard()) return;
    setSelected(null);
    setTitle("");
    setContent("");
    setSavedContent("");
    setIsNew(true);
    setNote(null);
  }

  function save() {
    if (!title.trim() || !content.trim()) {
      setNote({ tone: "error", text: "Both a title and content are required." });
      return;
    }
    void guard(async () => {
      setBusy("save");
      try {
        const res = await adminApi.saveDocument(adminKey, title.trim(), content);
        setNote({ tone: "ok", text: `Saved “${res.title}” and re-indexed it into ${res.chunks} chunk(s).` });
        setIsNew(false);
        setSelected(title.trim());
        setSavedContent(content);
        await loadDocs();
      } finally {
        setBusy(null);
      }
    });
  }

  function remove() {
    if (!selected) return;
    if (!window.confirm(`Delete “${selected}” and its chunks? This cannot be undone.`)) return;
    void guard(async () => {
      setBusy("delete");
      try {
        await adminApi.deleteDocument(adminKey, selected);
        setNote({ tone: "ok", text: `Deleted “${selected}”.` });
        setSelected(null);
        setTitle("");
        setContent("");
        setSavedContent("");
        await loadDocs();
      } finally {
        setBusy(null);
      }
    });
  }

  function reindex() {
    void guard(async () => {
      setBusy("reindex");
      try {
        const res = await adminApi.reindex(adminKey);
        setNote({ tone: "ok", text: `Re-indexed ${res.documents} document(s) into ${res.chunks} chunk(s).` });
        await loadDocs();
      } finally {
        setBusy(null);
      }
    });
  }

  const editing = selected !== null || isNew;

  return (
    <div className="grid gap-5 lg:grid-cols-[300px_minmax(0,1fr)]">
      {/* Document list */}
      <Panel
        className="flex flex-col lg:sticky lg:top-6 lg:max-h-[calc(100dvh-10rem)]"
        title={docs ? `${docs.length} docs · ${totalChunks} chunks` : "Documents"}
        actions={
          <Button variant="ghost" className="h-8 shrink-0 whitespace-nowrap px-2" onClick={reindex} loading={busy === "reindex"} disabled={busy !== null} title="Rebuild every document's chunks and embeddings">
            {busy !== "reindex" && <RefreshCw size={14} aria-hidden="true" />}
            Re-index
          </Button>
        }
      >
        <div className="border-b border-line p-2">
          <div className="relative">
            <Search size={14} className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-3" aria-hidden="true" />
            <input
              type="search"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              placeholder="Filter documents"
              aria-label="Filter documents"
              className="h-8 w-full rounded-md bg-surface-2 pl-8 pr-2 text-sm text-ink outline-none placeholder:text-ink-3 focus:ring-2 focus:ring-brand/30 focus-visible:outline-none"
            />
          </div>
        </div>
        <ul className="min-h-0 flex-1 space-y-0.5 overflow-y-auto p-2">
          {docs === null &&
            [0, 1, 2, 3, 4].map((i) => (
              <li key={i} className="px-2.5 py-2">
                <Skeleton className="h-3.5 w-3/4" />
                <Skeleton className="mt-1.5 h-2.5 w-1/4" />
              </li>
            ))}
          {visibleDocs.map((d) => {
            const isActive = selected === d.title;
            return (
              <li key={d.title}>
                <button
                  type="button"
                  onClick={() => openDoc(d.title)}
                  aria-current={isActive ? "true" : undefined}
                  className={`flex w-full items-start gap-2.5 rounded-lg px-2.5 py-2 text-left transition-colors ${
                    isActive ? "bg-brand-soft" : "hover:bg-surface-2"
                  }`}
                >
                  <FileText size={15} className={`mt-0.5 shrink-0 ${isActive ? "text-brand-ink" : "text-ink-3"}`} aria-hidden="true" />
                  <span className="min-w-0">
                    <span className={`block truncate text-sm font-medium ${isActive ? "text-brand-ink" : "text-ink"}`}>{d.title}</span>
                    <span className="font-admin-mono text-[11px] text-ink-3">{d.chunks} chunks</span>
                  </span>
                </button>
              </li>
            );
          })}
          {docs !== null && visibleDocs.length === 0 && (
            <li className="px-3 py-6 text-center text-sm text-ink-3">{filter ? "No matching documents." : "No documents yet."}</li>
          )}
        </ul>
        <div className="border-t border-line p-2">
          <Button variant="ghost" onClick={startNew} className="w-full">
            <Plus size={15} aria-hidden="true" /> New document
          </Button>
        </div>
      </Panel>

      {/* Editor */}
      <div className="flex min-w-0 flex-col gap-3">
        {note && <Notice tone={note.tone}>{note.text}</Notice>}

        {!editing ? (
          <div className="flex min-h-80 flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-line-strong p-8 text-center">
            <FileText size={28} className="text-ink-3" aria-hidden="true" />
            <p className="text-sm text-ink-3">Select a document to edit, or create a new one.</p>
            <Button onClick={startNew}>
              <Plus size={15} aria-hidden="true" /> New document
            </Button>
          </div>
        ) : (
          <Panel>
            <div className="flex flex-wrap items-center gap-3 border-b border-line px-4 py-3">
              {isNew ? (
                <>
                  <label htmlFor="doc-title" className="sr-only">
                    Document title
                  </label>
                  <input
                    id="doc-title"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="Document title"
                    autoFocus
                    className="h-9 min-w-0 flex-1 rounded-lg border border-line-strong bg-surface px-3 text-sm font-semibold text-ink outline-none focus:border-brand focus:ring-4 focus:ring-brand/15 focus-visible:outline-none"
                  />
                </>
              ) : (
                <h2 className="min-w-0 flex-1 truncate font-semibold">{title}</h2>
              )}
              {isDirty && (
                <span className="inline-flex items-center gap-1.5 text-xs font-medium text-warn">
                  <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full bg-warn" /> Unsaved changes
                </span>
              )}
            </div>
            <label htmlFor="doc-content" className="sr-only">
              Document content
            </label>
            <textarea
              id="doc-content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={22}
              placeholder="Document text (markdown)…"
              spellCheck
              className="block w-full resize-y border-0 bg-surface px-4 py-3 font-admin-mono text-[13px] leading-relaxed text-ink outline-none placeholder:text-ink-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-brand/30"
            />
            <div className="flex flex-wrap items-center gap-2 border-t border-line bg-surface-2/50 px-4 py-3">
              <Button variant="primary" onClick={save} loading={busy === "save"} disabled={busy !== null || (!isNew && !isDirty)}>
                {busy !== "save" && <Save size={15} aria-hidden="true" />} Save &amp; re-index
              </Button>
              {!isNew && selected && (
                <Button variant="danger" onClick={remove} loading={busy === "delete"} disabled={busy !== null}>
                  {busy !== "delete" && <Trash2 size={15} aria-hidden="true" />} Delete
                </Button>
              )}
              <span className="ml-auto font-admin-mono text-xs tabular-nums text-ink-3">
                {content.length.toLocaleString()} chars · {content.trim() ? content.trim().split(/\s+/).length.toLocaleString() : 0} words
              </span>
            </div>
          </Panel>
        )}
      </div>
    </div>
  );
}
