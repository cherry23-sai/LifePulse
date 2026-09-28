import { useEffect, useState } from "react";
import { api, auth } from "./api.js";
import { Activity, Todos, Habits } from "./Life.jsx";
import Finance from "./Finance.jsx";
import Landing from "./Landing.jsx";
import Memories from "./Memories.jsx";
import { Logo, MonthBars, DayBars, Ring, inr, hm } from "./ui.jsx";
const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

function OtpForm({ title, sub, digits = 6, onSubmit, resend, extra, busy, err }) {
  const [code, setCode] = useState(""), [sent, setSent] = useState("A code is on its way.");
  return <form className="authform" onSubmit={e => { e.preventDefault(); onSubmit(code); }}>
    <h1>{title}</h1><p className="sub">{sub}</p>
    <label>6-digit code<input inputMode="numeric" pattern="\d{6}" maxLength={digits} autoFocus value={code}
      onChange={e => setCode(e.target.value.replace(/\D/g, ""))} required /></label>
    {extra}{err && <p className="err">{err}</p>}
    <button disabled={busy || code.length !== 6}>{busy ? "Checking…" : "Verify"}</button>
    {resend && <button type="button" className="link" onClick={async () => { await resend(); setSent("A new code is on its way."); }}>{sent} Resend code</button>}
  </form>;
}

