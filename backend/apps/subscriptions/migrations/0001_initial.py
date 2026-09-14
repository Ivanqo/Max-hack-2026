# Generated migration for subscriptions app

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('topic', models.CharField(help_text='Topic or category for the subscription', max_length=255)),
                ('filters', models.JSONField(blank=True, default=dict, help_text='JSON object containing filter criteria (e.g., location, salary, experience level)')),
                ('active', models.BooleanField(default=True, help_text='Whether this subscription is active')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('student', models.ForeignKey(help_text='Student who owns this subscription', on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Subscription',
                'verbose_name_plural': 'Subscriptions',
                'db_table': 'subscriptions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='subscription',
            index=models.Index(fields=['student', 'active'], name='subscriptio_student_idx'),
        ),
        migrations.AddIndex(
            model_name='subscription',
            index=models.Index(fields=['topic'], name='subscriptio_topic_idx'),
        ),
    ]
