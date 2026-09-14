# Generated migration

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Opportunity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('university', models.CharField(db_index=True, max_length=255)),
                ('type', models.CharField(choices=[('internship', 'Internship'), ('vacancy', 'Vacancy'), ('project', 'Project'), ('hackathon', 'Hackathon'), ('event', 'Event'), ('course', 'Course')], db_index=True, max_length=20)),
                ('title', models.CharField(max_length=500)),
                ('description', models.TextField()),
                ('requirements', models.TextField(blank=True)),
                ('audience', models.JSONField(default=dict, help_text='Target audience criteria (e.g., year, major, skills)')),
                ('deadline', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('source_url', models.URLField(blank=True, max_length=1000)),
                ('verified_status', models.CharField(choices=[('pending', 'Pending'), ('verified', 'Verified'), ('rejected', 'Rejected')], db_index=True, default='pending', max_length=20)),
                ('published', models.BooleanField(db_index=True, default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_opportunities', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Opportunity',
                'verbose_name_plural': 'Opportunities',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SavedOpportunity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('opportunity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saved_by', to='opportunities.opportunity')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saved_opportunities', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Saved Opportunity',
                'verbose_name_plural': 'Saved Opportunities',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='OpportunitySkill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('skill', models.CharField(db_index=True, max_length=200)),
                ('required_level', models.CharField(choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced'), ('expert', 'Expert')], default='intermediate', max_length=20)),
                ('weight', models.IntegerField(default=1, help_text='Importance weight (1-10)', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ('opportunity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='required_skills', to='opportunities.opportunity')),
            ],
            options={
                'verbose_name': 'Opportunity Skill',
                'verbose_name_plural': 'Opportunity Skills',
                'ordering': ['-weight', 'skill'],
            },
        ),
        migrations.CreateModel(
            name='MatchResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.IntegerField(help_text='Match score from 0 to 100', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('reasons', models.JSONField(default=list, help_text='List of reasons why this opportunity matches')),
                ('gaps', models.JSONField(default=list, help_text='List of skill/requirement gaps')),
                ('calculated_at', models.DateTimeField(auto_now=True)),
                ('opportunity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_matches', to='opportunities.opportunity')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='opportunity_matches', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Match Result',
                'verbose_name_plural': 'Match Results',
                'ordering': ['-score', '-calculated_at'],
            },
        ),
        migrations.AddIndex(
            model_name='opportunity',
            index=models.Index(fields=['-created_at'], name='opportuniti_created_idx'),
        ),
        migrations.AddIndex(
            model_name='opportunity',
            index=models.Index(fields=['university', 'type'], name='opportuniti_univers_idx'),
        ),
        migrations.AddIndex(
            model_name='opportunity',
            index=models.Index(fields=['published', 'verified_status'], name='opportuniti_publish_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='savedopportunity',
            unique_together={('student', 'opportunity')},
        ),
        migrations.AddIndex(
            model_name='savedopportunity',
            index=models.Index(fields=['student', '-created_at'], name='opportuniti_student_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='opportunityskill',
            unique_together={('opportunity', 'skill')},
        ),
        migrations.AlterUniqueTogether(
            name='matchresult',
            unique_together={('student', 'opportunity')},
        ),
        migrations.AddIndex(
            model_name='matchresult',
            index=models.Index(fields=['student', '-score'], name='opportuniti_student_score_idx'),
        ),
        migrations.AddIndex(
            model_name='matchresult',
            index=models.Index(fields=['opportunity', '-score'], name='opportuniti_opportu_idx'),
        ),
        migrations.AddIndex(
            model_name='matchresult',
            index=models.Index(fields=['-calculated_at'], name='opportuniti_calcula_idx'),
        ),
    ]
