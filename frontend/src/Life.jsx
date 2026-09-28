import { useEffect, useState } from "react";
import { api } from "./api.js";

const iso = d => d.toLocaleDateString("en-CA");
const TODAY = () => iso(new Date()), TOMORROW = () => iso(new Date(Date.now() + 864e5));
const REASONS = [["forgot", "Forgot"], ["no_time", "No time"], ["busy", "Busy"], ["unwell", "Not feeling well"], ["other", "Other"]];
const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const useList = path => { const [rows, setRows] = useState([]); const load = () => api(path).then(setRows); useEffect(() => { load(); }, []); return [rows, load]; };

export function Activity() {
  const blank = { name: "", h: "", m: "", notes: "", date: "" };
  const [rows, load] = useList("/activities/"), [f, setF] = useState(blank), [err, setErr] = useState("");
  const set = k => e => setF({ ...f, [k]: e.target.value });
  const add = async e => { e.preventDefault(); setErr(""); const minutes = (+f.h || 0) * 60 + (+f.m || 0);
    if (minutes < 1) return setErr("Enter the time spent.");
    const b = { name: f.name, minutes, notes: f.notes }; if (f.date) b.date = f.date;
    await api("/activities/", "POST", b); setF(blank); load(); };
  return <><h1>Activity</h1><p className="sub">Record what you did today: phone hours, Rapido driving, study and more.</p>
    <form className="card form" onSubmit={add}>
    <div className="row"><label>Activity<input placeholder="What did you do? e.g. Rapido driving, Study, Phone usage" value={f.name} onChange={set("name")} required /></label>
      <label>Hours<input type="number" min="0" max="24" value={f.h} onChange={set("h")} /></label><label>Minutes<input type="number" min="0" max="59" value={f.m} onChange={set("m")} /></label>
      <label>Date (blank = today)<input type="date" value={f.date} onChange={set("date")} /></label></div>
    <label>Notes<input value={f.notes} onChange={set("notes")} /></label>{err && <p className="err">{err}</p>}<button>Add activity</button></form>
    {rows.length === 0 ? <p className="empty">No activities yet. Log where your time goes today.</p> :
      <ul className="list card">{rows.map(r => <li key={r.id}><span>{r.date} · {r.name}{r.notes && ` — ${r.notes}`}</span><b>{Math.floor(r.minutes / 60)}h {r.minutes % 60}m</b>
        <button className="link" onClick={async () => { await api(`/activities/${r.id}/`, "DELETE"); load(); }}>Delete</button></li>)}</ul>}</>;
}

