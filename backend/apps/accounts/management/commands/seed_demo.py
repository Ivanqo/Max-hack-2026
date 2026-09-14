from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.careers.models import CareerRole, CareerRoleSkill, Skill, StudentSkill
from apps.knowledge.models import KnowledgeItem
from apps.notifications.services import get_notification_service
from apps.opportunities.models import Opportunity
from apps.profiles.models import CareerGoal, StudentProfile
from apps.subscriptions.models import Subscription
from apps.universities.models import University


DEMO_PASSWORD = 'demo12345'


class Command(BaseCommand):
    help = 'Create idempotent UniPath MAX demo data.'

    def handle(self, *args, **options):
        demo = self._university('Demo University', 'demo-university')
        north = self._university('North Tech University', 'north-tech')

        admin = self._user('admin@demo.local', 'Admin', 'Demo', 'admin', demo.name, True)
        self._user('editor@demo.local', 'Editor', 'Demo', 'editor', demo.name, True)
        student = self._user('student@demo.local', 'Student', 'Demo', 'student', demo.name, False)

        north_admin = self._user('admin@north.local', 'Admin', 'North', 'admin', north.name, True)
        north_student = self._user('student@north.local', 'Student', 'North', 'student', north.name, False)

        skills = self._skills(demo.name)
        roles = self._career_roles(demo.name, skills)
        self._profile(student, demo.name, roles['Backend Developer'], skills)
        self._opportunities(demo.name, admin, skills)
        self._knowledge(demo.name, admin)
        self._subscriptions(student)
        self._tenant_marker_data(north.name, north_admin, north_student)

        service = get_notification_service()
        for opportunity in Opportunity.objects.filter(
            university=demo.name,
            published=True,
            verified_status='verified',
        ):
            service.create_for_opportunity_subscriptions(opportunity)

        self.stdout.write(self.style.SUCCESS('Demo data ready.'))
        self.stdout.write(f'Admin: admin@demo.local / {DEMO_PASSWORD}')
        self.stdout.write(f'Editor: editor@demo.local / {DEMO_PASSWORD}')
        self.stdout.write(f'Student: student@demo.local / {DEMO_PASSWORD}')
        self.stdout.write(f'Second tenant student: student@north.local / {DEMO_PASSWORD}')

    def _university(self, name, slug):
        university, _ = University.objects.update_or_create(
            slug=slug,
            defaults={
                'name': name,
                'settings': {
                    'support_unit': 'Учебный офис',
                    'support_contact': f'helpdesk@{slug}.local',
                },
            },
        )
        return university

    def _user(self, email, first_name, last_name, role, university, staff):
        User = get_user_model()
        user, _ = User.objects.update_or_create(
            email=email,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'role': role,
                'university': university,
                'is_staff': staff,
                'is_superuser': role == 'admin',
                'is_active': True,
            },
        )
        user.set_password(DEMO_PASSWORD)
        user.save()
        return user

    def _skills(self, university):
        result = {}
        specs = [
            ('Python', 'technical'),
            ('SQL', 'technical'),
            ('Django', 'technical'),
            ('REST', 'technical'),
            ('Docker', 'tool'),
            ('Git', 'tool'),
            ('CI/CD', 'tool'),
            ('PostgreSQL', 'technical'),
            ('Linux', 'tool'),
            ('Data Analysis', 'technical'),
            ('Machine Learning', 'technical'),
            ('Product Thinking', 'soft'),
            ('React', 'technical'),
        ]
        for name, category in specs:
            result[name], _ = Skill.objects.update_or_create(
                university=university,
                name=name,
                defaults={'category': category},
            )
        return result

    def _career_roles(self, university, skills):
        specs = {
            'Backend Developer': [
                ('Python', 4, 2),
                ('Django', 3, 2),
                ('REST', 3, 1.5),
                ('SQL', 3, 1.5),
                ('Docker', 3, 1),
            ],
            'Data Analyst': [
                ('SQL', 4, 2),
                ('Python', 3, 1.5),
                ('Data Analysis', 4, 2),
                ('Product Thinking', 2, 1),
            ],
            'ML Engineer': [
                ('Python', 4, 2),
                ('Machine Learning', 4, 2),
                ('SQL', 3, 1),
                ('Docker', 3, 1),
            ],
            'Product Analyst': [
                ('SQL', 3, 1.5),
                ('Data Analysis', 4, 2),
                ('Product Thinking', 4, 2),
            ],
            'DevOps Engineer': [
                ('Linux', 4, 2),
                ('Docker', 4, 2),
                ('CI/CD', 4, 2),
                ('Git', 3, 1),
            ],
        }
        roles = {}
        for name, required in specs.items():
            role, _ = CareerRole.objects.update_or_create(
                university=university,
                name=name,
                defaults={
                    'description': f'{name} career track with deterministic skill-gap scoring.',
                    'active': True,
                },
            )
            roles[name] = role
            for skill_name, level, weight in required:
                CareerRoleSkill.objects.update_or_create(
                    career_role=role,
                    skill=skills[skill_name],
                    defaults={'required_level': level, 'weight': weight},
                )
        return roles

    def _profile(self, user, university, backend_role, skills):
        goal, _ = CareerGoal.objects.update_or_create(
            name=backend_role.name,
            defaults={'description': backend_role.description, 'is_active': True},
        )
        profile, _ = StudentProfile.objects.update_or_create(
            user=user,
            defaults={
                'university': university,
                'institute': 'Institute of Computer Science',
                'course': 3,
                'program': 'Software Engineering',
                'interests': ['Backend', 'Python', 'стажировки', 'практика'],
                'career_goal': goal,
                'onboarding_completed': True,
            },
        )
        for skill_name, level in [('Python', 4), ('SQL', 2), ('Git', 4), ('Django', 2), ('REST', 3)]:
            StudentSkill.objects.update_or_create(
                student=profile,
                skill=skills[skill_name],
                defaults={'level': level, 'evidence': 'Demo profile evidence'},
            )

    def _opportunities(self, university, admin, skills):
        items = [
            ('internship', 'Backend Internship at MAX Labs', 'Build Django APIs for student services.', ['Python', 'Django', 'REST', 'SQL'], 'MAX Labs'),
            ('project', 'University Practice Automation Project', 'Automate production practice requests and mentor approvals.', ['Python', 'SQL', 'Git'], 'Career Center'),
            ('hackathon', 'AI Student Services Hackathon', 'Prototype helpful AI tools on top of verified university data.', ['Python', 'Machine Learning', 'Product Thinking'], 'AI Center'),
            ('event', 'Career Center Backend Meetup', 'Meet alumni engineers and review internship roadmaps.', ['Backend', 'Git'], 'Career Center'),
            ('course', 'Docker for Student Projects', 'Short practical course on containers for project deployment.', ['Docker', 'Linux'], 'IT Department'),
            ('internship', 'Data Analyst Internship', 'Analyze student success and opportunity engagement datasets.', ['SQL', 'Data Analysis', 'Python'], 'Analytics Office'),
            ('project', 'PostgreSQL Knowledge Base Search', 'Improve deterministic search over verified university materials.', ['PostgreSQL', 'SQL', 'Python'], 'Digital Campus'),
            ('vacancy', 'Junior DevOps Assistant', 'Help maintain CI pipelines and Linux deployment scripts.', ['Linux', 'Docker', 'CI/CD', 'Git'], 'Infrastructure Team'),
            ('hackathon', 'Product Analytics Challenge', 'Find gaps in university service journeys using event data.', ['SQL', 'Data Analysis', 'Product Thinking'], 'Product Lab'),
            ('event', 'Practice Paperwork Clinic', 'Bring questions about production practice documents and deadlines.', ['практика'], 'Учебный офис'),
            ('course', 'REST API Design Sprint', 'Design clean REST APIs and document contracts.', ['REST', 'Django', 'Git'], 'Software Lab'),
            ('project', 'Student Mini App Prototype', 'Build a React interface for career guidance in MAX.', ['React', 'REST', 'Product Thinking'], 'MAX Lab'),
        ]
        deadline = timezone.now() + timedelta(days=45)
        for item_type, title, description, requirements, company in items:
            opportunity, _ = Opportunity.objects.update_or_create(
                university=university,
                title=title,
                defaults={
                    'type': item_type,
                    'description': description,
                    'requirements': '\n'.join(requirements),
                    'audience': {
                        'company': company,
                        'location': 'Campus / Hybrid',
                        'remote': item_type in ['project', 'course'],
                        'courses': [2, 3, 4],
                    },
                    'deadline': deadline,
                    'source_url': f'https://demo.local/opportunities/{self._slug(title)}',
                    'verified_status': 'verified',
                    'published': True,
                    'created_by': admin,
                },
            )
            for requirement in requirements:
                if requirement in skills:
                    opportunity.required_skills.update_or_create(
                        skill=requirement,
                        defaults={'required_level': 'intermediate', 'weight': 2},
                    )

    def _knowledge(self, university, admin):
        topics = [
            ('Как оформить производственную практику', 'Подайте заявление в личном кабинете, согласуйте место практики с кафедрой и загрузите договор не позднее чем за 10 рабочих дней.', 'Учебный офис', ['all', 'students', 'практика']),
            ('Сроки производственной практики', 'Актуальные сроки практики публикуются учебным офисом института. Для 3 курса основной период начинается в июне.', 'Учебный офис', ['students', 'практика']),
            ('Шаблон договора на практику', 'Используйте только утвержденный шаблон договора из раздела практики. Старые версии считаются неактуальными.', 'Юридический отдел', ['students', 'практика']),
            ('Как получить справку об обучении', 'Справка заказывается через личный кабинет студента и обычно готовится в течение трех рабочих дней.', 'Студенческий офис', ['all', 'students']),
            ('Повышенная академическая стипендия', 'Заявка подается при наличии подтвержденных достижений в учебной, научной, общественной или спортивной деятельности.', 'Стипендиальная комиссия', ['students']),
            ('Социальная стипендия', 'Для социальной стипендии требуется документ, подтверждающий право на государственную социальную помощь.', 'Стипендиальная комиссия', ['students']),
            ('Воинский учет для студентов', 'Студенты предоставляют документы воинского учета в военно-учетный стол в течение двух недель после зачисления.', 'Военно-учетный стол', ['students']),
            ('Академический отпуск', 'Академический отпуск оформляется по заявлению с приложением подтверждающих документов и согласованием деканата.', 'Деканат', ['students']),
            ('Карьерный центр', 'Карьерный центр помогает с резюме, стажировками, встречами с работодателями и индивидуальными консультациями.', 'Карьерный центр', ['students', 'стажировки']),
            ('Общежитие', 'Заявления на общежитие принимаются через электронную форму, приоритет зависит от категории студента и удаленности проживания.', 'Жилищная комиссия', ['students']),
            ('Студенческие проекты', 'Каталог проектов обновляется каждый месяц; студент может подать заявку в команду или предложить свою тему.', 'Проектный офис', ['students', 'project']),
            ('Хакатоны университета', 'Хакатоны публикуются в разделе возможностей. Для участия нужна команда или индивидуальная регистрация.', 'Проектный офис', ['students', 'хакатоны']),
            ('Пересдача экзамена', 'Пересдачи назначаются учебным офисом после публикации ведомости и заявления студента при необходимости.', 'Учебный офис', ['students']),
            ('Индивидуальный учебный план', 'ИУП согласуется с руководителем программы и утверждается приказом после проверки академической разницы.', 'Учебный офис', ['students']),
            ('Выбор элективных дисциплин', 'Выбор элективов открывается в личном кабинете на ограниченный период перед началом семестра.', 'Учебный офис', ['students']),
            ('Научный руководитель', 'Выбор научного руководителя оформляется через кафедру после предварительного согласования темы.', 'Кафедра', ['students']),
            ('Проектная практика', 'Проектная практика может засчитываться через участие в утвержденном проекте с отчетом и отзывом руководителя.', 'Проектный офис', ['практика', 'students']),
            ('Зачет волонтерской деятельности', 'Волонтерская деятельность учитывается при наличии подтверждений из официальной системы учета.', 'Воспитательный отдел', ['students']),
            ('Доступ к корпоративной почте', 'Корпоративная почта создается автоматически после зачисления и используется для официальных уведомлений.', 'IT Department', ['all', 'students']),
            ('Восстановление пароля', 'Пароль восстанавливается через единый аккаунт университета или через обращение в IT-поддержку.', 'IT Department', ['all']),
            ('Подача заявки на стажировку', 'Перед подачей проверьте требования, дедлайн, источник вакансии и соответствие вашей карьерной цели.', 'Карьерный центр', ['стажировки', 'students']),
            ('Подтверждение навыков', 'Навык можно подтвердить сертификатом, проектом, оценкой по дисциплине или отзывом руководителя.', 'Карьерный центр', ['students']),
            ('Консультация по резюме', 'Запишитесь на консультацию карьерного центра и приложите текущую версию резюме.', 'Карьерный центр', ['стажировки', 'students']),
            ('MAX-уведомления', 'Если внешняя интеграция недоступна, уведомление сохраняется в UniPath MAX со статусом simulated или pending.', 'Digital Campus', ['all']),
        ]
        actual_until = timezone.now().date() + timedelta(days=365)
        for title, content, unit, audience in topics:
            KnowledgeItem.objects.update_or_create(
                university=university,
                title=title,
                defaults={
                    'content': content,
                    'source_url': f'https://demo.local/knowledge/{self._slug(title)}',
                    'responsible_unit': unit,
                    'audience': audience,
                    'verified_status': 'verified',
                    'published': True,
                    'actual_until': actual_until,
                    'created_by': admin,
                },
            )

    def _subscriptions(self, student):
        for topic in ['Backend', 'AI', 'стажировки', 'хакатоны', 'практика', 'Institute of Computer Science']:
            Subscription.objects.get_or_create(
                student=student,
                topic=topic,
                defaults={'filters': {'topic': topic}, 'active': True},
            )

    def _tenant_marker_data(self, university, admin, student):
        goal, _ = CareerGoal.objects.update_or_create(
            name='Robotics Engineer',
            defaults={'description': 'Second-tenant demo career goal.', 'is_active': True},
        )
        StudentProfile.objects.update_or_create(
            user=student,
            defaults={
                'university': university,
                'institute': 'North Robotics Institute',
                'course': 2,
                'program': 'Robotics',
                'interests': ['Robotics', 'Python'],
                'career_goal': goal,
                'onboarding_completed': True,
            },
        )
        Opportunity.objects.update_or_create(
            university=university,
            title='North-only Robotics Internship',
            defaults={
                'type': 'internship',
                'description': 'Tenant isolation marker opportunity for North Tech students.',
                'requirements': 'Python\nLinux',
                'audience': {'company': 'North Robotics', 'location': 'North Campus', 'remote': False},
                'verified_status': 'verified',
                'published': True,
                'created_by': admin,
            },
        )
        KnowledgeItem.objects.update_or_create(
            university=university,
            title='North Tech private practice rules',
            defaults={
                'content': 'This material belongs only to North Tech University.',
                'responsible_unit': 'North Study Office',
                'audience': ['students'],
                'verified_status': 'verified',
                'published': True,
                'created_by': admin,
            },
        )

    def _slug(self, value):
        slug = ''.join(char.lower() if char.isalnum() else '-' for char in value)
        return '-'.join(part for part in slug.split('-') if part)
