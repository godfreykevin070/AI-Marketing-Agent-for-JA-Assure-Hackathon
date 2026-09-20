import { NavLink, Outlet } from "react-router-dom";
import { useEffect, useState } from "react";
import { api } from "../api";

const NAV = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/generate", label: "Generate" },
  { to: "/review", label: "Review Queue" },
  { to: "/library", label: "Content Library" },
  { to: "/research", label: "Research" },
  { to: "/leads", label: "Leads" },
  { to: "/publishing", label: "Publishing" },
  { to: "/analytics", label: "Analytics" },
];

export default function Layout() {
  const [health, setHealth] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth(null));
  }, []);

  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-64 shrink-0 border-r border-ink-800 bg-ink-900/60 p-5 lg:block">
        <div className="mb-8">
          <p className="text-lg font-semibold text-white">JA Assure</p>
          <p className="text-xs text-slate-500">AI Marketing Agent</p>
        </div>
        <nav className="space-y-1">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `block rounded-lg px-3 py-2 text-sm transition-colors ${
                  isActive
                    ? "bg-accent/15 font-medium text-accent-soft"
                    : "text-slate-400 hover:bg-ink-800 hover:text-slate-200"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-8 rounded-lg border border-ink-700 p-3 text-xs">
          <p className="text-slate-500">System</p>
          <p className="mt-1 text-slate-300">
            LLM:{" "}
            <span className={health?.llm_enabled ? "text-emerald-400" : "text-amber-400"}>
              {health?.llm_enabled ? "live" : "fallback"}
            </span>
          </p>
          <p className="text-slate-300">
            Publisher: <span className="text-slate-400">{String(health?.publisher_backend ?? "—")}</span>
          </p>
        </div>
      </aside>

      <main className="flex-1 overflow-x-hidden">
        <header className="border-b border-ink-800 bg-ink-900/40 px-6 py-4 lg:hidden">
          <p className="font-semibold text-white">JA Assure — AI Marketing Agent</p>
        </header>
        <div className="mx-auto max-w-6xl px-6 py-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}