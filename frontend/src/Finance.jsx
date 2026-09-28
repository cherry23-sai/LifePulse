import { useEffect, useState } from "react";
import { api } from "./api.js";
import { inr, MonthBars } from "./ui.jsx";
const iso = d => d.toLocaleDateString("en-CA"), TODAY = () => iso(new Date());
const CATS = [["Food", "🍔"], ["Fuel", "⛽"], ["Travel", "🚌"], ["Shopping", "🛍️"], ["Bills", "🧾"], ["Entertainment", "🎬"], ["Education", "📚"], ["Health", "💊"], ["Family", "👨‍👩‍👦"], ["Subscriptions", "🔁"], ["Custom", "🏷️"]];
const ICON = Object.fromEntries(CATS), icon = c => ICON[c] || "🏷️";
const SOURCES = ["Rapido", "Other"];

function EarnCard() {
  const [amount, setAmount] = useState(""), [source, setSource] = useState("Rapido"), [date, setDate] = useState(TODAY()), [msg, setMsg] = useState(""), [err, setErr] = useState(""), [busy, setBusy] = useState(false);
  const add = async e => { e.preventDefault(); setErr(""); setMsg(""); setBusy(true);
    try { await api("/finance/transactions/", "POST", { kind: "earning", amount, category: source, date }); setAmount(""); setMsg("Earning added."); }
    catch (x) { setErr(x.message); } setBusy(false); };
  return <form className="panel earn" onSubmit={add}><h2>💵 Earned today</h2>
    <label>Amount (₹)<input type="number" min="0.01" step="0.01" required value={amount} onChange={e => setAmount(e.target.value)} placeholder="0" /></label>
    <div className="row"><label>Source<select value={source} onChange={e => setSource(e.target.value)}>{SOURCES.map(s => <option key={s}>{s}</option>)}</select></label>
      <label>Date<input type="date" required value={date} onChange={e => setDate(e.target.value)} /></label></div>
    {err && <p className="err">{err}</p>}{msg && <p className="ok">{msg}</p>}<button>Add earning</button></form>;
}

function SpendCard() {
  const [amount, setAmount] = useState(""), [cat, setCat] = useState("Food"), [custom, setCustom] = useState(""), [why, setWhy] = useState(""), [place, setPlace] = useState("");
  const [date, setDate] = useState(TODAY()), [msg, setMsg] = useState(""), [err, setErr] = useState(""), [busy, setBusy] = useState(false);
  const add = async e => { e.preventDefault(); setErr(""); setMsg(""); setBusy(true);
    try { await api("/finance/transactions/", "POST", { kind: "expense", amount, category: cat === "Custom" ? (custom || "Custom") : cat, why, place, date });
      setAmount(""); setWhy(""); setPlace(""); setCustom(""); setMsg("Expense added."); } catch (x) { setErr(x.message); } setBusy(false); };
  return <form className="panel spend" onSubmit={add}><h2>🧾 Spent today</h2>
    <label>Amount (₹)<input type="number" min="0.01" step="0.01" required value={amount} onChange={e => setAmount(e.target.value)} placeholder="0" /></label>
    <div className="catgrid">{CATS.map(([c, e]) => <button type="button" key={c} className={"catchip" + (cat === c ? " on" : "")} onClick={() => setCat(c)}><span>{e}</span>{c}</button>)}</div>
    {cat === "Custom" && <label>Custom category<input required maxLength="40" value={custom} onChange={e => setCustom(e.target.value)} placeholder="e.g. Vehicle repair" /></label>}
    <div className="row"><label>Why?<input required value={why} onChange={e => setWhy(e.target.value)} placeholder="e.g. Fuel for shifts" /></label>
      <label>Where?<input required value={place} onChange={e => setPlace(e.target.value)} placeholder="e.g. Petrol bunk" /></label></div>
    <label>Date<input type="date" required value={date} onChange={e => setDate(e.target.value)} /></label>
    {err && <p className="err">{err}</p>}{msg && <p className="ok">{msg}</p>}<button>Add expense</button></form>;
}

