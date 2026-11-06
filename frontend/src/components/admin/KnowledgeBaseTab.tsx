"use client";

import { useCallback, useEffect, useState } from "react";
import { FileText, Plus, RefreshCw, Save, Trash2 } from "lucide-react";
import { adminApi, AdminAuthError, type AdminDoc } from "@/lib/admin-api";

type Props = { adminKey: string; onAuthError: () => void };

export function KnowledgeBaseTab({ adminKey, onAuthError }: Props) {
  const [docs, setDocs] = useState<AdminDoc[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [isNew, setIsNew] = useState(false);
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState<string | null>(null);

  const guard = useCallback(
    async (fn: () => Promise<void>) => {
      setNote(null);
      try {
        await fn();
      } catch (e) {
        if (e instanceof AdminAuthError) onAuthError();
        else setNote(e instanceof Error ? e.message : "Something went wrong.");
      }
    },
    [onAuthError],
  );

  const loadDocs = useCallback(() => guard(async () => {
    setDocs(await adminApi.listDocuments(adminKey));
  }), [adminKey, guard]);

  useEffect(() => { void loadDocs(); }, [loadDocs]);

  function openDoc(docTitle: string) {
    void guard(async () => {
      const doc = await adminApi.getDocument(adminKey, docTitle);
      setSelected(doc.title);
      setTitle(doc.title);
      setContent(doc.content);
      setIsNew(false);
    });
  }

  function startNew() {
    setSelected(null);
    setTitle("");
    setContent("");
    setIsNew(true);
    setNote(null);
  }

  function save() {
    if (!title.trim() || !content.trim()) {
      setNote("Both a title and content are required.");
      return;
    }
    void guard(async () => {
      setBusy(true);
      try {
        const res = await adminApi.saveDocument(adminKey, title.trim(), content);
        setNote(`Saved “${res.title}” — re-indexed into ${res.chunks} chunk(s).`);
        setIsNew(false);
        setSelected(title.trim());
        await loadDocs();
      } finally {
        setBusy(false);
      }
    });
  }

  function remove() {
    if (!selected) return;
    if (!window.confirm(`Delete “${selected}” and its chunks? This cannot be undone.`)) return;
    void guard(async () => {
      setBusy(true);
      try {
        await adminApi.deleteDocument(adminKey, selected);
        setSelected(null);
        setTitle("");
        setContent("");
        setNote("Document deleted.");
        await loadDocs();
      } finally {
        setBusy(false);
      }
    });
  }

  function reindex() {
    void guard(async () => {
      setBusy(true);
      try {
        const res = await adminApi.reindex(adminKey);
        setNote(`Re-indexed ${res.documents} document(s) into ${res.chunks} chunk(s).`);
      } finally {
        setBusy(false);
      }
    });
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
      {/* document list */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-gray-700">Policy documents</h3>
          <button
            onClick={reindex}
            disabled={busy}
            className="flex items-center gap-1.5 rounded-lg border border-gray-200 px-2.5 py-1.5 text-xs font-semibold text-gray-600 transition hover:bg-gray-50 disabled:opacity-50"
          >
            <RefreshCw size={14} aria-hidden="true" /> Re-index all
          </button>
        </div>

        <div className="space-y-1.5">
          {docs.map((d) => (
            <button
              key={d.title}
              onClick={() => openDoc(d.title)}
              className={`flex w-full items-start gap-2 rounded-xl border px-3 py-2.5 text-left transition ${
                selected === d.title ? "border-brand bg-brand/5" : "border-gray-200 bg-white hover:bg-gray-50"
              }`}
            >
              <FileText size={16} className="mt-0.5 shrink-0 text-gray-400" aria-hidden="true" />
              <span className="min-w-0">
                <span className="block truncate text-sm font-semibold text-gray-800">{d.title}</span>
                <span className="text-[11px] text-gray-500">{d.chunks} chunk(s)</span>
              </span>
            </button>
          ))}
          {docs.length === 0 && (
            <p className="rounded-xl border border-dashed border-gray-200 px-3 py-6 text-center text-sm text-gray-500">
              No documents yet.
            </p>
          )}
        </div>

        <button
          onClick={startNew}
          className="flex items-center justify-center gap-1.5 rounded-xl border border-dashed border-gray-300 px-3 py-2.5 text-sm font-semibold text-gray-600 transition hover:bg-gray-50"
        >
          <Plus size={16} aria-hidden="true" /> New document
        </button>
      </div>

      {/* editor */}
      <div className="flex min-w-0 flex-col gap-3">
        {selected === null && !isNew ? (
          <div className="flex h-full min-h-48 items-center justify-center rounded-2xl border border-dashed border-gray-200 text-sm text-gray-500">
            Select a document to edit, or create a new one.
          </div>
        ) : (
          <>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              readOnly={!isNew}
              placeholder="Document title"
              className={`rounded-xl border border-gray-300 px-3 py-2.5 text-sm font-bold outline-none focus:border-brand focus:ring-2 focus:ring-brand/20 ${
                !isNew ? "bg-gray-50 text-gray-600" : "bg-white"
              }`}
            />
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={18}
              placeholder="Document text (markdown)…"
              className="resize-y rounded-xl border border-gray-300 bg-white px-3 py-2.5 font-mono text-sm leading-relaxed outline-none focus:border-brand focus:ring-2 focus:ring-brand/20"
            />
            <div className="flex items-center gap-2">
              <button
                onClick={save}
                disabled={busy}
                className="flex items-center gap-1.5 rounded-xl bg-brand px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-brand/90 disabled:opacity-50"
              >
                <Save size={16} aria-hidden="true" /> Save &amp; re-index
              </button>
              {!isNew && selected && (
                <button
                  onClick={remove}
                  disabled={busy}
                  className="flex items-center gap-1.5 rounded-xl border border-red-200 px-4 py-2.5 text-sm font-semibold text-red-600 transition hover:bg-red-50 disabled:opacity-50"
                >
                  <Trash2 size={16} aria-hidden="true" /> Delete
                </button>
              )}
            </div>
          </>
        )}
        {note && <p className="text-sm text-gray-600">{note}</p>}
      </div>
    </div>
  );
}