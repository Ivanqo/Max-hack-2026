from django.core.management.base import BaseCommand, CommandError

from apps.notifications.integrations.max.real_client import RealMaxClient


class Command(BaseCommand):
    help = 'Register MAX Bot API webhook subscription using configured env vars.'

    def handle(self, *args, **options):
        result = RealMaxClient().ensure_webhook_subscription()
        if not result.get('success'):
            raise CommandError(result.get('error') or 'MAX webhook registration failed')
        self.stdout.write(self.style.SUCCESS('MAX webhook subscription registered.'))
