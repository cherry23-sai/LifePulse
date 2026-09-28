const BASE = import.meta.env.VITE_API;
export const auth = { get: () => localStorage.getItem("lp_token"), set: t => localStorage.setItem("lp_token", t), clear: () => localStorage.removeItem("lp_token") };
export async function upload(path, file) {
  const fd = new FormData(); fd.append("file", file);
  const r = await fetch(BASE + path, { method: "POST", headers: { Authorization: "Bearer " + auth.get() }, body: fd });
  const data = await r.json().catch(() => null);
  if (!r.ok) throw new Error(data ? Object.values(data).flat().join(" ") : "Upload failed");
  return data;
}
export async function api(path, method = "GET", body) {
  const h = { "Content-Type": "application/json" }; if (auth.get()) h.Authorization = "Bearer " + auth.get();
  const r = await fetch(BASE + path, { method, headers: h, body: body && JSON.stringify(body) });
  if (r.status === 401 && auth.get()) { auth.clear(); location.reload(); }
  const data = r.status === 204 ? null : await r.json().catch(() => null);
  if (!r.ok) throw new Error(data ? Object.values(data).flat().join(" ") : "Request failed");
  return data;
}
