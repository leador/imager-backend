import datetime

from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from .models import Action


def brand_create_action(brand, verb, target=None):
    now = timezone.now()
    last_hours = now - datetime.timedelta(hours=6)
    similar_actions = Action.objects.filter(brand=brand,
                                            verb=verb,
                                            target_id=target.id,
                                            target_ct=ContentType.objects.get_for_model(target).id,
                                            created_at__gte=last_hours,
                                            seen=False)
    if not similar_actions:
        action = Action(brand=brand, verb=verb, target=target)
        action.save()
        return True
    return False


def brand_remove_action(brand, verb, target=None, action=None):
    try:
        action = Action.objects.get(brand=brand,
                                    verb=verb,
                                    target_id=target.id,
                                    target_ct=ContentType.objects.get_for_model(target).id,
                                    seen=False)
        if action == 'delete':
            action.delete()
        else:
            action.seen = True
            action.save()
        return True
    except Action.DoesNotExist:
        return False
