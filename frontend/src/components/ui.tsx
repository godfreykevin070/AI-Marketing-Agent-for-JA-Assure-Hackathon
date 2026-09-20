import type { ReactNode } from "react";

export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={`card ${className}`}>{children}</div>;
}

export function StatCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: ReactNode;
  hint?: string;
}) {
  return (
    <div className="card">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
        {label}
      </p>
      <p className="mt-2 text-3xl font-semibold text-white">{value}</p>
      {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
    </div>
  );
}

const TONES: Record<string, string> = {
  neutral: "bg-ink-700 text-slate-200",
  accent: "bg-accent/15 text-accent-soft border border-accent/30",
  success: "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30",
  warning: "bg-amber-500/15 text-amber-300 border border-amber-500/30",
  danger: "bg-rose-500/15 text-rose-300 border border-rose-500/30",
  info: "bg-sky-500/15 text-sky-300 border border-sky-500/30",
};

export function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: keyof typeof TONES | string;
}) {
  const cls = TONES[tone] ?? TONES.neutral;
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${cls}`}
    >
      {children}
    </span>
  );
}

export function statusTone(status: string): string {
  switch (status) {
    case "approved":
    case "published":
      return "success";
    case "rejected":
    case "failed":
      return "danger";
    case "pending_review":
      return "warning";
    case "scheduled":
      return "info";
    default:
      return "neutral";
  }
}

export function complianceTone(status: string): string {
  switch (status) {
    case "pass":
      return "success";
    case "needs_revision":
      return "warning";
    case "fail":
      return "danger";
    default:
      return "neutral";
  }
}

export function Spinner({ label = "Working…" }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 text-sm text-slate-400">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-ink-600 border-t-accent" />
      {label}
    </div>
  );
}

export function EmptyState({
  title,
  hint,
}: {
  title: string;
  hint?: string;
}) {
  return (
    <div className="rounded-xl border border-dashed border-ink-600 p-10 text-center">
      <p className="text-sm font-medium text-slate-300">{title}</p>
      {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
    </div>
  );
}

export function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
      {message}
    </div>
  );
}