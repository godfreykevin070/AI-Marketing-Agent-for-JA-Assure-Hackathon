import type {
  Asset,
  Digest,
  FeedbackStats,
  GenerateResponse,
  Lead,
  Lesson,
  LoginResponse,
  Outreach,
  Overview,
  PostResult,
  User,
  UserRole,
} from "./types";

const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? "";

function authHeader(): Record<string, string> {
  const token = localStorage.getItem("ja_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${BASE}/api${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...authHeader(),
      ...(init.headers ?? {}),
    },
  });

  if (response.status === 401) {
    localStorage.removeItem("ja_token");
    localStorage.removeItem("ja_user");
    if (!window.location.pathname.startsWith("/login")) {
      window.location.href = "/login";
    }
    throw new Error("Session expired. Please sign in again.");
  }

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* keep statusText */
    }
    throw new Error(detail);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  // --- Auth ---
  login: (email: string, password: string) =>
    request<LoginResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  me: () => request<User>("/auth/me"),
  changePassword: (current_password: string, new_password: string) =>
    request<{ status: string }>("/auth/change-password", {
      method: "POST",
      body: JSON.stringify({ current_password, new_password }),
    }),

  // --- Users (admin) ---
  listUsers: () => request<User[]>("/users"),
  createUser: (payload: { email: string; password: string; full_name: string; role: UserRole }) =>
    request<User>("/users", { method: "POST", body: JSON.stringify(payload) }),
  updateUser: (
    id: string,
    payload: { full_name?: string; role?: UserRole; is_active?: boolean }
  ) => request<User>(`/users/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  resetUserPassword: (id: string) =>
    request<{ temporary_password: string }>(`/users/${id}/reset-password`, {
      method: "POST",
    }),
  deleteUser: (id: string) => request<void>(`/users/${id}`, { method: "DELETE" }),

  // --- Health ---
  health: () => request<Record<string, unknown>>("/health"),

  // --- Content ---
  generate: (payload: Record<string, unknown>) =>
    request<GenerateResponse>("/content/generate", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listAssets: (params: Record<string, string | number> = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).map(([k, v]) => [k, String(v)])
    ).toString();
    return request<Asset[]>(`/content/assets${qs ? `?${qs}` : ""}`);
  },

  // --- Review ---
  reviewQueue: () => request<Asset[]>("/review/queue"),
  decide: (assetId: string, payload: Record<string, unknown>) =>
    request<Asset>(`/review/${assetId}/decision`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  lessons: (brand?: string) =>
    request<Lesson[]>(`/review/lessons${brand ? `?brand=${brand}` : ""}`),
  feedbackStats: (brand?: string) =>
    request<FeedbackStats>(`/review/stats${brand ? `?brand=${brand}` : ""}`),

  // --- Research ---
  runResearch: (payload: Record<string, unknown>) =>
    request<Digest>("/research/competitors", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  digests: (brand?: string) =>
    request<Digest[]>(`/research/digests${brand ? `?brand=${brand}` : ""}`),

  // --- Leads ---
  discoverLeads: (payload: Record<string, unknown>) =>
    request<Lead[]>("/leads/discover", { method: "POST", body: JSON.stringify(payload) }),
  leads: (params: Record<string, string | number> = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).map(([k, v]) => [k, String(v)])
    ).toString();
    return request<Lead[]>(`/leads${qs ? `?${qs}` : ""}`);
  },
  createOutreach: (payload: Record<string, unknown>) =>
    request<Outreach>("/leads/outreach", { method: "POST", body: JSON.stringify(payload) }),
  outreach: () => request<Outreach[]>("/leads/outreach"),
  decideOutreach: (id: string, decision: "approve" | "reject") =>
    request<Outreach>(`/leads/outreach/${id}/decision?decision=${decision}`, {
      method: "POST",
    }),

  // --- Publishing (Project 2) ---
  publishQueue: () => request<Asset[]>("/publishing/queue"),
  runPublishWorker: () =>
    request<{ published: string[]; failed: unknown[]; count: number }>("/publishing/run", {
      method: "POST",
    }),
  pullAnalytics: () =>
    request<{ updated: number }>("/publishing/pull-analytics", { method: "POST" }),
  postResults: () => request<PostResult[]>("/publishing/results"),

  // --- Analytics ---
  overview: () => request<Overview>("/analytics/overview"),
  feedbackTrend: () =>
    request<
      {
        week: string;
        reviews: number;
        rejection_rate: number;
        edit_rate: number;
        avg_edit_similarity: number | null;
      }[]
    >("/analytics/feedback-trend"),
  reasonTags: () =>
    request<{ reason_tag: string; count: number }[]>("/analytics/reason-tags"),
  engagement: () =>
    request<{
      posts_tracked: number;
      totals: Record<string, number>;
      averages: Record<string, number>;
    }>("/analytics/engagement"),
};