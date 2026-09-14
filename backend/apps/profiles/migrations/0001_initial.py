# Generated migration

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
            name='CareerGoal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Career Goal',
                'verbose_name_plural': 'Career Goals',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='StudentProfile',
            fields=[
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='student_profile', serialize=False, to=settings.AUTH_USER_MODEL)),
                ('university', models.CharField(blank=True, max_length=255)),
                ('institute', models.CharField(blank=True, max_length=255)),
                ('course', models.PositiveSmallIntegerField(blank=True, help_text='Year of study (1-6)', null=True)),
                ('program', models.CharField(blank=True, help_text='Study program or major', max_length=255)),
                ('interests', models.JSONField(blank=True, default=list, help_text='List of student interests and skills')),
                ('onboarding_completed', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('career_goal', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='students', to='profiles.careergoal')),
            ],
            options={
                'verbose_name': 'Student Profile',
                'verbose_name_plural': 'Student Profiles',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='studentprofile',
            index=models.Index(fields=['university'], name='profiles_st_univers_idx'),
        ),
        migrations.AddIndex(
            model_name='studentprofile',
            index=models.Index(fields=['onboarding_completed'], name='profiles_st_onboard_idx'),
        ),
    ]
