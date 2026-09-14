from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('opportunities', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='Notification title', max_length=255, verbose_name='Title')),
                ('message', models.TextField(help_text='Notification message content', verbose_name='Message')),
                ('status', models.CharField(
                    choices=[('pending', 'Pending'), ('sent', 'Sent'), ('failed', 'Failed')],
                    default='pending',
                    help_text='Current notification status',
                    max_length=10,
                    verbose_name='Status'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='When the notification was created', verbose_name='Created At')),
                ('sent_at', models.DateTimeField(blank=True, help_text='When the notification was sent', null=True, verbose_name='Sent At')),
                ('opportunity', models.ForeignKey(
                    blank=True,
                    help_text='Related opportunity (optional)',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='notifications',
                    to='opportunities.opportunity',
                    verbose_name='Opportunity'
                )),
                ('student', models.ForeignKey(
                    help_text='The student who will receive this notification',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='notifications',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Student'
                )),
            ],
            options={
                'verbose_name': 'Notification',
                'verbose_name_plural': 'Notifications',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['-created_at'], name='notificatio_created_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['student', 'status'], name='notificatio_student_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['status', 'created_at'], name='notificatio_status_idx'),
        ),
    ]
