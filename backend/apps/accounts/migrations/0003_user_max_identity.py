from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_alter_user_groups_alter_user_role_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='max_linked_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='max_user_id',
            field=models.CharField(
                blank=True,
                help_text='Linked MAX platform user id for mini-app and bot notifications',
                max_length=64,
                null=True,
                unique=True,
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='max_username',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
