import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import type { Asset } from "../types";
import AssetCard from "../components/AssetCard";
import { EmptyState, ErrorBanner, Spinner } from "../components/ui";

const STATUSES = ["", "pending_review", "approved", "rejected", "scheduled", "published", "failed"];

export default function ContentLibrary() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [status, setStatus] = useState("");
  const [brand, setBrand] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (status) params.status = status;
      if (brand) params.brand = brand;
      setAssets(await api.listAssets(params));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [status, brand]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold text-white">Content library</h1>
        <p className="mt-1 text-sm text-slate-400">
          Every asset ever produced, with its compliance verdict and current status.
        </p>
      </header>

      <div className="flex flex-wrap gap-4">
        <div>
          <label className="label">Status</label>
          <select className="input" value={status} onChange={(e) => setStatus(e.target.value)}>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s || "all"}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="label">Brand</label>
          <select className="input" value={brand} onChange={(e) => setBrand(e.target.value)}>
            <option value="">all</option>
            <option value="jade">jade</option>
            <option value="jaguar_transit">jaguar_transit</option>
            <option value="doctorshield">doctorshield</option>
            <option value="ja_assure">ja_assure</option>
          </select>
        </div>
      </div>

      {error && <ErrorBanner message={error} />}
      {loading ? (
        <Spinner label="Loading assets…" />
      ) : assets.length === 0 ? (
        <EmptyState title="No assets match these filters" />
      ) : (
        <div className="space-y-4">
          {assets.map((asset) => (
            <AssetCard key={asset.id} asset={asset} />
          ))}
        </div>
      )}
    </div>
  );
}