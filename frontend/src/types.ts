export type Brand = "ja_assure" | "jade" | "jaguar_transit" | "doctorshield";
export type Platform = "linkedin" | "instagram" | "x" | "tiktok" | "blog";
export type Language = "en" | "ms" | "id" | "th" | "zh";

export interface Asset {
  id: string;
  campaign_id: string | null;
  brand: string;
  platform: string;
  language: string;
  format: string;
  title: string;
  hook: string | null;
  body: string;
  cta: string | null;
  hashtags: string[];
  media_urls: string[];
  visual_prompt: string | null;
  video_script: VideoScript | null;
  variant_label: string | null;
  status: string;
  compliance_status: string;
  compliance_score: number | null;
  compliance_report: ComplianceReport | null;
  source_topic: string | null;
  created_at: string;
  updated_at: string;
}

export interface ComplianceVerdict {
  status: string;
  score: number;
  failed_rules: string[];
  reasons: string[];
  offending_spans: string[];
  suggested_fix: string;
  layer?: string;
}

export type ComplianceReport = ComplianceVerdict;

export interface VideoScene {
  index: number;
  duration_seconds: number;
  on_screen_text: string;
  voiceover: string;
  visual_direction: string;
}

export interface VideoScript {
  title: string;
  hook: string;
  total_seconds: number;
  aspect_ratio: string;
  scenes: VideoScene[];
  caption: string;
  hashtags: string[];
}

export interface GenerateResponse {
  run_id: string;
  assets: Asset[];
  research: Record<string, unknown> | null;
  errors: string[];
}

export interface Lead {
  id: string;
  company_name: string;
  category: string;
  country: string | null;
  city: string | null;
  website: string | null;
  contact_name: string | null;
  contact_email: string | null;
  contact_role: string | null;
  source_url: string | null;
  brand_fit: string | null;
  fit_score: number;
  score_reasons: string[];
  status: string;
  created_at: string;
}

export interface Outreach {
  id: string;
  lead_id: string;
  channel: string;
  language: string;
  subject: string | null;
  body: string;
  status: string;
  compliance_status: string;
  created_at: string;
}

export interface Digest {
  id: string;
  brand: string;
  topic: string | null;
  summary: string;
  changes: string[];
  recommendations: string[];
  sources: { title?: string; url?: string; snippet?: string }[];
  created_at: string;
}

export interface Lesson {
  id: string;
  brand: string;
  platform: string | null;
  reason_tag: string | null;
  text: string;
  occurrences: number;
  active: boolean;
}

export interface PostResult {
  id: string;
  asset_id: string;
  platform: string;
  publisher: string;
  external_post_id: string | null;
  permalink: string | null;
  status: string;
  scheduled_for: string | null;
  posted_at: string | null;
  error: string | null;
  analytics: Record<string, number | string>;
  created_at: string;
}

export interface FeedbackStats {
  total_reviews: number;
  approved: number;
  edited: number;
  rejected: number;
  rejection_rate: number;
  edit_rate: number;
  avg_edit_similarity: number | null;
  top_reason_tags: [string, number][];
}

export interface Overview {
  total_assets: number;
  by_status: Record<string, number>;
  by_brand: Record<string, number>;
  by_platform: Record<string, number>;
  total_reviews: number;
  rejection_rate: number;
  posts_published: number;
}

export const BRANDS: { value: Brand; label: string }[] = [
  { value: "jade", label: "Jade — Jewellers Block" },
  { value: "jaguar_transit", label: "Jaguar Transit — High-Value Goods" },
  { value: "doctorshield", label: "DoctorShield — Medical Indemnity" },
  { value: "ja_assure", label: "JA Assure — Group" },
];

export const PLATFORMS: Platform[] = ["linkedin", "instagram", "x", "tiktok", "blog"];
export const LANGUAGES: { value: Language; label: string }[] = [
  { value: "en", label: "English" },
  { value: "ms", label: "Bahasa Malaysia" },
  { value: "id", label: "Bahasa Indonesia" },
  { value: "th", label: "Thai" },
  { value: "zh", label: "Chinese" },
];

export const REASON_TAGS = [
  "too_salesy",
  "inaccurate_claim",
  "off_brand_tone",
  "wrong_cta",
  "compliance_risk",
  "too_long",
  "poor_visual",
  "not_localised",
  "weak_hook",
  "other",
] as const;

export const LEAD_CATEGORIES = [
  "jeweller",
  "clinic",
  "doctor",
  "sme",
  "courier",
  "logistics",
] as const;

export type UserRole = "admin" | "editor" | "viewer";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export type MediaMode = "none" | "image" | "video";