import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import type { Asset, Lesson } from "../types";
import { REASON_TAGS } from "../types";
import AssetCard from "../components/AssetCard";
import { Card, EmptyState, ErrorBanner, Spinner } from "../components/ui";

export default function ReviewQueue() {
  const [queue, setQueue] = useState<Asset[]>([]);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [editing, setEditing] = useState<string | null>(null);
  const [draftBody, setDraftBody] = useState("");
  const [reasonTag, setReasonTag] = useState<string>(REASON_TAGS[0]);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [q, l] = await Promise.all([api.reviewQueue(), api.lessons()]);
      setQueue(q);
      setLessons(l);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function decide(asset: Asset, decision: "approve" | "edit" | "reject") {
    setBusy(asset.id);
    setError(null);
    try {
      const payload: Record<string, unknown> = {
        decision,
        editor: "dashboard-user",
        reason_tag: decision === "approve" ? null : reasonTag,
        note: decision === "approve" ? null : note || null,
      };
      if (decision === "edit") payload.edited_body = draftBody;

      await api.decide(asset.id, payload);
      setEditing(null);
      setNote("");
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(null);
    }
  }

  if (loading) return <Spinner label="Loading review queue…" />;

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-2xl font-semibold text-white">Review queue</h1>
        <p className="mt-1 text-sm text-slate-400">
          Nothing becomes publish-ready without a human decision. Every rejection or edit
          teaches the content agent for next time.
        </p>
      </header>

      {error && <ErrorBanner message={error} />}

      <Card className="space-y-3">
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="label">Reason tag (required for edit/reject)</label>
            <select
              className="input"
              value={reasonTag}
              onChange={(e) => setReasonTag(e.target.value)}
            >
              {REASON_TAGS.map((tag) => (
                <option key={tag} value={tag}>
                  {tag}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Note (what exactly was wrong)</label>
            <input
              className="input"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="e.g. Opens with a product feature instead of a risk scenario"
            />
          </div>
        </div>
      </Card>

      {queue.length === 0 ? (
        <EmptyState title="Queue is empty" hint="Every asset has been reviewed." />
      ) : (
        <section className="space-y-4">
          {queue.map((asset) => (
            <AssetCard
              key={asset.id}
              asset={asset}
              actions={
                <div className="flex flex-wrap items-center gap-2">
                  {editing === asset.id ? (
                    <>
                      <button
                        className="btn-primary"
                        disabled={busy === asset.id}
                        onClick={() => decide(asset, "edit")}
                      >
                        Save & approve
                      </button>
                      <button className="btn-ghost" onClick={() => setEditing(null)}>
                        Cancel
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        className="btn-primary"
                        disabled={busy === asset.id}
                        onClick={() => decide(asset, "approve")}
                      >
                        Approve
                      </button>
                      <button
                        className="btn-ghost"
                        onClick={() => {
                          setEditing(asset.id);
                          setDraftBody(asset.body);
                        }}
                      >
                        Edit
                      </button>
                      <button
                        className="btn-danger"
                        disabled={busy === asset.id}
                        onClick={() => decide(asset, "reject")}
                      >
                        Reject
                      </button>
                    </>
                  )}
                </div>
              }
            />
          ))}

          {editing && (
            <Card className="space-y-3">
              <label className="label">Edit body before approving</label>
              <textarea
                className="input h-64 font-mono text-xs"
                value={draftBody}
                onChange={(e) => setDraftBody(e.target.value)}
              />
            </Card>
          )}
        </section>
      )}

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-white">Lessons learned memory</h2>
        <p className="text-sm text-slate-400">
          These instructions are injected into the content agent on the next run.
        </p>
        {lessons.length === 0 ? (
          <EmptyState title="No lessons yet" hint="Reject or edit an asset to teach the system." />
        ) : (
          <div className="space-y-2">
            {lessons.map((lesson) => (
              <Card key={lesson.id} className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm text-slate-200">{lesson.text}</p>
                  <p className="mt-1 text-xs text-slate-500">
                    {lesson.brand}
                    {lesson.platform ? ` · ${lesson.platform}` : ""}
                    {lesson.reason_tag ? ` · ${lesson.reason_tag}` : ""}
                  </p>
                </div>
                <span className="shrink-0 rounded-full bg-ink-700 px-2.5 py-0.5 text-xs text-slate-300">
                  ×{lesson.occurrences}
                </span>
              </Card>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}