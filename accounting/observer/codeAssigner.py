from __future__ import annotations

import re
from typing import Tuple
from django.db import transaction

_NUM_RE = re.compile(r"(\d+)$")


def _is_int_str(v: str) -> bool:
    try:
        int(str(v))
        return True
    except Exception:
        return False


def _get_next_prefixed_code(model_cls, *, branch_id, prefix: str, width: int = 5, field: str = "code") -> str:
    """
    Concurrency-safe next code for strings like BA00001 / BC00001.
    """
    with transaction.atomic():
        qs = (
            model_cls.objects.select_for_update()
            .filter(branch_id=branch_id, **{f"{field}__startswith": prefix})
            .exclude(**{field: None})
            .exclude(**{field: ""})
            .order_by(f"-{field}")
        )
        last = qs.first()
        n = 1
        if last:
            last_code = getattr(last, field, "") or ""
            m = _NUM_RE.search(last_code)
            if m:
                try:
                    n = int(m.group(1)) + 1
                except Exception:
                    n = 1
        return f"{prefix}{str(n).zfill(width)}"


def assign_bank_account_code(instance) -> None:
    """
    BankAccount.code:
      BANK -> BA00001...
      CASH -> BC00001...
    """
    if getattr(instance, "code", None):
        return

    branch_id = getattr(instance, "branch_id", None)
    if not branch_id:
        return

    t = (getattr(instance, "type", "") or "").lower().strip()
    prefix = "BA" if t == "bank" else "BC" if t == "cash" else "BA"
    instance.code = _get_next_prefixed_code(instance.__class__, branch_id=branch_id, prefix=prefix, width=5, field="code")


# ----------------------- COA code assignment (1000-7999) -----------------------

def _coa_range_for(instance) -> Tuple[int, int]:
    """
    1000-1999 Assets
    2000-2999 Liabilities
    3000-3999 Equity
    4000-4999 Revenue (income)
    5000-5999 COGS (detected when expense + cogs keyword or parent in 5000s)
    6000-7999 Expenses
    """
    cat = (getattr(instance, "account_type", None) or "asset").lower().strip()
    name = (getattr(instance, "name", "") or "").lower()

    parent = getattr(instance, "parent", None)
    parent_code = getattr(parent, "code", None)

    if cat == "expense":
        is_cogs = ("cogs" in name) or ("cost of goods" in name)
        if parent_code and _is_int_str(parent_code):
            p = int(parent_code)
            if 5000 <= p <= 5999:
                is_cogs = True
        return (5000, 5999) if is_cogs else (6000, 7999)

    if cat == "asset":
        return (1000, 1999)
    if cat == "liability":
        return (2000, 2999)
    if cat == "equity":
        return (3000, 3999)
    if cat == "income":
        return (4000, 4999)

    return (1000, 1999)


def _next_coa_code_in_range(model_cls, *, branch_id, start: int, end: int, first: int, step: int) -> str:
    start_s = f"{start:04d}"
    end_s = f"{end:04d}"

    with transaction.atomic():
        qs = (
            model_cls.objects.select_for_update()
            .filter(branch_id=branch_id)
            .exclude(code__isnull=True)
            .exclude(code="")
            .filter(code__gte=start_s, code__lte=end_s)
        )
        existing = set(qs.values_list("code", flat=True))

        for n in range(first, end + 1, step):
            c = f"{n:04d}"
            if c not in existing:
                return c

    raise ValueError(f"No available COA code in range {start}-{end}.")


def assign_coa_code(instance) -> None:
    """
    Parent-aware COA allocation:
      - root groups: 1000/2000/...
      - children groups under 1000: 1100/1200...
      - leaf accounts under 1000: 1010/1020...
      - children under 1200: 1210/1220...
    """
    if getattr(instance, "code", None):
        return

    branch_id = getattr(instance, "branch_id", None)
    if not branch_id:
        return

    start, end = _coa_range_for(instance)
    is_group = bool(getattr(instance, "is_group", False))

    parent = getattr(instance, "parent", None)
    parent_code = getattr(parent, "code", None)

    step = 100 if is_group else 10
    first = start if is_group else start + 10

    if parent_code and _is_int_str(parent_code):
        p = int(parent_code)

        if p % 1000 == 0:
            step = 100 if is_group else 10
            first = p + (100 if is_group else 10)
            start = max(start, p)
            end = min(end, p + 999)
        elif p % 100 == 0:
            step = 10
            first = p + 10
            start = max(start, p)
            end = min(end, p + 99)
        else:
            step = 1
            first = p + 1
            start = max(start, p)
            end = min(end, p + 9)

    instance.code = _next_coa_code_in_range(
        instance.__class__,
        branch_id=branch_id,
        start=start,
        end=end,
        first=first,
        step=step,
    )
