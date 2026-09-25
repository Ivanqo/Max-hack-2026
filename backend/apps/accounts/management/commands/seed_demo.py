from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.analytics.models import AuditLog, InteractionEvent
from apps.careers.models import CareerRole, CareerRoleSkill, Skill, StudentSkill
from apps.knowledge.models import KnowledgeItem
from apps.notifications.integrations.max import MockMaxClient
from apps.notifications.models import Notification
from apps.notifications.services import NotificationService
from apps.opportunities.models import Opportunity
from apps.profiles.models import CareerGoal, StudentProfile
from apps.subscriptions.models import Subscription
from apps.universities.models import University


DEMO_PASSWORD = 'demo12345'
PRIMARY_UNIVERSITY = 'НИУ МГСУ'
SECONDARY_UNIVERSITY = 'МАИ'
LEGACY_NORTH_UNIVERSITY = 'North Tech University'
NORTH_PRIVATE_KNOWLEDGE_TITLE = 'North Tech private practice rules'

LEGACY_PRIMARY_UNIVERSITIES = ['Demo University']
LEGACY_SECONDARY_UNIVERSITIES = ['North Tech University']

LEGACY_ROLE_NAMES = [
    'Backend Developer',
    'Data Analyst',
    'ML Engineer',
    'Product Analyst',
    'DevOps Engineer',
]

LEGACY_OPPORTUNITY_TITLES = [
    'Backend Internship at MAX Labs',
    'University Practice Automation Project',
    'AI Student Services Hackathon',
    'Career Center Backend Meetup',
    'Docker for Student Projects',
    'Data Analyst Internship',
    'PostgreSQL Knowledge Base Search',
    'Junior DevOps Assistant',
    'Product Analytics Challenge',
    'REST API Design Sprint',
    'Student Mini App Prototype',
    'North-only Robotics Internship',
]


