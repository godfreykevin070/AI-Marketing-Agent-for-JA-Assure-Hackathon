import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../api";
import { Card, ErrorBanner, StatCard } from "../components/ui";

interface TrendPoint {
  week: string;
  reviews: number;
  rejection_rate: number;
  edit_rate: number;
  avg_edit_similarity: number | null;
}

export default function Analytics() {
  const [trend, setTrend] = useState<TrendPoint[]>([]);
  const [tags, setTags] = useState<{ reason_tag: string; count: number }[]>([]);
  const [engagement, setEngagement] = useState<{
    posts_tracked: number;
    totals: Record<string, number>;
    averages: Record<string, number>;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.feedbackTrend(), api.reasonTags(), api.engagement()])
      .then(([t, g, e]) => {
        setTrend(t);
        setTags(g);
        setEngagement(e);
      })
      .catch((e: Error) => setError(e.message));
  }, []);

  const latest = trend[trend.length - 1];
  const first = trend[0];
  const improving =
    first && latest ? latest.rejection_rate <= first.rejection_rate : undefined;

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-2xl font-semibold text-white">Analytics</h1>
        <p className="mt-1 text-sm text-slate-400">
          Proof the closed loop works: rejection rate and human edit effort should fall as
          the lessons memory grows.
        </p>
      </header>

      {error && <ErrorBanner message={error} />}

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Reviews recorded" value={latest?.reviews ?? 0} hint="Latest week" />
        <StatCard
          label="Rejection rate"
          value={`${Math.round((latest?.rejection_rate ?? 0) * 100)}%`}
          hint={improving === undefined ? undefined : improving ? "Trending down ↓" : "Trending up ↑"}
        />
        <StatCard
          label="Avg edit similarity"
          value={
            latest?.avg_edit_similarity != null
              ? `${Math.round(latest.avg_edit_similarity * 100)}%`
              : "—"
          }
          hint="Lower = fewer human edits needed"
        />
        <StatCard label="Posts tracked" value={engagement?.posts_tracked ?? 0} />
      </section>

      <Card>
        <h2 className="text-sm font-semibold text-white">Rejection & edit rate by week</h2>
        <div className="mt-4 h-72">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trend}>
              <CartesianGrid stroke="#1b2c47" />
              <XAxis dataKey="week" stroke="#64748b" fontSize={12} />
              <YAxis stroke="#64748b" fontSize={12} />
              <Tooltip
                contentStyle={{
                  background: "#0c1729",
                  border: "1px solid #1b2c47",
                  borderRadius: 8,
                }}
              />
              <Line
                type="monotone"
                dataKey="rejection_rate"
                stroke="#f87171"
                name="Rejection rate"
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="edit_rate"
                stroke="#5eead4"
                name="Edit rate"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <Card>
        <h2 className="text-sm font-semibold text-white">Why humans reject</h2>
        <div className="mt-4 h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={tags}>
              <CartesianGrid stroke="#1b2c47" />
              <XAxis dataKey="reason_tag" stroke="#64748b" fontSize={11} interval={0} angle={-20} textAnchor="end" height={70} />
              <YAxis stroke="#64748b" fontSize={12} />
              <Tooltip
                contentStyle={{
                  background: "#0c1729",
                  border: "1px solid #1b2c47",
                  borderRadius: 8,
                }}
              />
              <Bar dataKey="count" fill="#5eead4" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {engagement && Object.keys(engagement.totals ?? {}).length > 0 && (
        <Card>
          <h2 className="text-sm font-semibold text-white">Engagement totals</h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-3 lg:grid-cols-5">
            {Object.entries(engagement.totals).map(([key, value]) => (
              <div key={key}>
                <p className="text-xs uppercase tracking-wide text-slate-500">{key}</p>
                <p className="mt-1 text-xl font-semibold text-white">{value}</p>
                <p className="text-xs text-slate-500">
                  avg {engagement.averages[key] ?? 0}
                </p>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}