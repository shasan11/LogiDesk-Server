from __future__ import annotations
from typing import Optional
from actors.models import MainActor


def _sync_accounting_actor(main_actor: MainActor) -> None:
    from accounting.models import Actors as AccountingActor

    if not main_actor.branch_id or not main_actor.display_name:
        return

    defaults = {
        "branch_id": main_actor.branch_id,
        "name": main_actor.display_name,
        "active": main_actor.active,
        "user_add": main_actor.user_add,
    }

    actor, created = AccountingActor.objects.get_or_create(
        branch_id=main_actor.branch_id,
        name=main_actor.display_name,
        defaults=defaults,
    )
    if created:
        return

    updates = {}
    if actor.active != main_actor.active:
        updates["active"] = main_actor.active
    if updates:
        for key, value in updates.items():
            setattr(actor, key, value)
        actor.save(update_fields=list(updates.keys()) + ["updated"])


def upsert_main_actor(instance, field_name: str, actor_type: str) -> MainActor:
    defaults = {"branch": instance.branch, "actor_type": actor_type, "display_name": str(instance)}
    obj, _ = MainActor.objects.update_or_create(**{field_name: instance}, defaults=defaults)
    _sync_accounting_actor(obj)
    return obj


def delete_main_actor(instance, field_name: str) -> None:
    MainActor.objects.filter(**{field_name: instance}).delete()


def refresh_customer_main_actor_display(customer) -> None:
    if not hasattr(customer, "main_actor"):
        return
    ma = customer.main_actor
    ma.display_name = str(customer)
    ma.save(update_fields=["display_name", "updated"])


def get_main_actor_for_instance(instance) -> Optional[MainActor]:
    rel = getattr(instance, "main_actor", None)
    if rel:
        return rel
    return None