function More({ done }) {
  const [open, setOpen] = useState(false), [kind, setKind] = useState("salary"), [amount, setAmount] = useState(""), [note, setNote] = useState(""), [date, setDate] = useState(TODAY()), [err, setErr] = useState("");
  const L = { salary: "Monthly salary", other_income: "Other income", saving: "Add to savings" };
  const submit = async e => { e.preventDefault(); setErr("");
    try { const b = { kind, amount, date }; if (kind === "saving") b.note = note; else b.category = note || L[kind];
      await api("/finance/transactions/", "POST", b); setAmount(""); setNote(""); done(); setOpen(false); } catch (x) { setErr(x.message); } };
  return <div className="more">{!open ? <div className="chips">{Object.entries(L).map(([k, l]) => <button type="button" key={k} className="chip ghostchip" onClick={() => { setKind(k); setOpen(true); }}>+ {l}</button>)}</div> :
    <form className="card form" onSubmit={submit}><h3>{L[kind]}</h3>
      <div className="row"><label>Amount (₹)<input type="number" min="0.01" step="0.01" required value={amount} onChange={e => setAmount(e.target.value)} /></label>
        <label>Date<input type="date" required value={date} onChange={e => setDate(e.target.value)} /></label></div>
      <label>{kind === "saving" ? "How did this money come to you?" : "Note (optional)"}<input required={kind === "saving"} value={note} onChange={e => setNote(e.target.value)} /></label>
      {err && <p className="err">{err}</p>}<div className="row"><button>Save</button><button type="button" className="ghost" onClick={() => setOpen(false)}>Cancel</button></div></form>}</div>;
}

function CatBars({ categories }) {
  const max = Math.max(1, ...categories.map(c => c.total));
  return categories.length === 0 ? <p className="empty">No spending logged this month.</p> : <ul className="catbars">
    {categories.map(c => <li key={c.category}><span className="cl">{icon(c.category)} {c.category}</span>
      <span className="track"><i style={{ width: Math.round(100 * c.total / max) + "%" }} /></span><b>{inr(c.total)}</b></li>)}</ul>;
}

// function Past({ done }) {
//   const [start, setStart] = useState(iso(new Date(Date.now() - 60 * 864e5))), [have, setHave] = useState(), [amt, setAmt] = useState({}), [busy, setBusy] = useState(false), [err, setErr] = useState("");
//   useEffect(() => { api("/finance/transactions/?kind=earning").then(r => setHave(new Set(r.map(x => x.date)))); }, []);
//   if (!have) return null;
//   const days = []; for (let d = new Date(start + "T00:00"); iso(d) < TODAY(); d.setDate(d.getDate() + 1)) if (!have.has(iso(d))) days.push(iso(d));
//   const g = (d, k) => +amt[d + "|" + k] || 0, put = (d, k) => e => setAmt({ ...amt, [d + "|" + k]: e.target.value });
//   const save = async () => { setBusy(true); setErr(""); const reqs = [];
//     for (const d of days) { if (g(d, "earn") > 0) reqs.push({ kind: "earning", amount: g(d, "earn"), category: "Rapido", date: d });
//       for (const c of ["Fuel", "Food"]) if (g(d, c) > 0) reqs.push({ kind: "expense", amount: g(d, c), category: c, why: c + " for Rapido shifts", place: "Past entry", date: d }); }
//     try { await Promise.all(reqs.map(b => api("/finance/transactions/", "POST", b))); setAmt({}); done(); } catch (x) { setErr(x.message); } setBusy(false); };
//   return <div className="card"><h3>Past daily earnings</h3><p className="sub">Enter what you earned since you started driving, with fuel and food, for an accurate forecast. Leave days off blank.</p>
//     <label>Started driving on<input type="date" value={start} max={TODAY()} onChange={e => setStart(e.target.value)} /></label>
//     {days.length === 0 ? <p className="empty">No days left to fill in for this range.</p> : <ul className="list past">{days.map(d => <li key={d}>
//       <span>{new Date(d + "T00:00").toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short" })}</span>
//       {[["earn", "Earned"], ["Fuel", "Fuel"], ["Food", "Food"]].map(([k, l]) => <input key={k} type="number" min="0" step="0.01" placeholder={l} aria-label={`${l} on ${d}`} value={amt[d + "|" + k] || ""} onChange={put(d, k)} />)}</li>)}</ul>}
//     {err && <p className="err">{err}</p>}<button disabled={busy || days.length === 0} onClick={save}>{busy ? "Saving…" : "Save all entries"}</button></div>;
// }

