from django.conf import settings
import django.contrib.postgres.indexes
import django.contrib.postgres.search
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='KnowledgeItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('university', models.CharField(db_index=True, help_text='University this knowledge item belongs to', max_length=255)),
                ('title', models.CharField(help_text='Title of the knowledge item', max_length=500)),
                ('content', models.TextField(help_text='Main content of the knowledge item (supports markdown)')),
                ('source_url', models.URLField(blank=True, help_text='Original source URL if applicable', max_length=1000)),
                ('responsible_unit', models.CharField(blank=True, help_text='Department or unit responsible for this information', max_length=255)),
                ('audience', models.JSONField(blank=True, default=list, help_text='Target audience for this knowledge item')),
                ('verified_status', models.CharField(choices=[('draft', 'Draft'), ('verified', 'Verified'), ('outdated', 'Outdated')], db_index=True, default='draft', help_text='Verification status of the content', max_length=20)),
                ('published', models.BooleanField(db_index=True, default=False, help_text='Whether this item is visible to users')),
                ('actual_until', models.DateField(blank=True, db_index=True, help_text='Date until which this information is valid', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('search_vector', django.contrib.postgres.search.SearchVectorField(blank=True, null=True)),
                ('created_by', models.ForeignKey(help_text='User who created this knowledge item', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_knowledge_items', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Knowledge Item',
                'verbose_name_plural': 'Knowledge Items',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='KnowledgeReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('university', models.CharField(db_index=True, help_text='University context for this report', max_length=255)),
                ('reason', models.TextField(help_text='Reason for the report')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('reviewing', 'Under Review'), ('resolved', 'Resolved'), ('rejected', 'Rejected')], db_index=True, default='pending', help_text='Current status of the report', max_length=20)),
                ('resolution_note', models.TextField(blank=True, help_text='Admin note about how the report was resolved')),
                ('resolved_at', models.DateTimeField(blank=True, help_text='When the report was resolved', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('knowledge_item', models.ForeignKey(help_text='Knowledge item being reported', on_delete=django.db.models.deletion.CASCADE, related_name='reports', to='knowledge.knowledgeitem')),
                ('resolved_by', models.ForeignKey(blank=True, help_text='Admin who resolved the report', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='resolved_knowledge_reports', to=settings.AUTH_USER_MODEL)),
                ('student', models.ForeignKey(help_text='User who submitted the report', on_delete=django.db.models.deletion.CASCADE, related_name='knowledge_reports', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Knowledge Report',
                'verbose_name_plural': 'Knowledge Reports',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='knowledgeitem',
            index=models.Index(fields=['university', 'published'], name='knowledge_kn_univers_a8b9f7_idx'),
        ),
        migrations.AddIndex(
            model_name='knowledgeitem',
            index=models.Index(fields=['university', 'verified_status'], name='knowledge_kn_univers_e8c9d5_idx'),
        ),
        migrations.AddIndex(
            model_name='knowledgeitem',
            index=models.Index(fields=['verified_status', 'published'], name='knowledge_kn_verifie_b7a3c4_idx'),
        ),
        migrations.AddIndex(
            model_name='knowledgeitem',
            index=models.Index(fields=['actual_until'], name='knowledge_kn_actual__c6d8e2_idx'),
        ),
        migrations.AddIndex(
            model_name='knowledgeitem',
            index=models.Index(fields=['-created_at'], name='knowledge_kn_created_f9e1a5_idx'),
        ),
        migrations.AddIndex(
            model_name='knowledgeitem',
            index=django.contrib.postgres.indexes.GinIndex(fields=['search_vector'], name='knowledge_search_idx'),
        ),
        migrations.AddIndex(
            model_name='knowledgereport',
            index=models.Index(fields=['university', 'status'], name='knowledge_kn_univers_d4f2b8_idx'),
        ),
        migrations.AddIndex(
            model_name='knowledgereport',
            index=models.Index(fields=['status', '-created_at'], name='knowledge_kn_status_e3c7a9_idx'),
        ),
        migrations.AddIndex(
            model_name='knowledgereport',
            index=models.Index(fields=['knowledge_item', 'status'], name='knowledge_kn_knowled_a5d9f1_idx'),
        ),
        migrations.AddIndex(
            model_name='knowledgereport',
            index=models.Index(fields=['-created_at'], name='knowledge_kn_created_b8e2c6_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='knowledgereport',
            unique_together={('student', 'knowledge_item')},
        ),
    ]
