import { useEffect, useState } from "react";
import { api, upload } from "./api.js";

const PRESET = [["Career", "💼"], ["Finance", "💰"], ["Education", "🎓"], ["Family", "👨‍👩‍👦"], ["Personal", "❤️"], ["Purchase", "🛍️"], ["Travel", "🚗"], ["Achievement", "🏆"], ["Celebration", "🎉"], ["Idea", "💡"], ["Important", "📌"], ["Other", "📖"]];
const EMOJI = Object.fromEntries(PRESET), NEW = "__new", emoji = c => EMOJI[c] || "🏷️";
const kb = n => n < 1048576 ? `${Math.max(1, Math.round(n / 1024))} KB` : `${(n / 1048576).toFixed(1)} MB`;
const dayOf = s => new Date(s).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" });
const timeOf = s => new Date(s).toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });

export default function Memories() {
  const [rows, setRows] = useState(), [text, setText] = useState(""), [cat, setCat] = useState("Other"), [custom, setCustom] = useState("");
  const [files, setFiles] = useState([]), [fk, setFk] = useState(0), [filter, setFilter] = useState("All"), [busy, setBusy] = useState(false), [err, setErr] = useState("");
  const load = () => api("/memories/").then(setRows); useEffect(() => { load(); }, []);
  if (!rows) return <p className="empty">Loading memories…</p>;
  const used = [...new Set(rows.map(r => r.category))], mine = used.filter(c => !EMOJI[c]);
  const add = async e => { e.preventDefault(); setErr(""); setBusy(true);
    try { const m = await api("/memories/", "POST", { text, category: cat === NEW ? custom : cat }), failed = [];
      for (const f of files) { try { await upload(`/memories/${m.id}/attachments/`, f); } catch (x) { failed.push(`${f.name} (${x.message})`); } }
      setText(""); setCustom(""); setCat("Other"); setFiles([]); setFk(fk + 1); if (failed.length) setErr("Memory saved, but these files were not attached: " + failed.join("; "));
      await load(); } catch (x) { setErr(x.message); } setBusy(false); };
  const del = async r => { if (confirm("Delete this memory and its attachments?")) { await api(`/memories/${r.id}/`, "DELETE"); load(); } };
  const delFile = async (r, a) => { await api(`/memories/${r.id}/attachments/${a.id}/`, "DELETE"); load(); };
  const shown = filter === "All" ? rows : rows.filter(r => r.category === filter), days = [];
  for (const r of shown) { const d = dayOf(r.created_at), last = days[days.length - 1]; last && last.d === d ? last.items.push(r) : days.push({ d, items: [r] }); }
  return <div className="mem"><h1>Memories</h1><p className="sub">Your life timeline. The date and time are saved automatically.</p>
    <form className="card form" onSubmit={add}>
      <label>What happened?<textarea rows="3" required value={text} onChange={e => setText(e.target.value)} placeholder="Share your experience" /></label>
      <span className="fieldlabel">Category</span>
      <div className="catgrid">{PRESET.map(([c, e]) => <button type="button" key={c} className={"catchip" + (cat === c ? " on" : "")} onClick={() => setCat(c)}><span>{e}</span>{c}</button>)}
        {mine.map(c => <button type="button" key={c} className={"catchip" + (cat === c ? " on" : "")} onClick={() => setCat(c)}><span>🏷️</span>{c}</button>)}
        <button type="button" className={"catchip new" + (cat === NEW ? " on" : "")} onClick={() => setCat(NEW)}><span>＋</span>New</button></div>
      {cat === NEW && <label>New category name<input required maxLength="40" value={custom} onChange={e => setCustom(e.target.value)} placeholder="e.g. Health goals" /></label>}
      <label>Attach photos or documents (optional)<input key={fk} type="file" multiple accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.txt" onChange={e => setFiles([...e.target.files])} /></label>
      <p className="sub">Up to 5 files, 10 MB each: photos, PDF, Word, Excel or text.</p>
      {err && <p className="err">{err}</p>}<button disabled={busy}>{busy ? "Saving…" : "Save memory"}</button></form>
    {rows.length === 0 ? <p className="empty">No memories yet. Add your first one above.</p> : <>
      <div className="chips">{["All", ...used].map(c => <button key={c} className={"chip" + (filter === c ? " on" : "")} onClick={() => setFilter(c)}>{c === "All" ? "All" : `${emoji(c)} ${c}`}</button>)}</div>
      {days.map(({ d, items }) => <section className="day" key={d}><h3>{d}</h3><ul className="timeline">{items.map(r => <li key={r.id}><span className="dot" />
        <b>{emoji(r.category)} {r.category}</b><p>{r.text}</p>
        {r.attachments.length > 0 && <div className="files">{r.attachments.map(a => <span className="file" key={a.id}>
          {a.image ? <a href={a.url} target="_blank" rel="noreferrer"><img src={a.url} alt={a.name} loading="lazy" /></a> : <a className="doc" href={a.url} target="_blank" rel="noreferrer">📎 {a.name} · {kb(a.size)}</a>}
          <button className="link" aria-label={`Remove ${a.name}`} onClick={() => delFile(r, a)}>×</button></span>)}</div>}
        <small className="sub">{timeOf(r.created_at)}</small><button className="link" onClick={() => del(r)}>Delete</button></li>)}</ul></section>)}</>}</div>;
}
