type P = { className?: string };

const base = "h-5 w-5 stroke-current fill-none";
const stroke = { strokeWidth: 1.75, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };

export const HomeIcon = ({ className = base }: P) => (
  <svg viewBox="0 0 24 24" className={className} {...stroke}>
    <path d="M3 10.5 12 3l9 7.5V21H3z" />
    <path d="M9 21v-6h6v6" />
  </svg>
);
export const SparkIcon = ({ className = base }: P) => (
  <svg viewBox="0 0 24 24" className={className} {...stroke}>
    <path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M5.6 18.4l2.8-2.8M15.6 8.4l2.8-2.8" />
  </svg>
);
export const CheckIcon = ({ className = base }: P) => (
  <svg viewBox="0 0 24 24" className={className} {...stroke}>
    <path d="M20 6 9 17l-5-5" />
  </svg>
);
export const LibraryIcon = ({ className = base }: P) => (
  <svg viewBox="0 0 24 24" className={className} {...stroke}>
    <rect x="3" y="4" width="4" height="16" rx="1" />
    <rect x="10" y="4" width="4" height="16" rx="1" />
    <path d="m17.5 5 3 14-3 .8" />
  </svg>
);
export const RadarIcon = ({ className = base }: P) => (
  <svg viewBox="0 0 24 24" className={className} {...stroke}>
    <circle cx="12" cy="12" r="9" />
    <circle cx="12" cy="12" r="4.5" />
    <path d="M12 12 18 6" />
  </svg>
);
export const UsersIcon = ({ className = base }: P) => (
  <svg viewBox="0 0 24 24" className={className} {...stroke}>
    <circle cx="9" cy="8" r="3.2" />
    <path d="M2.5 20c.8-3.6 3.4-6 6.5-6s5.7 2.4 6.5 6" />
    <path d="M16 5.8a3 3 0 0 1 0 5.6M18.5 20c-.3-1.4-.8-2.7-1.5-3.8" />
  </svg>
);
export const RocketIcon = ({ className = base }: P) => (
  <svg viewBox="0 0 24 24" className={className} {...stroke}>
    <path d="M5 15c-1 3-1 5-1 5s2 0 5-1" />
    <path d="M14 4c3.5-1 5-1 5-1s0 1.5-1 5c-.7 2.5-2.7 5-5.5 7l-3 3-6-6 3-3c2-2.8 4.5-4.8 7-5" />
    <circle cx="15" cy="9" r="1.4" />
  </svg>
);
export const ChartIcon = ({ className = base }: P) => (
  <svg viewBox="0 0 24 24" className={className} {...stroke}>
    <path d="M4 20V6M20 20H4M8 16v-4M12 16V8M16 16v-6" />
  </svg>
);
export const LogoutIcon = ({ className = base }: P) => (
  <svg viewBox="0 0 24 24" className={className} {...stroke}>
    <path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3" />
    <path d="M10 17l-5-5 5-5M5 12h10" />
  </svg>
);
export const LogoMark = ({ className = "h-8 w-8" }: P) => (
  <svg viewBox="0 0 32 32" className={className}>
    <defs>
      <linearGradient id="lg" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stopColor="#5eead4" />
        <stop offset="1" stopColor="#22d3ee" />
      </linearGradient>
    </defs>
    <rect width="32" height="32" rx="9" fill="url(#lg)" />
    <path
      d="M9 22V10h2.6v9.4h4.2V22H9Zm8.6 0V10h2.6v12h-2.6Z"
      fill="#08111f"
      fontWeight="700"
    />
  </svg>
);