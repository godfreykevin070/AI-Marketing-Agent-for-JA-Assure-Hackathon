import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import type { Digest } from "../types";
import { BRANDS } from "../types";
import { Card, EmptyState, ErrorBanner, Spinner } from "../components/ui";

export default function Research() {
  const [digests, setDigests] = useState<Digest[]>([]);
  const [brand, setBrand] = useState("jade");
  const [competitors, setCompetitors] = useState("");
  const [urls, setUrls] = useState("");
  const [topic, setTopic] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setDigests(await api.digests());
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function run() {
    setBusy(true);
    setError(null);
    try {
      await api.runResearch({
        brand,
        topic: topic || null,
        competitors: competitors.split(",").map((s) => s.trim()).filter(Boolean),
        urls: urls.split(",").map((s) => s.trim()).filter(Boolean),
      });
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-2xl font-semibold text-white">Competitor intelligence</h1>
        <p className="mt-1 text-sm text-slate-400">
          Monitors competitor pages, detects changes against the last snapshot, and produces
          a digest of what changed and what JA should do about it.
        </p>
      </header>

      <Card className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="label">Brand</label>
            <select className="input" value={brand} onChange={(e) => setBrand(e.target.value)}>
              {BRANDS.map((b) => (
                <option key={b.value} value={b.value}>
                  {b.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Topic focus (optional)</label>
            <input className="input" value={topic} onChange={(e) => setTopic(e.target.value)} />
          </div>
        </div>
        <div>
          <label className="label">Competitor names (comma separated)</label>
          <input
            className="input"
            value={competitors}
            onChange={(e) => setCompetitors(e.target.value)}
            placeholder="Provider A, Provider B"
          />
        </div>
        <div>
          <label className="label">Competitor URLs (comma separated)</label>
          <input
            className="input"
            value={urls}
            onChange={(e) => setUrls(e.target.value)}
            placeholder="https://competitor.example/pricing"
          />
        </div>
        <button className="btn-primary" onClick={run} disabled={busy}>
          {busy ? "Scanning…" : "Run research sweep"}
        </button>
      </Card>

      {error && <ErrorBanner message={error} />}

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-white">Digests</h2>
        {loading ? (
          <Spinner />
        ) : digests.length === 0 ? (
          <EmptyState title="No digests yet" hint="Run a research sweep to create one." />
        ) : (
          digests.map((d) => (
            <Card key={d.id} className="space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-white">
                  {d.brand} {d.topic ? `· ${d.topic}` : ""}
                </p>
                <span className="text-xs text-slate-500">
                  {new Date(d.created_at).toLocaleString()}
                </span>
              </div>
              <p className="text-sm text-slate-300">{d.summary}</p>
              {d.changes?.length > 0 && (
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500">What changed</p>
                  <ul className="mt-1 list-disc space-y-1 pl-4 text-xs text-slate-400">
                    {d.changes.map((c, i) => (
                      <li key={i}>{typeof c === "string" ? c : JSON.stringify(c)}</li>
                    ))}
                  </ul>
                </div>
              )}
              {d.recommendations?.length > 0 && (
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500">
                    Recommended actions
                  </p>
                  <ul className="mt-1 list-disc space-y-1 pl-4 text-xs text-sky-300">
                    {d.recommendations.map((r, i) => (
                      <li key={i}>{typeof r === "string" ? r : JSON.stringify(r)}</li>
                    ))}
                  </ul>
                </div>
              )}
              {d.sources?.length > 0 && (
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500">Sources</p>
                  <ul className="mt-1 space-y-1 text-xs">
                    {d.sources.slice(0, 6).map((s, i) => (
                      <li key={i} className="truncate">
                        <a
                          href={s.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-sky-300 hover:underline"
                        >
                          {s.title || s.url}
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </Card>
          ))
        )}
      </section>
    </div>
  );
}