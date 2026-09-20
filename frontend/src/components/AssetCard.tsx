import { useState } from "react";
import type { Asset } from "../types";
import { Badge, Card, complianceTone, statusTone } from "./ui";

export default function AssetCard({
  asset,
  actions,
}: {
  asset: Asset;
  actions?: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const report = asset.compliance_report;

  return (
    <Card className="space-y-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="accent">{asset.brand}</Badge>
            <Badge>{asset.platform}</Badge>
            <Badge>{asset.format}</Badge>
            <Badge>{asset.language}</Badge>
            {asset.variant_label && <Badge tone="info">variant {asset.variant_label}</Badge>}
          </div>
          <h3 className="mt-2 truncate text-base font-semibold text-white">
            {asset.title || "(untitled)"}
          </h3>
          {asset.hook && <p className="mt-1 text-sm italic text-slate-400">{asset.hook}</p>}
        </div>

        <div className="flex shrink-0 flex-col items-end gap-2">
          <Badge tone={statusTone(asset.status)}>{asset.status}</Badge>
          <Badge tone={complianceTone(asset.compliance_status)}>
            compliance: {asset.compliance_status}
            {asset.compliance_score != null ? ` (${asset.compliance_score})` : ""}
          </Badge>
        </div>
      </div>

      <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-300">
        {open ? asset.body : `${asset.body.slice(0, 260)}${asset.body.length > 260 ? "…" : ""}`}
      </p>

      {open && (
        <>
          {asset.cta && (
            <p className="text-sm text-slate-400">
              <span className="font-medium text-slate-300">CTA:</span> {asset.cta}
            </p>
          )}
          {asset.hashtags.length > 0 && (
            <p className="text-sm text-accent-soft">{asset.hashtags.join(" ")}</p>
          )}
          {asset.media_urls.length > 0 && (
            <div className="space-y-1">
              <p className="text-xs uppercase tracking-wide text-slate-500">Media</p>
              {asset.media_urls.map((url) => (
                <a
                  key={url}
                  href={url}
                  target="_blank"
                  rel="noreferrer"
                  className="block truncate text-xs text-sky-300 hover:underline"
                >
                  {url}
                </a>
              ))}
            </div>
          )}
          {asset.video_script && (
            <div className="rounded-lg border border-ink-700 bg-ink-950/60 p-3">
              <p className="mb-2 text-xs uppercase tracking-wide text-slate-500">
                Reel script · {asset.video_script.total_seconds}s ·{" "}
                {asset.video_script.aspect_ratio}
              </p>
              <ol className="space-y-2">
                {asset.video_script.scenes.map((scene) => (
                  <li key={scene.index} className="text-xs text-slate-300">
                    <span className="font-medium text-accent-soft">
                      {scene.index}. {scene.on_screen_text}
                    </span>{" "}
                    <span className="text-slate-500">({scene.duration_seconds}s)</span>
                    <br />
                    <span className="text-slate-400">{scene.voiceover}</span>
                  </li>
                ))}
              </ol>
            </div>
          )}
          {report && (
            <div className="rounded-lg border border-ink-700 bg-ink-950/60 p-3">
              <p className="mb-2 text-xs uppercase tracking-wide text-slate-500">
                Compliance report
              </p>
              <p className="text-xs text-slate-300">
                Status: <strong>{report.status}</strong> · score {report.score} · layer{" "}
                {report.layer ?? "—"}
              </p>
              {report.failed_rules.length > 0 && (
                <p className="mt-1 text-xs text-amber-300">
                  Rules: {report.failed_rules.join(", ")}
                </p>
              )}
              <ul className="mt-2 list-disc space-y-1 pl-4 text-xs text-slate-400">
                {report.reasons.map((reason, i) => (
                  <li key={i}>{reason}</li>
                ))}
              </ul>
              {report.suggested_fix && (
                <p className="mt-2 text-xs text-sky-300">Fix: {report.suggested_fix}</p>
              )}
            </div>
          )}
        </>
      )}

      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-ink-800 pt-3">
        <button className="btn-ghost" onClick={() => setOpen((v) => !v)}>
          {open ? "Show less" : "Show more"}
        </button>
        {actions}
      </div>
    </Card>
  );
}