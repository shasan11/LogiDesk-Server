from __future__ import annotations

import re
from django.db import transaction

_NUM_RE = re.compile(r"(\d+)$")


def _clean(s):
    return (s or "").strip()


def _next_accounts_prefixed_code(Accounts, *, branch_id, prefix: str, width: int = 5) -> str:
    """
    Creates next Accounts.code like AT00001 (for actor accounts).
    """
    with transaction.atomic():
        qs = (
            Accounts.objects.select_for_update()
            .filter(branch_id=branch_id, code__startswith=prefix)
            .exclude(code__isnull=True)
            .exclude(code="")
            .order_by("-code")
        )
        last = qs.first()
        n = 1
        if last:
            m = _NUM_RE.search(last.code or "")
            if m:
                try:
                    n = int(m.group(1)) + 1
                except Exception:
                    n = 1
        return f"{prefix}{str(n).zfill(width)}"


@transaction.atomic
def sync_accounts_for_coa(coa_instance) -> None:
    """
    Ensure ChartofAccount.account => Accounts(code=coa.code, name=coa.name, class='coa', balance=0 on create only)
    """
    from accounting.models import Accounts

    branch_id = getattr(coa_instance, "branch_id", None)
    code = _clean(getattr(coa_instance, "code", None))
    name = _clean(getattr(coa_instance, "name", None))

    if not branch_id or not code or not name:
        return

    desired_class = "coa"
    active = getattr(coa_instance, "active", True)
    user_add = getattr(coa_instance, "user_add", None)

    linked = getattr(coa_instance, "account", None)

    if linked:
        if linked.branch_id != branch_id:
            raise ValueError("COA linked Accounts.branch mismatch.")

        updates = {}
        if linked.code != code:
            updates["code"] = code
        if linked.name != name:
            updates["name"] = name
        if linked.account_class != desired_class:
            updates["account_class"] = desired_class
        if getattr(linked, "active", True) != active:
            updates["active"] = active

        if updates:
            for k, v in updates.items():
                setattr(linked, k, v)
            linked.save(update_fields=list(updates.keys()) + ["updated"])
        return

    existing = Accounts.objects.filter(branch_id=branch_id, code=code).first()
    if existing:
        updates = {}
        if existing.name != name:
            updates["name"] = name
        if existing.account_class != desired_class:
            updates["account_class"] = desired_class
        if getattr(existing, "active", True) != active:
            updates["active"] = active
        if updates:
            for k, v in updates.items():
                setattr(existing, k, v)
            existing.save(update_fields=list(updates.keys()) + ["updated"])

        coa_instance.account = existing
        return

    acc = Accounts.objects.create(
        branch_id=branch_id,
        code=code,
        name=name,
        account_class=desired_class,
        balance=0,
        user_add=user_add,
        active=active,
    )
    coa_instance.account = acc


@transaction.atomic
def sync_accounts_for_bank_account(bank_instance) -> None:
    """
    Ensure BankAccount.main_account => Accounts(code=bank.code, name=bank.display_name, class='bank', balance=0 on create only)
    """
    from accounting.models import Accounts

    branch_id = getattr(bank_instance, "branch_id", None)
    code = _clean(getattr(bank_instance, "code", None))
    name = _clean(getattr(bank_instance, "display_name", None))

    if not branch_id or not code or not name:
        return

    desired_class = "bank"
    active = getattr(bank_instance, "active", True)
    user_add = getattr(bank_instance, "user_add", None)

    linked = getattr(bank_instance, "main_account", None)

    if linked:
        if linked.branch_id != branch_id:
            raise ValueError("BankAccount linked Accounts.branch mismatch.")

        updates = {}
        if linked.code != code:
            updates["code"] = code
        if linked.name != name:
            updates["name"] = name
        if linked.account_class != desired_class:
            updates["account_class"] = desired_class
        if getattr(linked, "active", True) != active:
            updates["active"] = active

        if updates:
            for k, v in updates.items():
                setattr(linked, k, v)
            linked.save(update_fields=list(updates.keys()) + ["updated"])
        return

    existing = Accounts.objects.filter(branch_id=branch_id, code=code).first()
    if existing:
        updates = {}
        if existing.name != name:
            updates["name"] = name
        if existing.account_class != desired_class:
            updates["account_class"] = desired_class
        if getattr(existing, "active", True) != active:
            updates["active"] = active
        if updates:
            for k, v in updates.items():
                setattr(existing, k, v)
            existing.save(update_fields=list(updates.keys()) + ["updated"])

        bank_instance.main_account = existing
        return

    acc = Accounts.objects.create(
        branch_id=branch_id,
        code=code,
        name=name,
        account_class=desired_class,
        balance=0,
        user_add=user_add,
        active=active,
    )
    bank_instance.main_account = acc


@transaction.atomic
def sync_accounts_for_actor(actor_instance) -> None:
    """
    Ensure Actors.account => Accounts(code=AT00001..., name=actor.name, class='actor', balance=0 on create only)
    """
    from accounting.models import Accounts

    branch_id = getattr(actor_instance, "branch_id", None)
    name = _clean(getattr(actor_instance, "name", None))

    if not branch_id or not name:
        return

    desired_class = "actor"
    active = getattr(actor_instance, "active", True)
    user_add = getattr(actor_instance, "user_add", None)

    linked = getattr(actor_instance, "account", None)

    if linked:
        if linked.branch_id != branch_id:
            raise ValueError("Actor linked Accounts.branch mismatch.")

        updates = {}
        if linked.name != name:
            updates["name"] = name
        if linked.account_class != desired_class:
            updates["account_class"] = desired_class
        if getattr(linked, "active", True) != active:
            updates["active"] = active

        if updates:
            for k, v in updates.items():
                setattr(linked, k, v)
            linked.save(update_fields=list(updates.keys()) + ["updated"])
        return

    # create a new Accounts row for this actor
    code = _next_accounts_prefixed_code(Accounts, branch_id=branch_id, prefix="AT", width=5)

    acc = Accounts.objects.create(
        branch_id=branch_id,
        code=code,
        name=name,
        account_class=desired_class,
        balance=0,
        user_add=user_add,
        active=active,
    )
    actor_instance.account = acc