export function Todos() {
  const [rows, load] = useList("/todos/"), [title, setTitle] = useState(""), [date, setDate] = useState(TOMORROW());
  const patch = async (r, b) => { await api(`/todos/${r.id}/`, "PATCH", b); load(); };
  const t = TODAY();
  const groups = [["Today's review", rows.filter(r => r.plan_date === t)], ["Tomorrow's plan", rows.filter(r => r.plan_date > t)], ["Earlier", rows.filter(r => r.plan_date < t)]];
  return <><form className="card row" onSubmit={async e => { e.preventDefault(); await api("/todos/", "POST", { title, plan_date: date }); setTitle(""); load(); }}>
    <input placeholder="Task" value={title} onChange={e => setTitle(e.target.value)} required />
    <input type="date" value={date} onChange={e => setDate(e.target.value)} title="Defaults to tomorrow" /><button>Add task</button></form>
    {rows.length === 0 && <p className="empty">No tasks yet. Plan tomorrow tonight; tick them off the next day.</p>}
    {groups.map(([label, list]) => list.length > 0 && <section className="card" key={label}><h2>{label}</h2>
      <ul className="list">{list.map(r => <li key={r.id}>
        <input type="checkbox" checked={r.done} onChange={e => patch(r, { done: e.target.checked, skip_reason: "" })} aria-label={`Mark ${r.title} done`} />
        <span>{r.title}{r.plan_date > t && ` · ${r.plan_date}`}</span>
        {!r.done && r.plan_date <= t && <select value={r.skip_reason} onChange={e => patch(r, { skip_reason: e.target.value })}>
          <option value="">Why not done?</option>{REASONS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select>} {!r.done && r.plan_date <= t && r.skip_reason && <input placeholder="More detail (optional)" defaultValue={r.skip_note} onBlur={e => patch(r, { skip_note: e.target.value })} />}
        <button className="link" onClick={async () => { await api(`/todos/${r.id}/`, "DELETE"); load(); }}>Delete</button></li>)}</ul></section>)}</>;
}

export function Habits() {
  const blank = { name: "", frequency: "daily", weekdays: [], interval_hours: "", start_time: "06:00", start_date: TODAY(), end_date: "", end_time: "" };
  const [habits, loadH] = useList("/habits/"), [rows, setRows] = useState([]), [f, setF] = useState(blank), [why, setWhy] = useState({}), [err, setErr] = useState("");
  const loadR = () => api("/habits-today/").then(setRows); useEffect(() => { loadR(); }, []);
  const key = r => r.habit + "|" + r.slot;
  const mark = async (r, done) => { setErr(""); if (!done && !(why[key(r)] || "").trim()) return setErr(`Add a reason for "${r.name}" first.`);
    try { await api("/habits-today/", "POST", { habit: r.habit, slot: r.slot, done, reason: done ? "" : why[key(r)] }); loadR(); } catch (x) { setErr(x.message); } };
  const add = async e => { e.preventDefault(); setErr("");
    const b = { name: f.name, frequency: f.frequency, weekdays: [...f.weekdays].sort().join(","), start_date: f.start_date };
    if (f.frequency === "interval") { b.interval_hours = f.interval_hours; b.start_time = f.start_time || "06:00"; }
    if (f.end_date) { b.end_date = f.end_date; if (f.end_time) b.end_time = f.end_time; }
    try { await api("/habits/", "POST", b); setF(blank); loadH(); loadR(); } catch (x) { setErr(x.message); } };
  const toggleDay = i => setF({ ...f, weekdays: f.weekdays.includes(String(i)) ? f.weekdays.filter(x => x !== String(i)) : [...f.weekdays, String(i)] });
  const describe = h => h.frequency === "daily" ? "Every day" : h.frequency === "interval" ? `Every ${h.interval_hours}h from ${(h.start_time || "06:00").slice(0, 5)}` : h.weekdays.split(",").map(i => DAYS[i]).join(", ");
  return <div className="hab"><h1>Habits</h1>
    <section className="card"><h2>Today</h2>{rows.length === 0 ? <p className="empty">Nothing scheduled today. Add a habit below.</p> : <ul className="list">{rows.map(r => <li key={key(r)}>
      <span>{r.slot && <b>{r.slot} · </b>}{r.name}{r.done === true && <em className="ok"> · done</em>}{r.done === false && <em className="warn"> · not done{r.reason && `: ${r.reason}`}</em>}</span>
      <button onClick={() => mark(r, true)}>Done</button>
      <input placeholder="Reason if not done" value={why[key(r)] || ""} onChange={e => setWhy({ ...why, [key(r)]: e.target.value })} />
      <button className="ghost" onClick={() => mark(r, false)}>Not done</button></li>)}</ul>}{err && <p className="err">{err}</p>}</section>
    <form className="card form" onSubmit={add}><h2>New habit</h2>
      <div className="row"><label>Habit<input placeholder="Meditation, Exercise, Drink water…" value={f.name} onChange={e => setF({ ...f, name: e.target.value })} required /></label>
        <label>Repeats<select value={f.frequency} onChange={e => setF({ ...f, frequency: e.target.value })}><option value="daily">Every day</option><option value="weekly">Specific weekdays</option><option value="interval">Every few hours</option></select></label></div>
      {f.frequency === "weekly" && <div className="chips">{DAYS.map((d, i) => <label key={d} className="chk"><input type="checkbox" checked={f.weekdays.includes(String(i))} onChange={() => toggleDay(i)} /> {d}</label>)}</div>}
      {f.frequency === "interval" && <div className="row"><label>Every (hours)<input type="number" min="1" max="12" required value={f.interval_hours} onChange={e => setF({ ...f, interval_hours: e.target.value })} /></label>
        <label>First reminder at<input type="time" value={f.start_time} onChange={e => setF({ ...f, start_time: e.target.value })} /></label></div>}
      <div className="row"><label>Starts on<input type="date" required value={f.start_date} onChange={e => setF({ ...f, start_date: e.target.value })} /></label>
        <label>Ends on (optional)<input type="date" value={f.end_date} onChange={e => setF({ ...f, end_date: e.target.value })} /></label>
        <label>Ends at (time)<input type="time" value={f.end_time} onChange={e => setF({ ...f, end_time: e.target.value })} disabled={!f.end_date} /></label></div>
      <button disabled={f.frequency === "weekly" && f.weekdays.length === 0}>Add habit</button></form>
    {habits.length > 0 && <section className="card"><h2>All habits</h2><ul className="list">{habits.map(h => <li key={h.id}>
      <span>{h.name} · {describe(h)} · from {h.start_date}{h.end_date && ` until ${h.end_date}${h.end_time ? " " + h.end_time.slice(0, 5) : ""}`}</span>
      <button className="link" onClick={async () => { await api(`/habits/${h.id}/`, "DELETE"); loadH(); loadR(); }}>Delete</button></li>)}</ul></section>}</div>;
}
