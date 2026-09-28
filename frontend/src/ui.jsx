export const inr = n => "₹" + Math.round(n || 0).toLocaleString("en-IN");
export const hm = m => `${Math.floor(m / 60)}h ${m % 60}m`;

export const Logo = ({ size = 36, light }) => <span className={"logo" + (light ? " light" : "")}>
  <svg width={size} height={size} viewBox="0 0 48 48" aria-hidden="true"><rect width="48" height="48" rx="13" fill="#164A41" />
    <path d="M6 27h10l4-12 7 22 5-14 3 4h7" fill="none" stroke="#9DC88D" strokeWidth="3.4" strokeLinecap="round" strokeLinejoin="round" />
    <circle cx="42" cy="27" r="3.4" fill="#F1B24A" /></svg><b>LifePulse</b></span>;

export function MonthBars({ months }) {
  const max = Math.max(1, ...months.flatMap(m => [m.income, m.expenses])), h = v => Math.round(110 * v / max);
  return <><svg viewBox="0 0 300 165" className="chart" role="img" aria-label="Earned and spent per month">
    {months.map((m, i) => { const x = 18 + i * 94; return <g key={m.month}>
      <rect x={x} y={118 - h(m.income)} width="34" height={Math.max(2, h(m.income))} rx="5" fill="var(--mint)" />
      <rect x={x + 38} y={118 - h(m.expenses)} width="34" height={Math.max(2, h(m.expenses))} rx="5" fill="var(--coral)" />
      <text x={x + 36} y="135" textAnchor="middle" fontSize="11" fill="var(--mute)">{new Date(m.month + "-01").toLocaleString("en-IN", { month: "short" })}</text>
      <text x={x + 36} y="152" textAnchor="middle" fontSize="11" fontWeight="700" fill={m.saved < 0 ? "var(--coral)" : "var(--ink)"}>Saved {inr(m.saved)}</text></g>; })}</svg>
    <p className="legend"><i style={{ background: "var(--mint)" }} /> Earned <i style={{ background: "var(--coral)" }} /> Spent</p></>;
}

export function DayBars({ days }) {
  const max = Math.max(1, ...days.map(d => d.amount));
  return <svg viewBox="0 0 300 90" className="chart" role="img" aria-label="Earnings for the last 14 days">
    {days.map((d, i) => { const h = Math.max(3, Math.round(72 * d.amount / max)); return <rect key={d.date} x={4 + i * 20.5} y={80 - h} width="14" height={h} rx="4" fill="var(--mint)" opacity={d.amount ? 1 : .25}><title>{d.date}: {inr(d.amount)}</title></rect>; })}</svg>;
}

export const Ring = ({ pct, color }) => { const r = 30, c = 2 * Math.PI * r;
  return <svg width="80" height="80" viewBox="0 0 76 76" role="img" aria-label={`${pct}% of today's habits done`}>
    <circle cx="38" cy="38" r={r} fill="none" stroke="var(--line)" strokeWidth="8" />
    <circle cx="38" cy="38" r={r} fill="none" stroke={color} strokeWidth="8" strokeLinecap="round" strokeDasharray={`${c * pct / 100} ${c}`} transform="rotate(-90 38 38)" />
    <text x="38" y="43" textAnchor="middle" fontWeight="700" fontSize="16" fill="var(--ink)">{pct}%</text></svg>; };