function Auth({ mode, setMode, onDone, back }) {
  const reg = mode === "register", forgot = mode === "forgot";
  const [f, setF] = useState({ name: "", email: "", password: "" }), [err, setErr] = useState(""), [busy, setBusy] = useState(false);
  const [stage, setStage] = useState("form"), [newPw, setNewPw] = useState("");
  const set = k => e => setF({ ...f, [k]: e.target.value });
  const login = async () => { const t = await api("/auth/login/", "POST", { username: f.email.trim().toLowerCase(), password: f.password });
    auth.set(t.access); localStorage.setItem("lp_name", t.name || f.name); onDone(); };
  const start = async e => { e.preventDefault(); setErr(""); setBusy(true);
    try {
      if (forgot) { await api("/auth/forgot-password/", "POST", { email: f.email.trim().toLowerCase() }); setStage("otp"); }
      else if (reg) { await api("/auth/register/", "POST", { first_name: f.name, email: f.email, password: f.password }); setStage("otp"); }
      else await login();
    } catch (x) { setErr(x.message); } setBusy(false); };
  const verify = async code => { setErr(""); setBusy(true);
    try { const t = await api("/auth/verify-email/", "POST", { email: f.email.trim().toLowerCase(), code });
      auth.set(t.access); localStorage.setItem("lp_name", t.name || f.name); onDone(); } catch (x) { setErr(x.message); } setBusy(false); };
  const resetWithCode = async code => { setErr(""); setBusy(true);
    try { if (!newPw || newPw.length < 8) throw new Error("Choose a password with at least 8 characters.");
      const t = await api("/auth/reset-password/", "POST", { email: f.email.trim().toLowerCase(), code, password: newPw });
      auth.set(t.access); localStorage.setItem("lp_name", t.name || f.name); onDone(); } catch (x) { setErr(x.message); } setBusy(false); };
  const resend = () => api("/auth/resend-code/", "POST", { email: f.email.trim().toLowerCase() });

  let panel;
  if (stage === "otp" && reg) panel = <OtpForm title="Check your email" sub={`We sent a 6-digit code to ${f.email}. Enter it to verify your account.`}
    onSubmit={verify} resend={resend} busy={busy} err={err} />;
  else if (stage === "otp" && forgot) panel = <OtpForm title="Reset your password" sub={`Enter the code sent to ${f.email}, and choose a new password.`}
    onSubmit={resetWithCode} resend={resend} busy={busy} err={err}
    extra={<label>New password<input type="password" minLength={8} value={newPw} onChange={e => setNewPw(e.target.value)} required /></label>} />;
  else panel = <form className="authform" onSubmit={start}>
    <h1>{forgot ? "Forgot password" : reg ? "Create your account" : "Welcome back"}</h1>
    {forgot && <p className="sub">We'll email you a 6-digit code to reset your password.</p>}
    {reg && <label>Your name<input value={f.name} onChange={set("name")} required /></label>}
    <label>Email<input type="email" value={f.email} onChange={set("email")} required /></label>
    {!forgot && <label>Password<input type="password" minLength={8} value={f.password} onChange={set("password")} required /></label>}
    {!forgot && !reg && <button type="button" className="link right" onClick={() => setMode("forgot")}>Forgot password?</button>}
    {err && <p className="err">{err}</p>}
    <button disabled={busy}>{busy ? "Please wait…" : forgot ? "Send code" : reg ? "Create account" : "Sign in"}</button>
    {!forgot && <button type="button" className="link" onClick={() => setMode(reg ? "login" : "register")}>{reg ? "Already registered? Sign in" : "New here? Create an account"}</button>}
    {forgot && <button type="button" className="link" onClick={() => setMode("login")}>Back to sign in</button>}
  </form>;

  return <div className="authwrap"><aside><Logo light /><h2>Your money, time and habits in one place.</h2><p>Every account is private. Only you can see your data.</p></aside>
    {panel}
    <button type="button" className="link home" onClick={back}>Back to home</button></div>;
}

function ForecastBlock({ fc, go }) {
  if (!fc.has_data) return <div className="card"><h3>AI earnings forecast</h3><p className="empty">Add your daily earnings, including the last two months, and your forecast appears here.</p><button onClick={() => go("Finance")}>Add earnings</button></div>;
  if (!fc.target) return <div className="card"><h3>AI earnings forecast</h3><p>After petrol and food you earn about <b>{inr(fc.avg_net)}</b> on a day you drive. Set a monthly target to see the daily amount and days you need.</p><button onClick={() => go("Forecast")}>Set target</button></div>;
  const pct = Math.min(100, Math.round(100 * fc.earned_net / fc.target)), ok = fc.days_required != null && fc.days_required <= fc.days_left;
  return <div className="card"><h3>AI earnings forecast</h3><div className="bar"><i style={{ width: pct + "%" }} /></div>
    <p className="sub">{inr(fc.earned_net)} of {inr(fc.target)} earned after petrol and food · {inr(fc.remaining)} to go</p>
    <div className="grid"><div className="tile"><small>Your average per day</small><b>{inr(fc.avg_net)}</b><span>after petrol and food</span></div>
      <div className="tile"><small>Daily target needed</small><b>{inr(fc.required_per_day)}</b><span>over {fc.days_left} days left</span></div>
      <div className="tile"><small>Days you need to drive</small><b>{fc.days_required ?? "–"}</b><span>at your average</span></div></div>
    <p className={fc.target_reached || ok ? "ok" : "warn"}>{fc.target_reached ? "You have reached this month's target." : ok ? `At your average, driving ${fc.days_required} of the next ${fc.days_left} days reaches your target.` : fc.days_required == null ? "Your average after petrol and food is not above zero yet, so a forecast is not possible." : `At your average you need ${fc.days_required} driving days but only ${fc.days_left} days are left. Aim for ${inr(fc.required_per_day)} a day.`}</p></div>;
}

function Forecast({ go }) {
  const [s, setS] = useState(), [amt, setAmt] = useState(""), [k, setK] = useState(0);
  useEffect(() => { api("/finance/summary/").then(setS); }, [k]); if (!s) return null; const fc = s.forecast;
  return <div className="fin"><h1>AI Forecast</h1><p className="sub">Worked out from your own earnings over the last 60 days, with petrol and food taken off. No data leaves your account.</p>
    <form className="card row" onSubmit={async e => { e.preventDefault(); await api("/finance/target/", "PUT", { amount: amt }); setAmt(""); setK(k + 1); }}>
      <label>Monthly target (₹), now {inr(fc.target)}<input type="number" min="1" value={amt} onChange={e => setAmt(e.target.value)} required /></label><button>Save target</button></form>
    <ForecastBlock fc={fc} go={go} />
    {fc.has_data && <div className="two"><div className="card"><h3>If you earn this much a day</h3><ul className="plain">{fc.scenarios.map(x => <li key={x.per_day}><span>{inr(x.per_day)} a day</span><b>{inr(x.projected_month_end)} by month end</b></li>)}</ul><p className="sub">Assumes you drive every remaining day this month.</p></div>
      <div className="card"><h3>Your average by weekday</h3><ul className="plain">{Object.entries(fc.by_weekday).sort().map(([d, v]) => <li key={d}><span>{DAYS[d]}</span><b>{inr(v)}</b></li>)}</ul></div></div>}</div>;
}

function Dashboard({ go }) {
  const [s, setS] = useState(), [t, setT] = useState(); useEffect(() => { api("/finance/summary/").then(setS); api("/today/").then(setT); }, []);
  if (!s || !t) return <p className="empty">Loading your dashboard…</p>;
  const cur = s.months[2], hr = new Date().getHours(), name = localStorage.getItem("lp_name"), total = t.activities.reduce((a, x) => a + x.minutes, 0);
  return <><h1>{hr < 12 ? "Good morning" : hr < 18 ? "Good afternoon" : "Good evening"}{name && `, ${name}`}</h1>
    <p className="sub">{new Date().toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long" })}</p>
    <section className="fin"><h2>Finance</h2><div className="grid">
      <div className="tile big"><small>Total savings</small><b>{inr(s.current_savings)}</b><span>Earned − spent + money you added</span></div>
      <div className="tile"><small>Earned this month</small><b>{inr(cur.income)}</b></div><div className="tile"><small>Spent this month</small><b className="neg">{inr(cur.expenses)}</b></div>
      <div className="tile"><small>Saved this month</small><b>{inr(cur.saved)}</b></div></div>
      <div className="two"><div className="card"><h3>Last 3 months</h3><MonthBars months={s.months} /></div>
        <div className="card"><h3>Earnings, last 14 days</h3><DayBars days={s.daily} /><h3 className="gap">Spent this month</h3>
          {s.categories.length ? <ul className="plain">{s.categories.map(c => <li key={c.category}><span>{c.category || "Other"}</span><b>{inr(c.total)}</b></li>)}</ul> : <p className="empty">No spending logged this month.</p>}</div></div>
      <ForecastBlock fc={s.forecast} go={go} /></section>
    <section className="act"><h2>Activity</h2><div className="grid">
      <div className="tile"><small>Logged today</small><b>{hm(total)}</b><span>{t.activities.length} activities</span></div>
      {t.activities.slice(0, 3).map(a => <div className="tile" key={a.name}><small>{a.name}</small><b>{hm(a.minutes)}</b></div>)}
      <div className="tile"><small>Today's to-dos</small><b>{t.todos_total ? `${t.todos_done}/${t.todos_total}` : "–"}</b><span>{t.todos_total ? "tasks done" : "Plan tomorrow tonight"}</span></div></div>
      {t.activities.length === 0 && <p className="empty">Nothing logged today. <button className="link" onClick={() => go("Activity")}>Log an activity</button></p>}</section>
    <section className="hab"><h2>Habits</h2><div className="card row"><Ring pct={t.habits_pct} color="var(--amber)" /><div>
      <b>{t.habits_total ? `${t.habits_done} of ${t.habits_total} done today` : "No habits scheduled today"}</b><p className="sub">{t.habits_total ? "Mark the rest before the day ends." : "Create a habit to start your streak."}</p>
      <button className="ghost" onClick={() => go("Habits")}>Open habits</button></div></div></section>
    <section className="mem"><h2>Memories</h2><div className="tile"><small>Moments saved</small><b>{t.memories}</b><button className="link" onClick={() => go("Memories")}>Add a memory</button></div></section></>;
}

const NAV = [["Dashboard", "🏠"], ["Finance", "💰"], ["Forecast", "🤖"], ["Activity", "🏃"], ["Todos", "✅"], ["Habits", "🎯"], ["Memories", "📝"]];
export default function App() {
  const [authed, setAuthed] = useState(!!auth.get()), [view, setView] = useState("landing"), [tab, setTab] = useState("Dashboard");
  if (!authed) return view === "landing" ? <Landing go={setView} /> : <Auth mode={view} setMode={setView} onDone={() => setAuthed(true)} back={() => setView("landing")} />;
  return <div className="shell"><nav className="side"><Logo light />{NAV.map(([n, i]) => <button key={n} className={n === tab ? "on" : ""} onClick={() => setTab(n)}><span>{i}</span>{n}</button>)}
    <button className="out" onClick={() => { auth.clear(); setAuthed(false); setView("landing"); }}>Sign out</button></nav>
    <main>{tab === "Dashboard" && <Dashboard go={setTab} />}{tab === "Finance" && <Finance />}{tab === "Forecast" && <Forecast go={setTab} />}{tab === "Activity" && <Activity />}
      {tab === "Todos" && <div className="act"><h1>Todos</h1><p className="sub">Plan tomorrow tonight. Tomorrow, tick what you finished and say why for anything you did not.</p><Todos /></div>}{tab === "Habits" && <Habits />}{tab === "Memories" && <Memories />}</main></div>;
}
