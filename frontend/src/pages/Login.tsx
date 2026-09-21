import { useState, type FormEvent } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";
import { LogoMark } from "../components/Icons";

export default function Login() {
  const { login, user, loading } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@jaassure.com");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (!loading && user) return <Navigate to="/" replace />;

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(email, password);
      navigate("/", { replace: true });
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden px-4">
      {/* Background flourish */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-60"
        style={{
          background:
            "radial-gradient(60% 60% at 20% 20%, rgba(94,234,212,0.12), transparent 70%)," +
            "radial-gradient(50% 50% at 80% 80%, rgba(34,211,238,0.10), transparent 70%)",
        }}
      />

      <div className="relative w-full max-w-md">
        <div className="mb-8 flex items-center gap-3">
          <LogoMark className="h-10 w-10" />
          <div>
            <p className="text-lg font-semibold tracking-tight text-white">JA Assure</p>
            <p className="text-xs uppercase tracking-widest text-slate-500">
              AI Marketing Agent
            </p>
          </div>
        </div>

        <form onSubmit={submit} className="surface space-y-5 p-7">
          <div>
            <h1 className="text-xl font-semibold text-white">Sign in</h1>
            <p className="mt-1 text-sm text-slate-400">
              Use your JA Assure account to access the console.
            </p>
          </div>

          {error && (
            <div className="rounded-lg border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-sm text-rose-200">
              {error}
            </div>
          )}

          <div>
            <label className="label">Email</label>
            <input
              type="email"
              autoComplete="username"
              className="input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div>
            <label className="label">Password</label>
            <input
              type="password"
              autoComplete="current-password"
              className="input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button type="submit" className="btn-primary w-full" disabled={busy}>
            {busy ? "Signing in…" : "Sign in"}
          </button>

          <p className="border-t border-ink-800 pt-4 text-xs text-slate-500">
            Default admin: <span className="text-slate-300">admin@jaassure.com</span> /{" "}
            <span className="text-slate-300">admin@123</span> — change this immediately.
          </p>
        </form>
      </div>
    </div>
  );
}