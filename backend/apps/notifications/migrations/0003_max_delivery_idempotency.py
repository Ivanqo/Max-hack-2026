from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0002_rename_notificatio_created_idx_notificatio_created_ae6ed6_idx_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('simulated', 'Simulated'),
                    ('sent', 'Sent'),
                    ('failed', 'Failed'),
                ],
                default='pending',
                help_text='Legacy delivery status kept for API compatibility',
                max_length=10,
                verbose_name='Status',
            ),
        ),
        migrations.AddField(
            model_name='notification',
            name='delivery_status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('simulated', 'Simulated'),
                    ('sent', 'Sent'),
                    ('failed', 'Failed'),
                ],
                default='pending',
                help_text='Provider delivery status',
                max_length=10,
                verbose_name='Delivery Status',
            ),
        ),
        migrations.AddField(
            model_name='notification',
            name='failed_at',
            field=models.DateTimeField(
                blank=True,
                help_text='When the last delivery attempt failed',
                null=True,
                verbose_name='Failed At',
            ),
        ),
        migrations.AddField(
            model_name='notification',
            name='idempotency_key',
            field=models.CharField(
                blank=True,
                help_text='Unique key preventing duplicate notifications',
                max_length=255,
                null=True,
                unique=True,
                verbose_name='Idempotency Key',
            ),
        ),
        migrations.AddField(
            model_name='notification',
            name='last_error',
            field=models.TextField(
                blank=True,
                help_text='Sanitized last delivery error',
                verbose_name='Last Error',
            ),
        ),
        migrations.AddField(
            model_name='notification',
            name='provider',
            field=models.CharField(
                blank=True,
                help_text='Notification provider used for delivery',
                max_length=32,
                verbose_name='Provider',
            ),
        ),
        migrations.AddField(
            model_name='notification',
            name='provider_message_id',
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text='External message identifier returned by MAX',
                max_length=255,
                null=True,
                verbose_name='Provider Message ID',
            ),
        ),
        migrations.AddField(
            model_name='notification',
            name='read_at',
            field=models.DateTimeField(
                blank=True,
                help_text='When the student marked this notification as read',
                null=True,
                verbose_name='Read At',
            ),
        ),
        migrations.CreateModel(
            name='MaxWebhookEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_id', models.CharField(db_index=True, max_length=255, unique=True)),
                ('event_type', models.CharField(blank=True, max_length=100)),
                ('payload', models.JSONField(default=dict)),
                ('processed_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'MAX Webhook Event',
                'verbose_name_plural': 'MAX Webhook Events',
                'ordering': ['-processed_at'],
            },
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['student', 'delivery_status'], name='notificatio_student_2ed9ce_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['delivery_status', 'created_at'], name='notificatio_deliver_61f43d_idx'),
        ),
        migrations.AddIndex(
            model_name='maxwebhookevent',
            index=models.Index(fields=['event_type', '-processed_at'], name='notificatio_event_t_2e493d_idx'),
        ),
    ]
