from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.notifications.integrations.max.real_client import RealMaxClient


class Command(BaseCommand):
    help = 'Safely inspect MAX webhook subscriptions without printing secrets or full URLs.'

    def handle(self, *args, **options):
        result = RealMaxClient().get_webhook_subscriptions()
        if not result.get('success'):
            raise CommandError(result.get('error') or 'MAX subscription inspection failed')

        expected_url = getattr(settings, 'MAX_WEBHOOK_URL', '')
        subscriptions = result.get('subscriptions', [])
        matching = [item for item in subscriptions if isinstance(item, dict) and item.get('url') == expected_url]
        update_types = sorted({
            event_type
            for item in matching
            for event_type in (item.get('update_types') if isinstance(item.get('update_types'), list) else [])
            if isinstance(event_type, str)
        })
        self.stdout.write(f'Subscriptions returned: {len(subscriptions)}')
        self.stdout.write(f'Configured webhook URL present: {bool(expected_url)}')
        self.stdout.write(f'Matching subscriptions: {len(matching)}')
        self.stdout.write(f'Matching event types: {", ".join(update_types) or "none"}')
