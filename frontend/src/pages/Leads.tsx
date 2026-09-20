import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import type { Lead, Outreach } from "../types";
import { BRANDS, LEAD_CATEGORIES } from "../types";
import { Badge, Card, EmptyState, ErrorBanner, Spinner } from "../components/ui";

export default function Leads() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [outreach, setOutreach] = useState<Outreach[]>([]);
  const [brand, setBrand] = useState("jade");
  const [category, setCategory] = useState<string>("jeweller");
  const [country, setCountry] = useState("Singapore");
  const [limit, setLimit] = useState(6);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [l, o] = await Promise.all([api.leads(), api.outreach()]);
      setLeads(l);
      setOutreach(o);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function discover() {
    setBusy(true);
    setError(null);
    try {
      await api.discoverLeads({ brand, category, country, limit });
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function draft(lead: Lead) {
    setBusy(true);
    try {
      await api.createOutreach({ lead_id: lead.id, language: "en", channel: "email" });
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
        <h1 className="text-2xl font-semibold text-white">Lead generation</h1>
        <p className="mt-1 text-sm text-slate-400">
          Discovers prospects from public sources, scores fit, and drafts compliant outreach
          for human review.
        </p>
      </header>

      <Card className="space-y-4">
        <div className="grid gap-4 md:grid-cols-4">
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
            <label className="label">Category</label>
            <select
              className="input"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              {LEAD_CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Country</label>
            <input className="input" value={country} onChange={(e) => setCountry(e.target.value)} />
          </div>
          <div>
            <label className="label">Max results</label>
            <input
              type="number"
              min={1}
              max={25}
              className="input"
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
            />
          </div>
        </div>
        <button className="btn-primary" onClick={discover} disabled={busy}>
          {busy ? "Running lead agent…" : "Discover leads"}
        </button>
      </Card>

      {error && <ErrorBanner message={error} />}

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-white">Prospects ({leads.length})</h2>
        {loading ? (
          <Spinner />
        ) : leads.length === 0 ? (
          <EmptyState title="No leads yet" hint="Run a discovery sweep to populate this list." />
        ) : (
          <div className="space-y-3">
            {leads.map((lead) => (
              <Card key={lead.id} className="space-y-3">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="font-medium text-white">{lead.company_name}</p>
                    <p className="text-xs text-slate-500">
                      {lead.category} · {lead.city ?? ""} {lead.country ?? ""}
                    </p>
                    {lead.contact_email && (
                      <p className="mt-1 text-xs text-accent-soft">{lead.contact_email}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge tone={lead.fit_score >= 70 ? "success" : lead.fit_score >= 50 ? "warning" : "neutral"}>
                      fit {Math.round(lead.fit_score)}
                    </Badge>
                    <Badge>{lead.status}</Badge>
                  </div>
                </div>
                {lead.score_reasons.length > 0 && (
                  <ul className="list-disc space-y-1 pl-4 text-xs text-slate-400">
                    {lead.score_reasons.map((r, i) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                )}
                <div className="flex gap-2">
                  <button className="btn-ghost" onClick={() => draft(lead)} disabled={busy}>
                    Draft outreach
                  </button>
                  {lead.website && (
                    <a className="btn-ghost" href={lead.website} target="_blank" rel="noreferrer">
                      Website
                    </a>
                  )}
                </div>
              </Card>
            ))}
          </div>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-white">Outreach drafts ({outreach.length})</h2>
        {outreach.length === 0 ? (
          <EmptyState title="No outreach drafted yet" />
        ) : (
          outreach.map((o) => (
            <Card key={o.id} className="space-y-2">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-medium text-white">{o.subject}</p>
                <Badge tone={o.compliance_status === "pass" ? "success" : "warning"}>
                  {o.compliance_status}
                </Badge>
              </div>
              <p className="whitespace-pre-wrap text-sm text-slate-300">{o.body}</p>
              <div className="flex gap-2 pt-2">
                <button
                  className="btn-primary"
                  onClick={() => api.decideOutreach(o.id, "approve").then(load)}
                >
                  Approve
                </button>
                <button
                  className="btn-danger"
                  onClick={() => api.decideOutreach(o.id, "reject").then(load)}
                >
                  Reject
                </button>
              </div>
            </Card>
          ))
        )}
      </section>
    </div>
  );
}