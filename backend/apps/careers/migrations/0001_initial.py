# Generated for MVP startup.

from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('profiles', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CareerRole',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('university', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['university', 'name'],
                'unique_together': {('university', 'name')},
            },
        ),
        migrations.CreateModel(
            name='Skill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('university', models.CharField(blank=True, help_text='Leave blank for general skills available to all universities', max_length=255, null=True)),
                ('name', models.CharField(max_length=200)),
                ('category', models.CharField(choices=[('technical', 'Technical'), ('soft', 'Soft Skills'), ('language', 'Language'), ('domain', 'Domain Knowledge'), ('tool', 'Tools & Software'), ('other', 'Other')], default='other', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['category', 'name'],
                'unique_together': {('university', 'name')},
            },
        ),
        migrations.CreateModel(
            name='StudentSkill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.IntegerField(help_text='Student skill level (1-5)', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('evidence', models.TextField(blank=True, help_text='Optional evidence or documentation of this skill (certifications, projects, etc.)', null=True)),
                ('verified', models.BooleanField(default=False, help_text='Whether this skill has been verified by the university')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('skill', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_skills', to='careers.skill')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='skills', to='profiles.studentprofile')),
            ],
            options={
                'ordering': ['student', '-level', 'skill__name'],
                'unique_together': {('student', 'skill')},
            },
        ),
        migrations.CreateModel(
            name='CareerRoleSkill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('required_level', models.IntegerField(help_text='Required skill level (1-5)', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('weight', models.FloatField(default=1.0, help_text='Weight/importance of this skill for the role', validators=[django.core.validators.MinValueValidator(0.0)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('career_role', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='required_skills', to='careers.careerrole')),
                ('skill', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='career_roles', to='careers.skill')),
            ],
            options={
                'ordering': ['-weight', 'skill__name'],
                'unique_together': {('career_role', 'skill')},
            },
        ),
        migrations.AddIndex(
            model_name='careerrole',
            index=models.Index(fields=['university', 'active'], name='careers_car_univer_1d12a7_idx'),
        ),
        migrations.AddIndex(
            model_name='careerrole',
            index=models.Index(fields=['active'], name='careers_car_active_31df9e_idx'),
        ),
        migrations.AddIndex(
            model_name='skill',
            index=models.Index(fields=['university', 'category'], name='careers_ski_univer_61b124_idx'),
        ),
        migrations.AddIndex(
            model_name='skill',
            index=models.Index(fields=['name'], name='careers_ski_name_127c41_idx'),
        ),
        migrations.AddIndex(
            model_name='studentskill',
            index=models.Index(fields=['student', 'level'], name='careers_stu_student_03f4c4_idx'),
        ),
        migrations.AddIndex(
            model_name='studentskill',
            index=models.Index(fields=['skill', 'level'], name='careers_stu_skill_i_c167dd_idx'),
        ),
        migrations.AddIndex(
            model_name='studentskill',
            index=models.Index(fields=['verified'], name='careers_stu_verifie_d4f75f_idx'),
        ),
        migrations.AddIndex(
            model_name='careerroleskill',
            index=models.Index(fields=['career_role', 'required_level'], name='careers_car_career_06c20c_idx'),
        ),
    ]
