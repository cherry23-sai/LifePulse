import { Logo } from "./ui.jsx";
const TRACKERS = [
  ["fin", "💰", "Finance", "Know exactly what you earn, spend and keep.", ["Daily earnings and monthly salary, both supported", "Every spend records why and where", "Savings are calculated for you, plus a place to add money and note where it came from", "Monthly earned, spent and saved at a glance"]],
  ["act", "🏃", "Activity", "See where your day really goes.", ["Hours on the phone, driving, study and more", "Plan tomorrow's to-do list tonight", "Next day, mark each task yes or no and say why", "Compare what you planned with what you did"]],
  ["hab", "🎯", "Habits", "Build routines that follow your schedule.", ["Every day, chosen weekdays, or every few hours", "Set an end date and time", "Mark each one done or not done, with a reason", "See today's completion at a glance"]]];
export default function Landing({ go }) {
  return <div className="lp">
    <header><Logo light /><div className="row"><button className="ghost light" onClick={() => go("login")}>Sign in</button><button onClick={() => go("register")}>Get started</button></div></header>
    <section className="hero"><div><h1>Know where every rupee and every hour goes.</h1>
      <p>LifePulse is a personal finance, activity and habit tracker for people who earn day by day, like part-time drivers, and want a clear path to their monthly goal.</p>
      <div className="row"><button onClick={() => go("register")}>Create your account</button><button className="ghost light" onClick={() => go("login")}>Sign in</button></div></div>
      <svg className="pulse" viewBox="0 0 600 180" aria-hidden="true"><path pathLength="1" d="M0 90h150l25-60 40 120 35-90 25 30h325" /><circle cx="600" cy="90" r="7" /></svg></section>
    <section className="feat">{TRACKERS.map(([c, i, t, d, b]) => <article key={t} className={"card " + c}><h2>{i} {t}</h2><p className="lead">{d}</p><ul>{b.map(x => <li key={x}>{x}</li>)}</ul></article>)}</section>
    <section className="ai"><div><h2>An earnings forecast built on your own numbers</h2>
      <p>Enter your daily earnings, including the last two months if you started recently. LifePulse subtracts petrol and food, then tells you your real average per day, the daily amount you need, and how many days you must drive to reach your monthly target. It runs on your data alone, with no paid AI service.</p></div></section>
    <section className="steps"><h2>How a day works</h2><ol>
      <li><b>Log your day.</b> Earnings, spending, activity hours and habits.</li>
      <li><b>Plan tomorrow tonight.</b> Write the to-do list before you sleep.</li>
      <li><b>Review in the morning.</b> Tick each task yes or no and note why. A nightly email reminds you to update.</li></ol>
      <button onClick={() => go("register")}>Start tracking</button></section>
    <section className="feat"><article className="card mem"><h2>📝 Memories</h2><p className="lead">Keep the moments that matter, such as a new job, a purchase or a gift, on a personal timeline. The date and time are added for you.</p></article></section>
    <footer>© LifePulse · Your data belongs to you. Every account is private.</footer></div>;
}
