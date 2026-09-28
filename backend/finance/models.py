from django.conf import settings
from django.db import models
from django.utils import timezone
class Transaction(models.Model):
    KINDS = [("earning", "Daily earning"), ("salary", "Salary"), ("other_income", "Other income"),
             ("expense", "Expense"), ("saving", "Added savings (external)")]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    kind = models.CharField(max_length=20, choices=KINDS)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.CharField(max_length=60, blank=True)   # Food, Fuel, Rapido...
    note = models.CharField(max_length=200, blank=True)
    why = models.CharField(max_length=200, blank=True)    # why the money was spent
    place = models.CharField(max_length=120, blank=True)  # where it was spent
    date = models.DateField(default=timezone.localdate)      # editable only for historical entries
    created_at = models.DateTimeField(auto_now_add=True)
class MonthlyTarget(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    month = models.DateField()  # first day of month
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    class Meta: unique_together = ("user", "month")
