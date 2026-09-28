import calendar, math
from datetime import timedelta
from django.db.models import Sum, Q
from django.utils import timezone
from .models import Transaction, MonthlyTarget
INCOME = ["earning", "salary", "other_income"]
WORK_COST = Q(category__iexact="fuel") | Q(category__iexact="food")   # fuel + food are taken off earnings in the forecast
def _sum(qs): return float(qs.aggregate(s=Sum("amount"))["s"] or 0)
def _work(qs): return _sum(qs.filter(kind="expense").filter(WORK_COST))
def totals(user):
    t = Transaction.objects.filter(user=user)
    income, expenses, added = _sum(t.filter(kind__in=INCOME)), _sum(t.filter(kind="expense")), _sum(t.filter(kind="saving"))
    return {"income": income, "expenses": expenses, "external_savings": added, "current_savings": income - expenses + added}
def _per_day(qs):
    per = {}
    for d, a in qs.values_list("date", "amount"): per[d] = per.get(d, 0) + float(a)
    return per
def forecast(user):
    today = timezone.localdate(); first = today.replace(day=1); t = Transaction.objects.filter(user=user)
    left = calendar.monthrange(today.year, today.month)[1] - today.day + 1
    recent = t.filter(date__gte=today - timedelta(days=60), date__lte=today); earn = recent.filter(kind="earning")
    per = _per_day(earn); days = len(per)
    avg_gross = sum(per.values()) / days if days else 0; avg_cost = _work(recent) / days if days else 0; avg_net = avg_gross - avg_cost
    mt = MonthlyTarget.objects.filter(user=user, month=first).first(); target = float(mt.amount) if mt else 0
    month = t.filter(date__gte=first)
    earned = _sum(month.filter(kind__in=INCOME)) - _work(month)
    remaining = max(target - earned, 0); req = remaining / left
    buckets = {}
    for d, a in per.items(): buckets.setdefault(d.weekday(), []).append(a)
    rates = sorted({max(50, round(avg_net * f / 50) * 50) for f in (0.75, 1, 1.25, 1.5)}) if avg_net > 0 else [500, 600, 700, 800]
    return {"target": target, "earned_net": earned, "remaining": remaining, "days_left": left, "target_reached": bool(target) and remaining == 0,
        "avg_gross": round(avg_gross), "avg_expense": round(avg_cost), "avg_net": round(avg_net), "required_per_day": round(req),
        "days_required": math.ceil(remaining / avg_net) if avg_net > 0 else None, "on_track": bool(target) and avg_net >= req,
        "by_weekday": {str(k): round(sum(v) / len(v)) for k, v in buckets.items()},
        "scenarios": [{"per_day": r, "projected_month_end": round(earned + r * left)} for r in rates], "has_data": days > 0}
def extras(user):
    today = timezone.localdate(); first = today.replace(day=1); t = Transaction.objects.filter(user=user); months = []
    for i in (2, 1, 0):
        y, m = today.year, today.month - i
        if m < 1: m += 12; y -= 1
        q = t.filter(date__year=y, date__month=m); inc, exp = _sum(q.filter(kind__in=INCOME)), _sum(q.filter(kind="expense"))
        months.append({"month": f"{y}-{m:02d}", "income": inc, "expenses": exp, "saved": inc - exp})
    cats = [{"category": c["category"], "total": float(c["s"])} for c in t.filter(kind="expense", date__gte=first).values("category").annotate(s=Sum("amount")).order_by("-s")]
    per = _per_day(t.filter(kind="earning", date__gte=today - timedelta(days=13)))
    daily = [{"date": str(today - timedelta(days=i)), "amount": per.get(today - timedelta(days=i), 0)} for i in range(13, -1, -1)]
    return {"months": months, "categories": cats, "daily": daily}
