import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import type { Asset, PostResult } from "../types";
import { Badge, Card, EmptyState, ErrorBanner, Spinner } from "../components/ui";

export default function Publishing() {
  const [queue, setQueue] = useState<Asset[]>([]);
  const [results, setResults] = useState<PostResult[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [q, r] = await Promise.all([api.publishQueue(), api.postResults()]);
      setQueue(q);
      setResults(r);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function runWorker() {
    setBusy("run");
    try {
      await api.runPublishWorker();
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(null);
    }
  }

  async function pullAnalytics() {
    setBusy("analytics");
    try {
      await api.pullAnalytics();
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-2xl font-semibold text-white">
          Project 2 — The Hands
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          A background worker polls the database for approved rows, publishes them via the
          posting API, stores the returned post id, and flips status to scheduled. A second
          job pulls engagement back.
        </p>
      </header>

      <Card className="flex flex-wrap gap-3">
        <button className="btn-primary" onClick={runWorker} disabled={busy !== null}>
          {busy === "run" ? "Publishing…" : "Run worker now"}
        </button>
        <button className="btn-ghost" onClick={pullAnalytics} disabled={busy !== null}>
          {busy === "analytics" ? "Pulling…" : "Pull analytics"}
        </button>
        <button className="btn-ghost" onClick={load}>
          Refresh
        </button>
      </Card>

      {error && <ErrorBanner message={error} />}

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-white">
          Approved queue ({queue.length})
        </h2>
        {loading ? (
          <Spinner />
        ) : queue.length === 0 ? (
          <EmptyState
            title="Nothing approved yet"
            hint="Approve assets in the review queue and the worker will pick them up."
          />
        ) : (
          queue.map((asset) => (
            <Card key={asset.id} className="flex items-center justify-between gap-4">
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-white">{asset.title}</p>
                <p className="text-xs text-slate-500">
                  {asset.brand} · {asset.platform} · {asset.language}
                </p>
              </div>
              <Badge tone="info">{asset.status}</Badge>
            </Card>
          ))
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-white">Post results ({results.length})</h2>
        {results.length === 0 ? (
          <EmptyState title="No posts yet" />
        ) : (
          results.map((r) => (
            <Card key={r.id} className="space-y-2">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-medium text-white">
                    {r.platform} · {r.publisher}
                  </p>
                  <p className="text-xs text-slate-500">
                    post id: {r.external_post_id ?? "—"} · asset {r.asset_id.slice(0, 8)}
                  </p>
                </div>
                <Badge
                  tone={
                    r.status === "published"
                      ? "success"
                      : r.status === "failed"
                      ? "danger"
                      : "info"
                  }
                >
                  {r.status}
                </Badge>
              </div>
              {r.error && <p className="text-xs text-rose-300">{r.error}</p>}
              {Object.keys(r.analytics ?? {}).length > 0 && (
                <div className="flex flex-wrap gap-3 text-xs text-slate-400">
                  {Object.entries(r.analytics).map(([k, v]) => (
                    <span key={k}>
                      {k}: <strong className="text-slate-200">{String(v)}</strong>
                    </span>
                  ))}
                </div>
              )}
            </Card>
          ))
        )}
      </section>
    </div>
  );
}