from __future__ import annotations

from decimal import Decimal
from typing import Dict
from django.db import transaction
from django.db.models import F


def _d(v) -> Decimal:
    try:
        return Decimal(v or 0)
    except Exception:
        return Decimal("0")


def _is_posted(tx) -> bool:
    """
    approved == True AND voided_at is NULL
    """
    return bool(getattr(tx, "approved", False)) and getattr(tx, "voided_at", None) is None


def _apply_deltas(account_deltas: Dict[str, Decimal]) -> None:
    if not account_deltas:
        return

    from accounting.models import Accounts

    ids = list(account_deltas.keys())
    with transaction.atomic():
        list(Accounts.objects.select_for_update().filter(id__in=ids).values_list("id", flat=True))
        for acc_id, delta in account_deltas.items():
            if delta:
                Accounts.objects.filter(id=acc_id).update(balance=F("balance") + delta)


# ---------------------- CashTransfer ----------------------

def _cashtransfer_deltas(ct_id) -> Dict[str, Decimal]:
    from accounting.models import CashTransfer, CashTransferItem

    ct = CashTransfer.objects.select_related("from_account").get(pk=ct_id)
    from_main_id = getattr(ct.from_account, "main_account_id", None)
    if not from_main_id:
        raise ValueError("CashTransfer.from_account.main_account is NULL (BankAccount must have main_account).")

    items = CashTransferItem.objects.select_related("to_account").filter(cash_transfer_id=ct.id)
    if not items.exists():
        raise ValueError("Cannot post CashTransfer with no items.")

    deltas: Dict[str, Decimal] = {}
    total_out = Decimal("0")

    for it in items:
        amt = _d(it.amount)
        if not amt:
            continue

        to_main_id = getattr(it.to_account, "main_account_id", None)
        if not to_main_id:
            raise ValueError("CashTransferItem.to_account.main_account is NULL.")

        deltas[to_main_id] = deltas.get(to_main_id, Decimal("0")) + amt
        total_out += amt

    deltas[from_main_id] = deltas.get(from_main_id, Decimal("0")) - total_out
    return deltas


def handle_cashtransfer_posting(instance, old_instance=None) -> None:
    old_posted = _is_posted(old_instance) if old_instance else False
    new_posted = _is_posted(instance)

    if not old_posted and new_posted:
        _apply_deltas(_cashtransfer_deltas(instance.id))
    elif old_posted and not new_posted:
        d = _cashtransfer_deltas(instance.id)
        _apply_deltas({k: -v for k, v in d.items()})


# ---------------------- JournalVoucher ----------------------

def _journalvoucher_deltas(jv_id) -> Dict[str, Decimal]:
    from accounting.models import JournalVoucherItem

    items = JournalVoucherItem.objects.filter(journal_voucher_id=jv_id)
    if not items.exists():
        raise ValueError("Cannot post JournalVoucher with no items.")

    deltas: Dict[str, Decimal] = {}
    for it in items:
        if not it.account_id:
            continue
        delta = _d(it.dr_amount) - _d(it.cr_amount)
        if not delta:
            continue
        deltas[it.account_id] = deltas.get(it.account_id, Decimal("0")) + delta
    return deltas


def handle_journalvoucher_posting(instance, old_instance=None) -> None:
    old_posted = _is_posted(old_instance) if old_instance else False
    new_posted = _is_posted(instance)

    if not old_posted and new_posted:
        _apply_deltas(_journalvoucher_deltas(instance.id))
    elif old_posted and not new_posted:
        d = _journalvoucher_deltas(instance.id)
        _apply_deltas({k: -v for k, v in d.items()})


# ---------------------- ChequeRegister ----------------------

def _is_cheque_posted(cr) -> bool:
    if not _is_posted(cr):
        return False
    return (getattr(cr, "status", "") or "").lower().strip() == "cleared"


def _cheque_direction(current, old_instance=None) -> str:
    """
    Need issued/received even after it becomes CLEARED.
    Priority:
      1) current.status if issued/received
      2) old.status if issued/received
      3) infer from received_date
    """
    cur = (getattr(current, "status", "") or "").lower().strip()
    if cur in ("issued", "received"):
        return cur

    if old_instance:
        old = (getattr(old_instance, "status", "") or "").lower().strip()
        if old in ("issued", "received"):
            return old

    return "received" if getattr(current, "received_date", None) else "issued"


def _chequeregister_other_account_id(cr) -> str:
    """
    Other side of cheque:
      - if coa_account set -> use coa_account.account (Accounts)
      - else if contact set -> use contact.account (Accounts)
      - else error
    """
    if getattr(cr, "coa_account_id", None):
        other = getattr(cr.coa_account, "account_id", None)
        if not other:
            raise ValueError("ChequeRegister.coa_account.account is NULL.")
        return other

    if getattr(cr, "contact_id", None):
        other = getattr(cr.contact, "account_id", None)
        if not other:
            raise ValueError("ChequeRegister.contact.account is NULL (Actor must have account).")
        return other

    raise ValueError("ChequeRegister needs coa_account or contact to post.")


def _chequeregister_deltas(cr_id, old_instance=None) -> Dict[str, Decimal]:
    from accounting.models import ChequeRegister

    cr = ChequeRegister.objects.select_related("bank_account", "coa_account", "contact").get(pk=cr_id)

    bank_main_id = getattr(cr.bank_account, "main_account_id", None)
    if not bank_main_id:
        raise ValueError("ChequeRegister.bank_account.main_account is NULL.")

    other_acc_id = _chequeregister_other_account_id(cr)

    amt = _d(cr.amount)
    if not amt:
        return {}

    direction = _cheque_direction(cr, old_instance=old_instance)

    # balance convention: balance += dr - cr
    # received: Dr bank, Cr other
    if direction == "received":
        return {bank_main_id: +amt, other_acc_id: -amt}

    # issued: Dr other, Cr bank
    return {bank_main_id: -amt, other_acc_id: +amt}


def handle_chequeregister_posting(instance, old_instance=None) -> None:
    old_posted = _is_cheque_posted(old_instance) if old_instance else False
    new_posted = _is_cheque_posted(instance)

    if not old_posted and new_posted:
        _apply_deltas(_chequeregister_deltas(instance.id, old_instance=old_instance))
    elif old_posted and not new_posted:
        d = _chequeregister_deltas(instance.id, old_instance=old_instance)
        _apply_deltas({k: -v for k, v in d.items()})
