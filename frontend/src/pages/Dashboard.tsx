import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import type { Asset, FeedbackStats, Overview } from "../types";
import { Card, EmptyState, ErrorBanner, StatCard, statusTone, Badge } from "../components/ui";

export default function Dashboard() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [stats, setStats] = useState<FeedbackStats | null>(null);
  const [queue, setQueue] = useState<Asset[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.overview(), api.feedbackStats(), api.reviewQueue()])
      .then(([o, s, q]) => {
        setOverview(o);
        setStats(s);
        setQueue(q);
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-sm text-slate-400">Loading dashboard…</p>;

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-2xl font-semibold text-white">Dashboard</h1>
        <p className="mt-1 text-sm text-slate-400">
          Project 1 (The Brain) produces approved assets. Project 2 (The Hands) publishes them.
        </p>
      </header>

      {error && <ErrorBanner message={error} />}

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Total assets" value={overview?.total_assets ?? 0} />
        <StatCard
          label="Awaiting review"
          value={overview?.by_status?.pending_review ?? 0}
          hint="Human approval is mandatory"
        />
        <StatCard
          label="Rejection rate"
          value={`${Math.round((overview?.rejection_rate ?? 0) * 100)}%`}
          hint={`${stats?.total_reviews ?? 0} reviews recorded`}
        />
        <StatCard label="Scheduled / published" value={overview?.posts_published ?? 0} />
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <Card>
          <h2 className="text-sm font-semibold text-white">Assets by brand</h2>
          <ul className="mt-4 space-y-2 text-sm">
            {Object.entries(overview?.by_brand ?? {}).map(([brand, count]) => (
              <li key={brand} className="flex items-center justify-between">
                <span className="text-slate-300">{brand}</span>
                <span className="text-slate-400">{count}</span>
              </li>
            ))}
            {Object.keys(overview?.by_brand ?? {}).length === 0 && (
              <li className="text-slate-500">No assets yet.</li>
            )}
          </ul>
        </Card>

        <Card>
          <h2 className="text-sm font-semibold text-white">Top rejection reasons</h2>
          <ul className="mt-4 space-y-2 text-sm">
            {(stats?.top_reason_tags ?? []).map(([tag, count]) => (
              <li key={tag} className="flex items-center justify-between">
                <span className="text-slate-300">{tag}</span>
                <span className="text-slate-400">{count}</span>
              </li>
            ))}
            {(stats?.top_reason_tags ?? []).length === 0 && (
              <li className="text-slate-500">No feedback captured yet.</li>
            )}
          </ul>
        </Card>
      </section>

      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">Needs your review</h2>
          <Link to="/review" className="text-sm text-accent-soft hover:underline">
            Open review queue →
          </Link>
        </div>
        {queue.length === 0 ? (
          <EmptyState
            title="Nothing waiting on you"
            hint="Generate content to fill the review queue."
          />
        ) : (
          <div className="space-y-3">
            {queue.slice(0, 5).map((asset) => (
              <Card key={asset.id} className="flex items-center justify-between gap-4">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-white">{asset.title}</p>
                  <p className="text-xs text-slate-500">
                    {asset.brand} · {asset.platform} · {asset.language}
                  </p>
                </div>
                <Badge tone={statusTone(asset.status)}>{asset.status}</Badge>
              </Card>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}