class Command(BaseCommand):
    help = 'Create idempotent UniPath MAX demo data.'

    def handle(self, *args, **options):
        self._rename_university_scope(LEGACY_PRIMARY_UNIVERSITIES, PRIMARY_UNIVERSITY)
        self._rename_university_scope(LEGACY_SECONDARY_UNIVERSITIES, SECONDARY_UNIVERSITY)

        primary = self._university(PRIMARY_UNIVERSITY, 'demo-university')
        secondary = self._university(SECONDARY_UNIVERSITY, 'north-tech')

        self._cleanup_legacy_seed_rows()

        admin = self._user('admin@demo.local', 'Администратор', 'МГСУ', 'admin', primary.name, True)
        self._user('editor@demo.local', 'Редактор', 'МГСУ', 'editor', primary.name, True)
        student = self._user('student@demo.local', 'Студент', 'МГСУ', 'student', primary.name, False)

        secondary_admin = self._user('admin@north.local', 'Администратор', 'МАИ', 'admin', secondary.name, True)
        secondary_student = self._user('student@north.local', 'Студент', 'МАИ', 'student', secondary.name, False)

        primary_skills = self._mgsu_skills(primary.name)
        primary_roles = self._mgsu_career_roles(primary.name, primary_skills)
        self._profile(student, primary.name, primary_roles['BIM-координатор в строительстве'], primary_skills)
        self._mgsu_opportunities(primary.name, admin)
        self._mgsu_knowledge(primary.name, admin)
        self._subscriptions(student)

        secondary_skills = self._mai_skills(secondary.name)
        secondary_roles = self._mai_career_roles(secondary.name, secondary_skills)
        self._secondary_profile(secondary_student, secondary.name, secondary_roles['Инженер-конструктор БПЛА'], secondary_skills)
        self._mai_opportunities(secondary.name, secondary_admin)
        self._mai_knowledge(secondary.name, secondary_admin)

        # Demo seeding runs on every production container start. Never reset or
        # simulate real notification deliveries as part of a production boot.
        if getattr(settings, 'USE_MOCK_MAX_CLIENT', True):
            Notification.objects.filter(
                student__university=primary.name,
                idempotency_key__startswith='subscription:',
                delivery_status=Notification.DeliveryStatus.FAILED,
            ).update(
                status=Notification.Status.PENDING,
                delivery_status=Notification.DeliveryStatus.PENDING,
                failed_at=None,
                last_error='',
            )
            service = NotificationService(client=MockMaxClient())
            for opportunity in Opportunity.objects.filter(
                university=primary.name,
                published=True,
                verified_status='verified',
            ):
                service.create_for_opportunity_subscriptions(opportunity)

        self.stdout.write(self.style.SUCCESS('Demo data ready.'))
        self.stdout.write(f'Primary university: {PRIMARY_UNIVERSITY}')
        self.stdout.write(f'Second university: {SECONDARY_UNIVERSITY}')
        self.stdout.write(f'Admin: admin@demo.local / {DEMO_PASSWORD}')
        self.stdout.write(f'Editor: editor@demo.local / {DEMO_PASSWORD}')
        self.stdout.write(f'Student: student@demo.local / {DEMO_PASSWORD}')
        self.stdout.write(f'Second tenant student: student@north.local / {DEMO_PASSWORD}')

    def _rename_university_scope(self, old_names, new_name):
        User = get_user_model()
        for old_name in old_names:
            if old_name == new_name:
                continue
            models = [User, StudentProfile, Skill, CareerRole, Opportunity, InteractionEvent, AuditLog]
            # North Tech is a separate legacy tenant, not the current MAI tenant.
            # Its private knowledge must retain its original scope.
            if old_name != LEGACY_NORTH_UNIVERSITY:
                models.append(KnowledgeItem)
            for model in models:
                model.objects.filter(university=old_name).update(university=new_name)

        # An earlier seed version reassigned this explicitly North Tech-only
        # record while renaming the legacy tenant. Restore its known owner and
        # visibility without changing or deleting the content itself.
        KnowledgeItem.objects.filter(
            university=SECONDARY_UNIVERSITY,
            title=NORTH_PRIVATE_KNOWLEDGE_TITLE,
        ).update(university=LEGACY_NORTH_UNIVERSITY)

    def _cleanup_legacy_seed_rows(self):
        CareerRole.objects.filter(name__in=LEGACY_ROLE_NAMES).delete()
        Opportunity.objects.filter(title__in=LEGACY_OPPORTUNITY_TITLES).delete()
        Subscription.objects.filter(topic__in=['Backend', 'AI', 'Institute of Computer Science']).delete()

    def _university(self, name, slug):
        university, _ = University.objects.update_or_create(
            slug=slug,
            defaults={
                'name': name,
                'settings': {
                    'support_unit': 'Студенческий офис',
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
                # `role='admin'` is a tenant-scoped university admin, not a
                # Django platform superuser. `is_superuser` bypasses
                # university filtering across the codebase.
                'is_superuser': False,
                'is_active': True,
            },
        )
        user.set_password(DEMO_PASSWORD)
        user.save()
        return user

    def _mgsu_skills(self, university):
        return self._skills(university, [
            ('BIM-моделирование', 'technical'),
            ('Revit', 'tool'),
            ('Renga', 'tool'),
            ('Navisworks', 'tool'),
            ('AutoCAD', 'tool'),
            ('ЛИРА-САПР', 'tool'),
            ('SCAD', 'tool'),
            ('Гранд-Смета', 'tool'),
            ('СП и ГОСТ', 'domain'),
            ('Проектная документация', 'domain'),
            ('Технология строительного производства', 'domain'),
            ('Геодезия', 'technical'),
            ('ГИС', 'technical'),
            ('4D-планирование', 'technical'),
            ('Python', 'technical'),
            ('SQL', 'technical'),
            ('Коммуникация с заказчиком', 'soft'),
            ('Охрана труда', 'domain'),
        ])

    def _mai_skills(self, university):
        return self._skills(university, [
            ('Аэродинамика', 'domain'),
            ('Конструкция летательных аппаратов', 'domain'),
            ('CATIA', 'tool'),
            ('Компас-3D', 'tool'),
            ('MATLAB/Simulink', 'tool'),
            ('C/C++', 'technical'),
            ('Python', 'technical'),
            ('Встроенные системы', 'technical'),
            ('Авионика', 'domain'),
            ('Испытания и телеметрия', 'domain'),
            ('Системная инженерия', 'domain'),
            ('Технический английский', 'language'),
        ])

    def _skills(self, university, specs):
        result = {}
        for name, category in specs:
            result[name], _ = Skill.objects.update_or_create(
                university=university,
                name=name,
                defaults={'category': category},
            )
        return result

    def _mgsu_career_roles(self, university, skills):
        specs = {
            'BIM-координатор в строительстве': {
                'description': 'Ведет цифровую модель объекта, проверяет коллизии и синхронизирует архитекторов, конструкторов и инженеров.',
                'avg_salary': '160 000 - 260 000 ₽',
                'demand_level': 'high',
                'education_path': ['Освоить Revit/Renga', 'Собрать BIM-модель учебного объекта', 'Пройти практику в проектном бюро'],
                'skills': [('BIM-моделирование', 4, 2), ('Revit', 4, 2), ('Navisworks', 3, 1.5), ('Проектная документация', 3, 1.5), ('Коммуникация с заказчиком', 3, 1)],
            },
            'Инженер-конструктор зданий': {
                'description': 'Проектирует несущие конструкции, выполняет расчеты и готовит разделы КР/КЖ для экспертизы.',
                'avg_salary': '140 000 - 230 000 ₽',
                'demand_level': 'high',
                'education_path': ['Повторить строительную механику', 'Освоить ЛИРА-САПР или SCAD', 'Подготовить расчетный проект'],
                'skills': [('ЛИРА-САПР', 4, 2), ('SCAD', 4, 2), ('СП и ГОСТ', 4, 1.5), ('AutoCAD', 3, 1), ('Проектная документация', 3, 1)],
            },
            'Инженер ПТО': {
                'description': 'Сопровождает стройку документами, графиками, актами и связью между площадкой, проектировщиками и заказчиком.',
                'avg_salary': '120 000 - 200 000 ₽',
                'demand_level': 'high',
                'education_path': ['Изучить исполнительную документацию', 'Разобрать календарный график', 'Пройти практику на строительной площадке'],
                'skills': [('Технология строительного производства', 4, 2), ('Проектная документация', 3, 1.5), ('Охрана труда', 3, 1), ('4D-планирование', 3, 1), ('Коммуникация с заказчиком', 4, 1)],
            },
            'Специалист по сметному делу': {
                'description': 'Готовит сметы, проверяет объемы работ и помогает оценивать стоимость строительных проектов.',
                'avg_salary': '110 000 - 190 000 ₽',
                'demand_level': 'medium',
                'education_path': ['Освоить Гранд-Смету', 'Разобрать ФЕР/ТЕР', 'Собрать смету по учебному проекту'],
                'skills': [('Гранд-Смета', 4, 2), ('СП и ГОСТ', 3, 1.5), ('Проектная документация', 3, 1), ('AutoCAD', 2, 1), ('Коммуникация с заказчиком', 3, 1)],
            },
            'Геодезист стройплощадки': {
                'description': 'Выполняет разбивочные работы, контролирует геометрию объекта и передает точные данные строительной команде.',
                'avg_salary': '120 000 - 210 000 ₽',
                'demand_level': 'medium',
                'education_path': ['Закрепить геодезию', 'Поработать с полевыми измерениями', 'Подготовить исполнительную схему'],
                'skills': [('Геодезия', 4, 2), ('AutoCAD', 3, 1), ('ГИС', 3, 1), ('СП и ГОСТ', 3, 1), ('Охрана труда', 3, 1)],
            },
            'ГИС-аналитик городской инфраструктуры': {
                'description': 'Анализирует пространственные данные города, инфраструктуры и транспортной доступности для строительных проектов.',
                'avg_salary': '130 000 - 220 000 ₽',
                'demand_level': 'medium',
                'education_path': ['Освоить ГИС', 'Подготовить слой городской инфраструктуры', 'Автоматизировать анализ на Python/SQL'],
                'skills': [('ГИС', 4, 2), ('Python', 3, 1.5), ('SQL', 3, 1.5), ('Проектная документация', 2, 1), ('Коммуникация с заказчиком', 3, 1)],
            },
        }
        return self._career_roles(university, skills, specs)

    def _mai_career_roles(self, university, skills):
        specs = {
            'Инженер-конструктор БПЛА': {
                'description': 'Проектирует узлы беспилотных летательных аппаратов и участвует в аэродинамической компоновке.',
                'avg_salary': '150 000 - 260 000 ₽',
                'demand_level': 'high',
                'education_path': ['Освоить CATIA/Компас-3D', 'Собрать расчетную модель БПЛА', 'Пройти проектную практику в авиационной лаборатории'],
                'skills': [('Аэродинамика', 4, 2), ('Конструкция летательных аппаратов', 4, 2), ('CATIA', 3, 1.5), ('Компас-3D', 3, 1), ('Технический английский', 3, 1)],
            },
            'Инженер по авионике': {
                'description': 'Разрабатывает и проверяет бортовые электронные системы, датчики и каналы обмена данными.',
                'avg_salary': '160 000 - 280 000 ₽',
                'demand_level': 'high',
                'education_path': ['Изучить авионику', 'Собрать стенд с телеметрией', 'Протестировать протокол обмена данными'],
                'skills': [('Авионика', 4, 2), ('Встроенные системы', 4, 2), ('C/C++', 3, 1.5), ('Испытания и телеметрия', 3, 1), ('Системная инженерия', 3, 1)],
            },
            'Разработчик встроенного ПО для авиации': {
                'description': 'Пишет надежное ПО для бортовых контроллеров, стендов испытаний и наземной диагностики.',
                'avg_salary': '170 000 - 300 000 ₽',
                'demand_level': 'high',
                'education_path': ['Освоить C/C++ для embedded', 'Сделать стендовый проект', 'Добавить телеметрию и тесты'],
                'skills': [('C/C++', 4, 2), ('Встроенные системы', 4, 2), ('MATLAB/Simulink', 3, 1), ('Python', 3, 1), ('Испытания и телеметрия', 3, 1)],
            },
        }
        return self._career_roles(university, skills, specs)

    def _career_roles(self, university, skills, specs):
        roles = {}
        for name, spec in specs.items():
            role, _ = CareerRole.objects.update_or_create(
                university=university,
                name=name,
                defaults={
                    'description': spec['description'],
                    'avg_salary': spec['avg_salary'],
                    'demand_level': spec['demand_level'],
                    'education_path': spec['education_path'],
                    'active': True,
                },
            )
            roles[name] = role
            for skill_name, level, weight in spec['skills']:
                CareerRoleSkill.objects.update_or_create(
                    career_role=role,
                    skill=skills[skill_name],
                    defaults={'required_level': level, 'weight': weight},
                )
        return roles

    def _profile(self, user, university, role, skills):
        goal, _ = CareerGoal.objects.update_or_create(
            name=role.name,
            defaults={'description': role.description, 'is_active': True},
        )
        profile, _ = StudentProfile.objects.update_or_create(
            user=user,
            defaults={
                'university': university,
                'institute': 'Институт цифровых технологий и моделирования в строительстве',
                'course': 3,
                'program': 'Цифровое строительство и BIM',
                'interests': ['BIM', 'практика', 'стажировки', 'сметное дело', 'проектирование'],
                'career_goal': goal,
                'onboarding_completed': True,
            },
        )
        selected_skills = [
            ('BIM-моделирование', 4),
            ('Revit', 3),
            ('AutoCAD', 4),
            ('Проектная документация', 3),
            ('СП и ГОСТ', 2),
        ]
        profile.skills.exclude(skill__name__in=[name for name, _ in selected_skills]).delete()
        for skill_name, level in selected_skills:
            StudentSkill.objects.update_or_create(
                student=profile,
                skill=skills[skill_name],
                defaults={'level': level, 'evidence': 'Демо-профиль студента МГСУ'},
            )

    def _secondary_profile(self, user, university, role, skills):
        goal, _ = CareerGoal.objects.update_or_create(
            name=role.name,
            defaults={'description': role.description, 'is_active': True},
        )
        profile, _ = StudentProfile.objects.update_or_create(
            user=user,
            defaults={
                'university': university,
                'institute': 'Институт авиационной техники',
                'course': 2,
                'program': 'Проектирование беспилотных авиационных систем',
                'interests': ['БПЛА', 'авионика', 'embedded', 'проектная практика'],
                'career_goal': goal,
                'onboarding_completed': True,
            },
        )
        selected_skills = [('Аэродинамика', 3), ('CATIA', 2), ('C/C++', 3), ('Технический английский', 3)]
        profile.skills.exclude(skill__name__in=[name for name, _ in selected_skills]).delete()
        for skill_name, level in selected_skills:
            StudentSkill.objects.update_or_create(
                student=profile,
                skill=skills[skill_name],
                defaults={'level': level, 'evidence': 'Демо-профиль студента МАИ'},
            )

    def _mgsu_opportunities(self, university, admin):
        self._opportunities(university, admin, [
            ('internship', 'Стажировка BIM-моделировщика в Мосинжпроекте', 'Помогайте собирать информационные модели станционных комплексов и проверять коллизии.', ['BIM-моделирование', 'Revit', 'Navisworks', 'Проектная документация'], 'Мосинжпроект'),
            ('project', 'Цифровой двойник кампуса МГСУ', 'Соберите модель учебного корпуса и добавьте слои инженерных систем для навигации и эксплуатации.', ['BIM-моделирование', 'Renga', 'ГИС', 'SQL'], 'Проектный офис МГСУ'),
            ('internship', 'Практика инженера ПТО на объекте реновации', 'Работа с исполнительной документацией, графиками и актами под наставничеством инженера ПТО.', ['Технология строительного производства', 'Проектная документация', 'Охрана труда'], 'ГК ФСК'),
            ('course', 'Revit и Renga для проектировщика', 'Короткий интенсив по моделированию конструктивных и архитектурных разделов.', ['Revit', 'Renga', 'BIM-моделирование'], 'Центр цифрового строительства'),
            ('vacancy', 'Младший сметчик в строительной компании', 'Проверка объемов работ и подготовка локальных смет для учебных и коммерческих проектов.', ['Гранд-Смета', 'СП и ГОСТ', 'Проектная документация'], 'Сметный департамент'),
            ('hackathon', 'Хакатон Умный строительный город', 'Команды решают задачи стройконтроля, городских данных и цифровых сервисов для кампуса.', ['ГИС', 'Python', 'SQL', 'Коммуникация с заказчиком'], 'МГСУ x Департамент строительства'),
            ('project', 'Расчет железобетонного каркаса', 'Подготовьте расчетную схему, сравните результаты ЛИРА-САПР и SCAD и оформите выводы.', ['ЛИРА-САПР', 'SCAD', 'СП и ГОСТ'], 'Кафедра строительных конструкций'),
            ('event', 'Семинар по СП и ГОСТ в проектной документации', 'Разбор типовых ошибок в разделах КР, АР и ПОС перед экспертизой.', ['СП и ГОСТ', 'Проектная документация'], 'Учебный офис МГСУ'),
            ('internship', 'Стажировка ГИС-аналитика городских данных', 'Анализируйте слои инфраструктуры, транспортной доступности и строительных площадок.', ['ГИС', 'Python', 'SQL'], 'Городские цифровые сервисы'),
            ('project', '4D-график строительства учебного корпуса', 'Свяжите календарный план с BIM-моделью и подготовьте визуальный сценарий строительства.', ['4D-планирование', 'Navisworks', 'Технология строительного производства'], 'Лаборатория BIM'),
            ('event', 'Карьерная встреча с Главгосэкспертизой', 'Эксперты расскажут, как проверяется проектная документация и какие навыки нужны выпускникам.', ['СП и ГОСТ', 'Проектная документация'], 'Карьерный центр МГСУ'),
            ('course', 'Безопасность и охрана труда на стройплощадке', 'Практический модуль для студентов, выходящих на производственную практику.', ['Охрана труда', 'Технология строительного производства'], 'Учебный центр МГСУ'),
        ])

    def _mai_opportunities(self, university, admin):
        self._opportunities(university, admin, [
            ('internship', 'Стажировка инженера БПЛА в лаборатории МАИ', 'Проектирование узлов БПЛА, подготовка 3D-моделей и участие в летных испытаниях.', ['Аэродинамика', 'CATIA', 'Компас-3D'], 'Лаборатория беспилотных систем МАИ'),
            ('project', 'Стенд телеметрии для учебного БПЛА', 'Соберите прототип обмена данными и визуализацию параметров полета.', ['C/C++', 'Python', 'Испытания и телеметрия'], 'Проектный офис МАИ'),
            ('course', 'MATLAB/Simulink для авиационных систем', 'Моделирование динамики и базовых контуров управления летательным аппаратом.', ['MATLAB/Simulink', 'Системная инженерия'], 'Институт систем управления МАИ'),
        ])

    def _opportunities(self, university, admin, items):
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
                        'location': 'Москва / кампус',
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
                opportunity.required_skills.update_or_create(
                    skill=requirement,
                    defaults={'required_level': 'intermediate', 'weight': 2},
                )

    def _mgsu_knowledge(self, university, admin):
        self._knowledge(university, admin, [
            ('Как оформить производственную практику в МГСУ', 'Подайте заявление в личном кабинете, согласуйте базу практики с кафедрой и загрузите договор до дедлайна учебного офиса.', 'Учебный офис МГСУ', ['all', 'students', 'практика']),
            ('Сроки производственной практики МГСУ', 'Для 3 курса основной период практики начинается летом; точные даты публикуются институтом и кафедрой в начале семестра.', 'Учебный офис МГСУ', ['students', 'практика']),
            ('Шаблон договора на практику', 'Используйте утвержденный шаблон договора МГСУ и проверяйте реквизиты организации до загрузки документа.', 'Юридический отдел', ['students', 'практика']),
            ('BIM-лаборатория МГСУ', 'BIM-лаборатория помогает студентам с Revit, Renga, Navisworks и цифровыми моделями учебных проектов.', 'Лаборатория BIM', ['students', 'BIM']),
            ('Доступ к Revit и Renga', 'Учебные лицензии и инструкции по установке выдаются через кафедру или цифровой сервис университета.', 'IT-поддержка МГСУ', ['all', 'students', 'BIM']),
            ('Консультация по сметному делу', 'Запишитесь на консультацию кафедры, если нужно разобрать локальную смету, объемы работ или нормативную базу.', 'Кафедра экономики строительства', ['students', 'сметное дело']),
            ('Карьерный центр МГСУ', 'Карьерный центр помогает с резюме, стажировками в строительных компаниях и встречами с работодателями Москвы.', 'Карьерный центр МГСУ', ['students', 'стажировки']),
            ('Проектная практика', 'Проектная практика может засчитываться через участие в утвержденном проекте с отчетом и отзывом руководителя.', 'Проектный офис МГСУ', ['практика', 'students']),
            ('Подтверждение навыков', 'Навык можно подтвердить сертификатом, проектом, оценкой по дисциплине или отзывом руководителя практики.', 'Карьерный центр МГСУ', ['students']),
            ('Выбор элективных дисциплин', 'Выбор элективов открывается в личном кабинете на ограниченный период перед началом семестра.', 'Учебный офис МГСУ', ['students']),
            ('Повышенная академическая стипендия', 'Заявка подается при наличии подтвержденных достижений в учебной, научной, общественной или спортивной деятельности.', 'Стипендиальная комиссия', ['students']),
            ('Социальная стипендия', 'Для социальной стипендии требуется документ, подтверждающий право на государственную социальную помощь.', 'Стипендиальная комиссия', ['students']),
            ('Воинский учет для студентов', 'Студенты предоставляют документы воинского учета в военно-учетный стол в течение двух недель после зачисления.', 'Военно-учетный стол', ['students']),
            ('Академический отпуск', 'Академический отпуск оформляется по заявлению с приложением подтверждающих документов и согласованием деканата.', 'Деканат', ['students']),
            ('Общежитие', 'Заявления на общежитие принимаются через электронную форму, приоритет зависит от категории студента и удаленности проживания.', 'Жилищная комиссия', ['students']),
            ('Студенческие проекты', 'Каталог проектов обновляется каждый месяц; студент может подать заявку в команду или предложить свою тему.', 'Проектный офис МГСУ', ['students', 'project']),
            ('Хакатоны университета', 'Хакатоны публикуются в разделе возможностей. Для участия нужна команда или индивидуальная регистрация.', 'Проектный офис МГСУ', ['students', 'хакатоны']),
            ('Пересдача экзамена', 'Пересдачи назначаются учебным офисом после публикации ведомости и заявления студента при необходимости.', 'Учебный офис МГСУ', ['students']),
            ('Индивидуальный учебный план', 'ИУП согласуется с руководителем программы и утверждается приказом после проверки академической разницы.', 'Учебный офис МГСУ', ['students']),
            ('Научный руководитель', 'Выбор научного руководителя оформляется через кафедру после предварительного согласования темы.', 'Кафедра', ['students']),
            ('Зачет волонтерской деятельности', 'Волонтерская деятельность учитывается при наличии подтверждений из официальной системы учета.', 'Воспитательный отдел', ['students']),
            ('Доступ к корпоративной почте', 'Корпоративная почта создается автоматически после зачисления и используется для официальных уведомлений.', 'IT-поддержка МГСУ', ['all', 'students']),
            ('Восстановление пароля', 'Пароль восстанавливается через единый аккаунт университета или через обращение в IT-поддержку.', 'IT-поддержка МГСУ', ['all']),
            ('MAX-уведомления', 'Если внешняя интеграция недоступна, уведомление сохраняется в UniPath MAX со статусом simulated или pending.', 'Цифровой кампус', ['all']),
        ])

    def _mai_knowledge(self, university, admin):
        self._knowledge(university, admin, [
            ('Правила проектной практики МАИ', 'Студент согласует тему проекта с кафедрой, регистрирует команду и загружает отчет после защиты.', 'Проектный офис МАИ', ['students', 'практика']),
            ('Лаборатории БПЛА МАИ', 'Лаборатории принимают студентов на проектные задачи по конструкции, авионике, телеметрии и испытаниям.', 'Институт авиационной техники', ['students']),
            ('Доступ к MATLAB/Simulink', 'Учебный доступ оформляется через цифровые сервисы МАИ или кафедрального администратора.', 'IT-служба МАИ', ['students']),
        ])

    def _knowledge(self, university, admin, topics):
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
        for topic in ['BIM', 'Revit', 'проектирование', 'стажировки', 'практика', 'сметное дело', 'геодезия']:
            Subscription.objects.get_or_create(
                student=student,
                topic=topic,
                defaults={'filters': {'topic': topic}, 'active': True},
            )

    def _slug(self, value):
        translit = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
            'ы': 'y', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        }
        chars = []
        for char in value.lower():
            if char in translit:
                chars.append(translit[char])
            elif char.isascii() and char.isalnum():
                chars.append(char)
            else:
                chars.append('-')
        return '-'.join(part for part in ''.join(chars).split('-') if part)
