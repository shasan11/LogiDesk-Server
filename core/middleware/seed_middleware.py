from __future__ import annotations

import os
import threading
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError
from django.db.utils import OperationalError, ProgrammingError

from master.models import Branch, Currency

# Prevent re-running per request (per process)
_SEEDED = False
_LOCK = threading.Lock()


# A practical currency set (not full ISO 4217 ~180+ codes).
# If you truly want ALL ISO codes, use `pycountry` or import a JSON dataset.
CURRENCY_SEED = [
    # SAARC
    {"code": "NPR", "name": "Nepalese Rupee", "symbol": "रु", "dp": 2, "base": True},
    {"code": "INR", "name": "Indian Rupee", "symbol": "₹", "dp": 2},
    {"code": "BDT", "name": "Bangladeshi Taka", "symbol": "৳", "dp": 2},
    {"code": "PKR", "name": "Pakistani Rupee", "symbol": "₨", "dp": 2},
    {"code": "LKR", "name": "Sri Lankan Rupee", "symbol": "Rs", "dp": 2},
    {"code": "AFN", "name": "Afghan Afghani", "symbol": "؋", "dp": 2},
    {"code": "BTN", "name": "Bhutanese Ngultrum", "symbol": "Nu.", "dp": 2},
    {"code": "MVR", "name": "Maldivian Rufiyaa", "symbol": "Rf", "dp": 2},

    # GCC
    {"code": "AED", "name": "UAE Dirham", "symbol": "د.إ", "dp": 2},
    {"code": "SAR", "name": "Saudi Riyal", "symbol": "﷼", "dp": 2},
    {"code": "QAR", "name": "Qatari Riyal", "symbol": "ر.ق", "dp": 2},
    {"code": "KWD", "name": "Kuwaiti Dinar", "symbol": "د.ك", "dp": 3},
    {"code": "BHD", "name": "Bahraini Dinar", "symbol": "د.ب", "dp": 3},
    {"code": "OMR", "name": "Omani Rial", "symbol": "ر.ع.", "dp": 3},

    # Major
    {"code": "USD", "name": "US Dollar", "symbol": "$", "dp": 2},
    {"code": "EUR", "name": "Euro", "symbol": "€", "dp": 2},
    {"code": "GBP", "name": "British Pound", "symbol": "£", "dp": 2},
    {"code": "JPY", "name": "Japanese Yen", "symbol": "¥", "dp": 0},
    {"code": "CNY", "name": "Chinese Yuan", "symbol": "¥", "dp": 2},
    {"code": "HKD", "name": "Hong Kong Dollar", "symbol": "$", "dp": 2},
    {"code": "SGD", "name": "Singapore Dollar", "symbol": "$", "dp": 2},
    {"code": "AUD", "name": "Australian Dollar", "symbol": "$", "dp": 2},
    {"code": "CAD", "name": "Canadian Dollar", "symbol": "$", "dp": 2},
    {"code": "CHF", "name": "Swiss Franc", "symbol": "Fr", "dp": 2},

    # SEA / nearby
    {"code": "MYR", "name": "Malaysian Ringgit", "symbol": "RM", "dp": 2},
    {"code": "THB", "name": "Thai Baht", "symbol": "฿", "dp": 2},
    {"code": "IDR", "name": "Indonesian Rupiah", "symbol": "Rp", "dp": 2},
    {"code": "VND", "name": "Vietnamese Dong", "symbol": "₫", "dp": 0},
    {"code": "KRW", "name": "South Korean Won", "symbol": "₩", "dp": 0},

    # Others commonly encountered
    {"code": "SEK", "name": "Swedish Krona", "symbol": "kr", "dp": 2},
    {"code": "NOK", "name": "Norwegian Krone", "symbol": "kr", "dp": 2},
    {"code": "DKK", "name": "Danish Krone", "symbol": "kr", "dp": 2},
    {"code": "NZD", "name": "New Zealand Dollar", "symbol": "$", "dp": 2},
    {"code": "ZAR", "name": "South African Rand", "symbol": "R", "dp": 2},
    {"code": "TRY", "name": "Turkish Lira", "symbol": "₺", "dp": 2},
]


