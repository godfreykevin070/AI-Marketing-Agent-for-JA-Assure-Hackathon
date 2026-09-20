import { useState } from "react";
import { api } from "../api";
import type { Asset } from "../types";
import { BRANDS, LANGUAGES, PLATFORMS, type Brand, type Language, type Platform } from "../types";
import AssetCard from "../components/AssetCard";
import { Card, ErrorBanner, Spinner } from "../components/ui";

const SUGGESTED_TOPICS: Record<string, string[]> = {
  jade: [
    "2026 gold price volatility and jewellers block cover",
    "What to check before lending stock for an exhibition",
  ],
  jaguar_transit: [
    "Transit cover for high-value electronics last mile",
    "Incoterms and where your liability actually ends",
  ],
  doctorshield: [
    "Indemnity limits: how much is enough for a clinic",
    "What medico-legal cover does and does not include",
  ],
  ja_assure: ["Why specialist cover beats a generic commercial policy"],
};

export default function Generate() {
  const [brand, setBrand] = useState<Brand>("jade");
  const [topic, setTopic] = useState(SUGGESTED_TOPICS.jade[0]);
  const [brief, setBrief] = useState("");
  const [platforms, setPlatforms] = useState<Platform[]>(["linkedin", "instagram"]);
  const [languages, setLanguages] = useState<Language[]>(["en"]);
  const [variants, setVariants] = useState(2);
  const [includeVideo, setIncludeVideo] = useState(true);

  const [assets, setAssets] = useState<Asset[]>([]);
  const [errors, setErrors] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function toggle<T>(list: T[], value: T, setter: (v: T[]) => void) {
    setter(list.includes(value) ? list.filter((v) => v !== value) : [...list, value]);
  }

  async function run() {
    setLoading(true);
    setError(null);
    setAssets([]);
    try {
      const response = await api.generate({
        brand,
        topic,
        brief: brief || null,
        platforms,
        languages,
        variants,
        include_video: includeVideo,
        auto_compliance: true,
      });
      setAssets(response.assets);
      setErrors(response.errors ?? []);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-2xl font-semibold text-white">Generate content</h1>
        <p className="mt-1 text-sm text-slate-400">
          The Brain runs research → content → localisation → video → compliance, then
          writes everything into the pending-review queue.
        </p>
      </header>

      <Card className="space-y-5">
        <div className="grid gap-5 md:grid-cols-2">
          <div>
            <label className="label">Brand</label>
            <select
              className="input"
              value={brand}
              onChange={(e) => {
                const next = e.target.value as Brand;
                setBrand(next);
                setTopic(SUGGESTED_TOPICS[next]?.[0] ?? topic);
              }}
            >
              {BRANDS.map((b) => (
                <option key={b.value} value={b.value}>
                  {b.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="label">A/B variants per platform</label>
            <input
              type="number"
              min={1}
              max={3}
              className="input"
              value={variants}
              onChange={(e) => setVariants(Number(e.target.value))}
            />
          </div>
        </div>

        <div>
          <label className="label">Topic / idea</label>
          <input className="input" value={topic} onChange={(e) => setTopic(e.target.value)} />
          <div className="mt-2 flex flex-wrap gap-2">
            {(SUGGESTED_TOPICS[brand] ?? []).map((s) => (
              <button
                key={s}
                onClick={() => setTopic(s)}
                className="rounded-full border border-ink-600 px-3 py-1 text-xs text-slate-400 hover:border-accent hover:text-accent-soft"
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="label">Extra brief (optional)</label>
          <textarea
            className="input h-24"
            value={brief}
            onChange={(e) => setBrief(e.target.value)}
            placeholder="Tone notes, must-mention points, campaign context…"
          />
        </div>

        <div className="grid gap-5 md:grid-cols-2">
          <div>
            <label className="label">Platforms</label>
            <div className="flex flex-wrap gap-2">
              {PLATFORMS.map((p) => (
                <button
                  key={p}
                  onClick={() => toggle(platforms, p, setPlatforms)}
                  className={`rounded-lg border px-3 py-1.5 text-xs ${
                    platforms.includes(p)
                      ? "border-accent bg-accent/15 text-accent-soft"
                      : "border-ink-600 text-slate-400 hover:border-ink-600"
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="label">Languages (first = source)</label>
            <div className="flex flex-wrap gap-2">
              {LANGUAGES.map((l) => (
                <button
                  key={l.value}
                  onClick={() => toggle(languages, l.value, setLanguages)}
                  className={`rounded-lg border px-3 py-1.5 text-xs ${
                    languages.includes(l.value)
                      ? "border-accent bg-accent/15 text-accent-soft"
                      : "border-ink-600 text-slate-400"
                  }`}
                >
                  {l.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <label className="flex items-center gap-3 text-sm text-slate-300">
          <input
            type="checkbox"
            checked={includeVideo}
            onChange={(e) => setIncludeVideo(e.target.checked)}
            className="h-4 w-4 accent-teal-400"
          />
          Generate short-form video scripts and render Reels (FFmpeg)
        </label>

        <button className="btn-primary" onClick={run} disabled={loading || platforms.length === 0}>
          {loading ? "Running the pipeline…" : "Generate"}
        </button>

        {loading && <Spinner label="Agents are researching, writing and checking compliance…" />}
      </Card>

      {error && <ErrorBanner message={error} />}

      {errors.length > 0 && (
        <Card>
          <p className="text-sm font-medium text-amber-300">Pipeline warnings</p>
          <ul className="mt-2 list-disc space-y-1 pl-4 text-xs text-slate-400">
            {errors.map((e, i) => (
              <li key={i}>{e}</li>
            ))}
          </ul>
        </Card>
      )}

      {assets.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-lg font-semibold text-white">
            Generated assets ({assets.length})
          </h2>
          {assets.map((asset) => (
            <AssetCard key={asset.id} asset={asset} />
          ))}
        </section>
      )}
    </div>
  );
}