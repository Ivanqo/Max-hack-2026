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
            name='InteractionEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('university', models.CharField(db_index=True, max_length=255)),
                ('event_type', models.CharField(choices=[('view', 'View'), ('click', 'Click'), ('search', 'Search'), ('save', 'Save'), ('unsave', 'Unsave'), ('apply', 'Apply'), ('share', 'Share'), ('filter', 'Filter'), ('sort', 'Sort'), ('export', 'Export'), ('login', 'Login'), ('logout', 'Logout'), ('signup', 'Signup')], db_index=True, help_text='Type of interaction event', max_length=50)),
                ('entity_type', models.CharField(blank=True, choices=[('opportunity', 'Opportunity'), ('user', 'User'), ('skill', 'Skill'), ('match', 'Match'), ('profile', 'Profile'), ('dashboard', 'Dashboard'), ('page', 'Page')], help_text='Type of entity involved in the event', max_length=50, null=True)),
                ('entity_id', models.CharField(blank=True, help_text='ID of the entity involved (if applicable)', max_length=255, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict, help_text='Additional event data (search terms, filters, etc.)')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('user', models.ForeignKey(blank=True, help_text='User who performed the action (nullable for anonymous events)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='interaction_events', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Interaction Event',
                'verbose_name_plural': 'Interaction Events',
                'ordering': ['-created_at', '-id'],
            },
        ),
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('university', models.CharField(db_index=True, max_length=255)),
                ('action', models.CharField(choices=[('create', 'Create'), ('update', 'Update'), ('delete', 'Delete'), ('verify', 'Verify'), ('reject', 'Reject'), ('publish', 'Publish'), ('unpublish', 'Unpublish'), ('approve', 'Approve'), ('ban', 'Ban'), ('unban', 'Unban'), ('assign', 'Assign'), ('unassign', 'Unassign'), ('export', 'Export'), ('import', 'Import'), ('restore', 'Restore')], db_index=True, help_text='Type of administrative action', max_length=50)),
                ('entity_type', models.CharField(choices=[('opportunity', 'Opportunity'), ('user', 'User'), ('skill', 'Skill'), ('match', 'Match'), ('profile', 'Profile'), ('settings', 'Settings'), ('report', 'Report')], help_text='Type of entity affected', max_length=50)),
                ('entity_id', models.CharField(help_text='ID of the affected entity', max_length=255)),
                ('metadata', models.JSONField(blank=True, default=dict, help_text='Additional details (old/new values, reason, etc.)')),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('admin', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_logs', to=settings.AUTH_USER_MODEL, help_text='Admin/organizer who performed the action')),
            ],
            options={
                'verbose_name': 'Audit Log',
                'verbose_name_plural': 'Audit Logs',
                'ordering': ['-timestamp', '-id'],
            },
        ),
        migrations.AddIndex(
            model_name='interactionevent',
            index=models.Index(fields=['-created_at'], name='analytics_i_created_c9f8f0_idx'),
        ),
        migrations.AddIndex(
            model_name='interactionevent',
            index=models.Index(fields=['event_type', '-created_at'], name='analytics_i_event_t_85a639_idx'),
        ),
        migrations.AddIndex(
            model_name='interactionevent',
            index=models.Index(fields=['university', '-created_at'], name='analytics_i_univers_0baf43_idx'),
        ),
        migrations.AddIndex(
            model_name='interactionevent',
            index=models.Index(fields=['user', '-created_at'], name='analytics_i_user_id_982a4d_idx'),
        ),
        migrations.AddIndex(
            model_name='interactionevent',
            index=models.Index(fields=['entity_type', 'entity_id'], name='analytics_i_entity__ad0d3d_idx'),
        ),
        migrations.AddIndex(
            model_name='interactionevent',
            index=models.Index(fields=['university', 'event_type', '-created_at'], name='analytics_i_univers_a7b245_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['-timestamp'], name='analytics_a_timesta_3f7e23_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['action', '-timestamp'], name='analytics_a_action_bf8912_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['university', '-timestamp'], name='analytics_a_univers_94c7a8_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['admin', '-timestamp'], name='analytics_a_admin_i_7e2fa1_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['entity_type', 'entity_id'], name='analytics_a_entity__6f0a94_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['university', 'action', '-timestamp'], name='analytics_a_univers_8d3c5e_idx'),
        ),
    ]
