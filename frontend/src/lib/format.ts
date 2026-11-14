export const COLORS = {
  up: "#f59e0b",
  down: "#38bdf8",
  none: "#94a3b8",
  ink: "#e2e8f0",
  muted: "#94a3b8",
  grid: "rgba(148,163,184,0.15)",
};

export function sig(x: number | null | undefined, digits = 3): string {
  if (x === null || x === undefined || !Number.isFinite(x)) return "n/a";
  if (x === 0) return "0";
  const s = Number(x.toPrecision(digits));
  return Math.abs(s) < 1e-4 ? s.toExponential(1) : String(s);
}

export function signed(x: number, digits = 3): string {
  const s = sig(x, digits);
  return x > 0 ? `+${s}` : s.replace("-", "−");
}

export function pval(p: number): string {
  if (p < 0.001) return "< 0.001";
  return p.toFixed(3);
}

/** "p < 0.001" or "p = 0.012" */
export function pEq(p: number): string {
  return p < 0.001 ? "p < 0.001" : `p = ${p.toFixed(3)}`;
}

export function pct(x: number): string {
  return `${Math.round(x * 100)}%`;
}

/** Colour for a trend: direction if both tests pass, grey otherwise. */
export function trendColor(slope: number, significant: boolean): string {
  if (!significant) return COLORS.none;
  return slope > 0 ? COLORS.up : COLORS.down;
}
