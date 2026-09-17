from django.core.management.base import BaseCommand

from apps.notifications.services import get_notification_service


class Command(BaseCommand):
    help = 'Retry failed MAX notifications without creating duplicates.'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=100)

    def handle(self, *args, **options):
        result = get_notification_service().retry_failed_notifications(
            limit=options['limit']
        )
        self.stdout.write(
            self.style.SUCCESS(
                'Retried {total}: {succeeded} succeeded, {failed} failed.'.format(**result)
            )
        )