def seed_initial_data() -> None:
    """
    Idempotent: safe to call multiple times.
    """
    User = get_user_model()

    # If migrations haven't run yet, tables may not exist.
    # Just skip until DB is ready.
    try:
        with transaction.atomic():
            # ------------------ 1) Main Branch ------------------
            main_branch = Branch.objects.filter(is_main_branch=True).first()

            if not main_branch:
                branch_name = os.getenv("APP_MAIN_BRANCH_NAME", "Main Branch")
                branch_code = os.getenv("APP_MAIN_BRANCH_CODE", "KTM")

                # Prefer existing branch with that code, else create
                existing_by_code = Branch.objects.filter(code=branch_code).first()
                if existing_by_code:
                    # Ensure no other main branch (shouldn't exist due constraint, but be safe)
                    Branch.objects.filter(is_main_branch=True).update(is_main_branch=False)
                    existing_by_code.is_main_branch = True
                    existing_by_code.name = existing_by_code.name or branch_name
                    existing_by_code.save(update_fields=["is_main_branch", "name", "updated"])
                    main_branch = existing_by_code
                else:
                    main_branch = Branch.objects.create(
                        name=branch_name,
                        code=branch_code,
                        is_main_branch=True,
                        phone=os.getenv("APP_MAIN_BRANCH_PHONE", ""),
                        email=os.getenv("APP_MAIN_BRANCH_EMAIL", ""),
                        address=os.getenv("APP_MAIN_BRANCH_ADDRESS", ""),
                    )

            # ------------------ 2) Superuser ------------------
            # Use env vars if provided; fallback is insecure but usable.
            su_email = os.getenv("APP_SUPERUSER_EMAIL", "admin@admin.com")
            su_username = os.getenv("APP_SUPERUSER_USERNAME", "admin")
            su_password = os.getenv("APP_SUPERUSER_PASSWORD", "ChangeMe123!@#")  # CHANGE THIS in production

            superuser = User.objects.filter(is_superuser=True).first()
            if not superuser:
                by_email = User.objects.filter(email=su_email).first()
                if by_email:
                    # Upgrade existing user to superuser
                    by_email.is_staff = True
                    by_email.is_superuser = True
                    if su_password:
                        by_email.set_password(su_password)
                    if hasattr(by_email, "branch"):
                        by_email.branch = main_branch
                    by_email.save()
                    superuser = by_email
                else:
                    superuser = User.objects.create_superuser(
                        username=su_username,
                        email=su_email,
                        password=su_password,
                    )
                    if hasattr(superuser, "branch"):
                        superuser.branch = main_branch
                        superuser.save(update_fields=["branch"])

            # Link branch.user_add if empty
            if getattr(main_branch, "user_add_id", None) is None:
                main_branch.user_add = superuser
                main_branch.save(update_fields=["user_add", "updated"])

            # ------------------ 3) Currencies ------------------
            base_code = os.getenv("APP_BASE_CURRENCY", "NPR").upper().strip()

            # Ensure only one base currency always
            # We'll set base later; first upsert list.
            for c in CURRENCY_SEED:
                code = c["code"].upper().strip()
                is_base = (code == base_code) or bool(c.get("base", False) and base_code == "NPR" and code == "NPR")

                Currency.objects.update_or_create(
                    code=code,
                    defaults={
                        "name": c["name"],
                        "symbol": c.get("symbol", "") or "",
                        "decimal_places": int(c.get("dp", 2)),
                        "is_base": is_base,
                        # rate_to_base: keep default 1 unless you have a live FX source
                        "rate_to_base": Decimal("1"),
                        "active": True,
                        "user_add": superuser if hasattr(Currency, "user_add") else None,
                    },
                )

            # If base currency not in seed list, at least create it
            if not Currency.objects.filter(code=base_code).exists():
                Currency.objects.create(
                    name=base_code,
                    code=base_code,
                    symbol="",
                    decimal_places=2,
                    is_base=True,
                    rate_to_base=Decimal("1"),
                    active=True,
                    user_add=superuser,
                )

            # Enforce single base (just in case)
            Currency.objects.filter(is_base=True).exclude(code=base_code).update(is_base=False)

    except (OperationalError, ProgrammingError):
        # DB tables not ready yet (before migrations). Ignore.
        return
    except IntegrityError:
        # Concurrent create in multi-worker startup; safe to ignore.
        return


class InitialSeederMiddleware:
    """
    Runs seeding once (per process) on the first request.
    Safe with unique constraints + update_or_create.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        global _SEEDED
        if not _SEEDED:
            with _LOCK:
                if not _SEEDED:
                    seed_initial_data()
                    _SEEDED = True
        return self.get_response(request)
