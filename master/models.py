from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q


class Branch(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)  # e.g. "KTM", "BRT"
    is_main_branch = models.BooleanField(default=False)

    phone = models.CharField(max_length=30, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    address = models.CharField(max_length=255, blank=True, default="")
    user_add = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        editable=False,
        related_name="settings_branch_user_add",
    )

    active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["is_main_branch"],     # <-- required field
                condition=Q(is_main_branch=True),
                name="unique_main_branch",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Currency(models.Model):
    name = models.CharField(max_length=60)              # e.g. "Nepalese Rupee"
    code = models.CharField(max_length=3, unique=True)  # e.g. "NPR", "USD"
    symbol = models.CharField(max_length=10, blank=True, default="")  # e.g. "₨", "$"
    decimal_places = models.PositiveSmallIntegerField(
        default=2,
        validators=[MinValueValidator(0), MaxValueValidator(6)]
    )

    is_base = models.BooleanField(default=False)
    rate_to_base = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=1,
        validators=[MinValueValidator(0)]
    )

    user_add = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        editable=False,
        related_name="settings_currency_user_add",
    )

    active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]
        constraints = [
            models.UniqueConstraint(
                fields=["is_base"],
                condition=Q(is_base=True),
                name="unique_base_currency",
            )
        ]

    def __str__(self):
        return f"{self.code} ({self.symbol})" if self.symbol else self.code
