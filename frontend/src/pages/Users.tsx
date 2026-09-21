import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import type { User, UserRole } from "../types";
import { Badge, Card, EmptyState, ErrorBanner, Spinner } from "../components/ui";

const ROLES: UserRole[] = ["admin", "editor", "viewer"];

export default function Users() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ email: "", full_name: "", password: "", role: "viewer" as UserRole });
  const [revealed, setRevealed] = useState<{ id: string; password: string } | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setUsers(await api.listUsers());
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function create() {
    setError(null);
    try {
      await api.createUser(form);
      setForm({ email: "", full_name: "", password: "", role: "viewer" });
      setCreating(false);
      await load();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function update(id: string, patch: { role?: UserRole; is_active?: boolean }) {
    setError(null);
    try {
      await api.updateUser(id, patch);
      await load();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function resetPassword(id: string) {
    setError(null);
    try {
      const res = await api.resetUserPassword(id);
      setRevealed({ id, password: res.temporary_password });
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function remove(id: string) {
    if (!confirm("Delete this user? This cannot be undone.")) return;
    setError(null);
    try {
      await api.deleteUser(id);
      await load();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-white">User management</h1>
          <p className="mt-1 text-sm text-slate-400">
            Create accounts, assign roles, reset passwords and deactivate access.
          </p>
        </div>
        <button className="btn-primary" onClick={() => setCreating((v) => !v)}>
          {creating ? "Cancel" : "Add user"}
        </button>
      </header>

      {error && <ErrorBanner message={error} />}

      {revealed && (
        <Card className="border-accent/40 bg-accent/5">
          <p className="text-sm font-medium text-accent-soft">
            Temporary password generated — copy it now
          </p>
          <p className="mt-2 font-mono text-sm text-white">{revealed.password}</p>
          <button className="btn-ghost btn-sm mt-3" onClick={() => setRevealed(null)}>
            Dismiss
          </button>
        </Card>
      )}

      {creating && (
        <Card className="space-y-4">
          <h2 className="text-sm font-semibold text-white">New user</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="label">Full name</label>
              <input
                className="input"
                value={form.full_name}
                onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              />
            </div>
            <div>
              <label className="label">Email</label>
              <input
                className="input"
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
            </div>
            <div>
              <label className="label">Initial password</label>
              <input
                className="input"
                type="text"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                placeholder="min 6 characters"
              />
            </div>
            <div>
              <label className="label">Role</label>
              <select
                className="input"
                value={form.role}
                onChange={(e) => setForm({ ...form, role: e.target.value as UserRole })}
              >
                {ROLES.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="flex gap-2">
            <button className="btn-primary" onClick={create}>
              Create user
            </button>
            <button className="btn-ghost" onClick={() => setCreating(false)}>
              Cancel
            </button>
          </div>
        </Card>
      )}

      <Card className="overflow-hidden p-0">
        {loading ? (
          <div className="p-6">
            <Spinner label="Loading users…" />
          </div>
        ) : users.length === 0 ? (
          <div className="p-6">
            <EmptyState title="No users" />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>User</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Last login</th>
                  <th className="text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id}>
                    <td>
                      <p className="font-medium text-white">{u.full_name || "—"}</p>
                      <p className="text-xs text-slate-500">{u.email}</p>
                    </td>
                    <td>
                      <select
                        className="input max-w-[8rem]"
                        value={u.role}
                        onChange={(e) => update(u.id, { role: e.target.value as UserRole })}
                      >
                        {ROLES.map((r) => (
                          <option key={r} value={r}>
                            {r}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td>
                      <Badge tone={u.is_active ? "success" : "danger"}>
                        {u.is_active ? "active" : "disabled"}
                      </Badge>
                    </td>
                    <td className="text-xs text-slate-500">
                      {u.last_login_at ? new Date(u.last_login_at).toLocaleString() : "never"}
                    </td>
                    <td>
                      <div className="flex flex-wrap justify-end gap-2">
                        <button
                          className="btn-ghost btn-sm"
                          onClick={() => update(u.id, { is_active: !u.is_active })}
                        >
                          {u.is_active ? "Disable" : "Enable"}
                        </button>
                        <button className="btn-ghost btn-sm" onClick={() => resetPassword(u.id)}>
                          Reset password
                        </button>
                        <button className="btn-danger btn-sm" onClick={() => remove(u.id)}>
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}