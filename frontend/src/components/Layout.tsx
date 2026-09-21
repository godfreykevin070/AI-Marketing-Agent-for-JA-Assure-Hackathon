import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { useAuth } from "../auth";
import { api } from "../api";
import {
  ChartIcon,
  CheckIcon,
  HomeIcon,
  LibraryIcon,
  LogoMark,
  LogoutIcon,
  RadarIcon,
  RocketIcon,
  SparkIcon,
  UsersIcon,
} from "./Icons";

const NAV = [
  { to: "/", label: "Dashboard", icon: HomeIcon, end: true },
  { to: "/generate", label: "Generate", icon: SparkIcon, canEdit: true },
  { to: "/review", label: "Review Queue", icon: CheckIcon, canEdit: true },
  { to: "/library", label: "Content Library", icon: LibraryIcon },
  { to: "/research", label: "Research", icon: RadarIcon },
  { to: "/leads", label: "Leads", icon: UsersIcon, canEdit: true },
  { to: "/publishing", label: "Publishing", icon: RocketIcon, canEdit: true },
  { to: "/analytics", label: "Analytics", icon: ChartIcon },
];

const ADMIN_NAV = [
  { to: "/users", label: "User Management", icon: UsersIcon },
];

const PAGE_TITLES: Record<string, string> = {
  "/": "Dashboard",
  "/generate": "Generate Content",
  "/review": "Review Queue",
  "/library": "Content Library",
  "/research": "Competitor Research",
  "/leads": "Lead Generation",
  "/publishing": "Publishing",
  "/analytics": "Analytics",
  "/users": "User Management",
};

export default function Layout() {
  const { user, logout, isAdmin, canEdit } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [health, setHealth] = useState<Record<string, unknown> | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth(null));
  }, []);

  useEffect(() => {
    setMobileNavOpen(false);
    setMenuOpen(false);
  }, [location.pathname]);

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  const title = PAGE_TITLES[location.pathname] ?? "JA Assure";
  const initials = (user?.full_name || user?.email || "?")
    .split(/\s+/)
    .map((s) => s[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  const renderNav = (
    items: typeof NAV,
    opts: { requireEdit?: boolean; requireAdmin?: boolean } = {}
  ) =>
    items
      .filter((i) => (opts.requireEdit ? canEdit : true))
      .filter((i) => (opts.requireAdmin ? isAdmin : true))
      .map((item) => {
        const Icon = item.icon;
        return (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `nav-link ${isActive ? "nav-link-active" : ""}`
            }
          >
            <Icon className="h-5 w-5" />
            <span>{item.label}</span>
          </NavLink>
        );
      });

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-ink-800
                    bg-ink-900/95 backdrop-blur transition-transform lg:static lg:translate-x-0
                    ${mobileNavOpen ? "translate-x-0" : "-translate-x-full"}`}
      >
        <div className="flex items-center gap-3 border-b border-ink-800 px-5 py-5">
          <LogoMark />
          <div>
            <p className="text-sm font-semibold tracking-tight text-white">JA Assure</p>
            <p className="text-[11px] uppercase tracking-widest text-slate-500">
              AI Marketing Agent
            </p>
          </div>
        </div>

        <nav className="scrollbar-thin flex-1 space-y-1 overflow-y-auto px-3 py-4">
          {renderNav(NAV, { requireEdit: false })}
          {isAdmin && (
            <>
              <p className="mt-6 px-3 text-[10px] font-semibold uppercase tracking-widest text-slate-600">
                Admin
              </p>
              <div className="mt-2 space-y-1">{renderNav(ADMIN_NAV)}</div>
            </>
          )}
        </nav>

        <div className="border-t border-ink-800 p-3">
          <div className="surface-flat p-3 text-xs">
            <p className="text-slate-500">System</p>
            <p className="mt-1 flex items-center gap-1.5 text-slate-300">
              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  health?.llm_enabled ? "bg-emerald-400" : "bg-amber-400"
                }`}
              />
              LLM: {health?.llm_enabled ? "live" : "fallback"}
            </p>
            <p className="mt-0.5 flex items-center gap-1.5 text-slate-300">
              <span className="h-1.5 w-1.5 rounded-full bg-sky-400" />
              Publisher: {String(health?.publisher_backend ?? "—")}
            </p>
          </div>
        </div>
      </aside>

      {mobileNavOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/60 lg:hidden"
          onClick={() => setMobileNavOpen(false)}
        />
      )}

      {/* Main */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 border-b border-ink-800 bg-ink-950/80 backdrop-blur">
          <div className="flex h-16 items-center justify-between gap-4 px-5 lg:px-8">
            <div className="flex items-center gap-3">
              <button
                className="btn-ghost btn-sm lg:hidden"
                onClick={() => setMobileNavOpen((v) => !v)}
                aria-label="Toggle navigation"
              >
                <svg viewBox="0 0 24 24" className="h-4 w-4" stroke="currentColor" fill="none" strokeWidth={2}>
                  <path d="M4 6h16M4 12h16M4 18h16" strokeLinecap="round" />
                </svg>
              </button>
              <div>
                <h1 className="text-base font-semibold text-white">{title}</h1>
                <p className="hidden text-xs text-slate-500 sm:block">
                  InsurTech group · SG · MY · HK · ID · TH
                </p>
              </div>
            </div>

            <div className="relative">
              <button
                onClick={() => setMenuOpen((v) => !v)}
                className="flex items-center gap-3 rounded-lg border border-ink-800 bg-ink-900/60 px-3 py-1.5 text-sm
                           transition-colors hover:border-ink-700 hover:bg-ink-800"
              >
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-accent/15 text-xs font-semibold text-accent-soft">
                  {initials || "?"}
                </span>
                <span className="hidden text-left sm:block">
                  <span className="block text-xs font-medium text-slate-100">
                    {user?.full_name || user?.email}
                  </span>
                  <span className="block text-[10px] uppercase tracking-widest text-slate-500">
                    {user?.role}
                  </span>
                </span>
              </button>

              {menuOpen && (
                <div
                  className="absolute right-0 mt-2 w-56 overflow-hidden rounded-xl border border-ink-800 bg-ink-900 shadow-2xl"
                  onMouseLeave={() => setMenuOpen(false)}
                >
                  <div className="border-b border-ink-800 px-4 py-3">
                    <p className="truncate text-sm font-medium text-white">
                      {user?.full_name || "Signed in"}
                    </p>
                    <p className="truncate text-xs text-slate-500">{user?.email}</p>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="flex w-full items-center gap-2 px-4 py-3 text-left text-sm text-rose-300 hover:bg-rose-500/10"
                  >
                    <LogoutIcon className="h-4 w-4" />
                    Sign out
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        <main className="mx-auto w-full max-w-7xl flex-1 px-5 py-8 lg:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}