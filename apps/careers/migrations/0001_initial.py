# Generated migration for careers app

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('universities', '0001_initial'),
        ('students', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Skill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('category', models.CharField(
                    choices=[
                        ('technical', 'Technical'),
                        ('soft', 'Soft Skills'),
                        ('language', 'Language'),
                        ('domain', 'Domain Knowledge'),
                        ('tool', 'Tools & Software'),
                        ('other', 'Other'),
                    ],
                    default='other',
                    max_length=50
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('university', models.ForeignKey(
                    blank=True,
                    help_text='Leave blank for general skills available to all universities',
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='skills',
                    to='universities.university'
                )),
            ],
            options={
                'ordering': ['category', 'name'],
            },
        ),
        migrations.CreateModel(
            name='CareerRole',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('university', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='career_roles',
                    to='universities.university'
                )),
            ],
            options={
                'ordering': ['university', 'name'],
            },
        ),
        migrations.CreateModel(
            name='StudentSkill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.IntegerField(
                    help_text='Student skill level (1-5)',
                    validators=[
                        django.core.validators.MinValueValidator(1),
                        django.core.validators.MaxValueValidator(5)
                    ]
                )),
                ('evidence', models.TextField(
                    blank=True,
                    help_text='Optional evidence or documentation of this skill (certifications, projects, etc.)',
                    null=True
                )),
                ('verified', models.BooleanField(
                    default=False,
                    help_text='Whether this skill has been verified by the university'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('skill', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='student_skills',
                    to='careers.skill'
                )),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='skills',
                    to='students.studentprofile'
                )),
            ],
            options={
                'ordering': ['student', '-level', 'skill__name'],
            },
        ),
        migrations.CreateModel(
            name='CareerRoleSkill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('required_level', models.IntegerField(
                    help_text='Required skill level (1-5)',
                    validators=[
                        django.core.validators.MinValueValidator(1),
                        django.core.validators.MaxValueValidator(5)
                    ]
                )),
                ('weight', models.FloatField(
                    default=1.0,
                    help_text='Weight/importance of this skill for the role',
                    validators=[django.core.validators.MinValueValidator(0.0)]
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('career_role', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='required_skills',
                    to='careers.careerrole'
                )),
                ('skill', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='career_roles',
                    to='careers.skill'
                )),
            ],
            options={
                'ordering': ['-weight', 'skill__name'],
            },
        ),
        migrations.AddIndex(
            model_name='studentskill',
            index=models.Index(fields=['student', 'level'], name='careers_stu_student_idx'),
        ),
        migrations.AddIndex(
            model_name='studentskill',
            index=models.Index(fields=['skill', 'level'], name='careers_stu_skill_i_idx'),
        ),
        migrations.AddIndex(
            model_name='studentskill',
            index=models.Index(fields=['verified'], name='careers_stu_verifie_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='studentskill',
            unique_together={('student', 'skill')},
        ),
        migrations.AddIndex(
            model_name='skill',
            index=models.Index(fields=['university', 'category'], name='careers_ski_univers_idx'),
        ),
        migrations.AddIndex(
            model_name='skill',
            index=models.Index(fields=['name'], name='careers_ski_name_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='skill',
            unique_together={('university', 'name')},
        ),
        migrations.AddIndex(
            model_name='careerrole',
            index=models.Index(fields=['university', 'active'], name='careers_car_univers_idx'),
        ),
        migrations.AddIndex(
            model_name='careerrole',
            index=models.Index(fields=['active'], name='careers_car_active_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='careerrole',
            unique_together={('university', 'name')},
        ),
        migrations.AddIndex(
            model_name='careerroleskill',
            index=models.Index(fields=['career_role', 'required_level'], name='careers_car_career__idx'),
        ),
        migrations.AlterUniqueTogether(
            name='careerroleskill',
            unique_together={('career_role', 'skill')},
        ),
    ]
