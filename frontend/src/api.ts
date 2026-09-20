import type {
  Asset,
  Digest,
  FeedbackStats,
  GenerateResponse,
  Lead,
  Lesson,
  Outreach,
  Overview,
  PostResult,
} from "./types";

const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });

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
    request<Lead[]>("/leads/discover", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  leads: (params: Record<string, string | number> = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).map(([k, v]) => [k, String(v)])
    ).toString();
    return request<Lead[]>(`/leads${qs ? `?${qs}` : ""}`);
  },
  createOutreach: (payload: Record<string, unknown>) =>
    request<Outreach>("/leads/outreach", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  outreach: () => request<Outreach[]>("/leads/outreach"),
  decideOutreach: (id: string, decision: "approve" | "reject") =>
    request<Outreach>(`/leads/outreach/${id}/decision?decision=${decision}`, {
      method: "POST",
    }),

  // --- Publishing (Project 2) ---
  publishQueue: () => request<Asset[]>("/publishing/queue"),
  runPublishWorker: () =>
    request<{ published: string[]; failed: unknown[]; count: number }>(
      "/publishing/run",
      { method: "POST" }
    ),
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