function History() {
  const [rows, setRows] = useState(); const load = () => api("/finance/transactions/").then(setRows); useEffect(() => { load(); }, []);
  if (!rows) return null;
  if (rows.length === 0) return <p className="empty">No entries yet. Add your first one under Today.</p>;
  const days = []; for (const r of rows) { const last = days[days.length - 1]; last && last.date === r.date ? last.items.push(r) : days.push({ date: r.date, items: [r] }); }
  return <ul className="timeline money">{days.map(({ date, items }) => { const net = items.reduce((a, r) => a + (r.kind === "expense" ? -r.amount : +r.amount), 0);
    return <li key={date}><span className="dot" /><div className="dayhead"><b>{new Date(date + "T00:00").toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short" })}</b>
      <b className={net >= 0 ? "ok" : "neg"}>{net >= 0 ? "+" : ""}{inr(net)}</b></div>
      <ul className="plain">{items.map(r => { const out = r.kind === "expense";
        return <li key={r.id}><span>{r.kind === "expense" ? icon(r.category) : r.kind === "saving" ? "🏦" : "💵"} {r.kind === "expense" ? r.category : r.kind === "salary" ? "Monthly salary" : r.kind === "other_income" ? "Other income" : r.kind === "saving" ? "Added to savings" : r.category}
          {(r.why || r.place) && <small className="sub"> · {[r.why, r.place].filter(Boolean).join(" at ")}</small>}{r.note && <small className="sub"> · {r.note}</small>}</span>
          <b className={out ? "neg" : "ok"}>{out ? "−" : "+"}{inr(r.amount)}</b>
          <button className="link" onClick={async () => { await api(`/finance/transactions/${r.id}/`, "DELETE"); load(); }}>Delete</button></li>; })}</ul></li>; })}</ul>;
}

export default function Finance() {
  const [tab, setTab] = useState("Today"), [k, setK] = useState(0), [s, setS] = useState();
  useEffect(() => { api("/finance/summary/").then(setS); }, [k]);
  const bump = () => setK(k + 1);
  return <div className="fin"><h1>Finance</h1><div className="chips">{["Today", "History"].map(t => <button key={t} className={"chip" + (tab === t ? " on" : "")} onClick={() => setTab(t)}>{t}</button>)}</div>
    {tab === "Today" && <>
      {s && <div className="grid save">
        <div className="tile big"><small>Total savings</small><b>{inr(s.current_savings)}</b><span>Earned − spent + added</span></div>
        <div className="tile"><small>Earned this month</small><b>{inr(s.months[2].income)}</b></div>
        <div className="tile"><small>Spent this month</small><b className="neg">{inr(s.months[2].expenses)}</b></div>
        <div className="tile"><small>Saved this month</small><b>{inr(s.months[2].saved)}</b></div></div>}
      <div className="two"><EarnCard bump={bump} /><SpendCard bump={bump} /></div>
      <More done={bump} />
      {s && <div className="two"><div className="card"><h3>Last 3 months</h3><MonthBars months={s.months} /></div>
        <div className="card"><h3>Spending by category, this month</h3><CatBars categories={s.categories} /></div></div>}
    </>}
    {tab === "Past earnings" && <Past key={k} done={bump} />}
    {tab === "History" && <History key={k} />}
  </div>;
}
