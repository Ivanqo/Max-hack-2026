from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.analytics.models import AuditLog, InteractionEvent
from apps.careers.models import CareerRole, CareerRoleSkill, Skill, StudentSkill
from apps.careers.services import CareerGPSService
from apps.knowledge.services import KnowledgeSearchService
from apps.knowledge.models import KnowledgeItem
from apps.notifications.services import get_notification_service
from apps.opportunities.models import Opportunity, OpportunitySkill, SavedOpportunity
from apps.opportunities.services import OpportunityMatchingService
from apps.profiles.models import CareerGoal, StudentProfile
from apps.subscriptions.models import Subscription
from apps.universities.models import University


MANAGER_ROLES = ['editor', 'institute_admin', 'university_admin', 'organizer', 'admin']

DEFAULT_UNIVERSITY_NAME = 'НИУ МГСУ'

DEMO_INSTITUTES_BY_UNIVERSITY = {
    'НИУ МГСУ': [
        {'id': 'mgsu-digital', 'name': 'Институт цифровых технологий и моделирования в строительстве'},
        {'id': 'mgsu-construction', 'name': 'Институт строительства и архитектуры'},
        {'id': 'mgsu-economics', 'name': 'Институт экономики, управления и коммуникаций в строительстве'},
    ],
    'МАИ': [
        {'id': 'mai-aviation', 'name': 'Институт авиационной техники'},
        {'id': 'mai-control', 'name': 'Институт систем управления, информатики и электроэнергетики'},
        {'id': 'mai-robotics', 'name': 'Институт робототехники и интеллектуальных систем'},
    ],
}

DEMO_PROGRAMS = [
    {'id': 'mgsu-bim', 'name': 'Цифровое строительство и BIM', 'instituteId': 'mgsu-digital'},
    {'id': 'mgsu-pgs', 'name': 'Промышленное и гражданское строительство', 'instituteId': 'mgsu-construction'},
    {'id': 'mgsu-estimate', 'name': 'Экономика и управление в строительстве', 'instituteId': 'mgsu-economics'},
    {'id': 'mai-uav', 'name': 'Проектирование беспилотных авиационных систем', 'instituteId': 'mai-aviation'},
    {'id': 'mai-avionics', 'name': 'Системы управления летательными аппаратами', 'instituteId': 'mai-control'},
    {'id': 'mai-embedded', 'name': 'Встроенные системы и робототехника', 'instituteId': 'mai-robotics'},
]

DEMO_INTERESTS = [
    {'id': 'BIM', 'name': 'BIM'},
    {'id': 'проектирование', 'name': 'Проектирование'},
    {'id': 'сметное дело', 'name': 'Сметное дело'},
    {'id': 'геодезия', 'name': 'Геодезия'},
    {'id': 'БПЛА', 'name': 'БПЛА'},
    {'id': 'авионика', 'name': 'Авионика'},
    {'id': 'стажировки', 'name': 'Стажировки'},
    {'id': 'практика', 'name': 'Практика'},
    {'id': 'хакатоны', 'name': 'Хакатоны'},
]

SKILL_LEVELS = {
    'beginner': 2,
    'intermediate': 3,
    'advanced': 4,
    'expert': 5,
}


DEMO_COURSES = [
    {
        'id': 1,
        'title': 'Основы карьерного планирования',
        'description': 'Learn how to map your skills to university career paths and opportunities.',
        'materials': [
            {'id': 1, 'title': 'Skills Map', 'type': 'article', 'content': 'List your strongest skills and connect them to roles.'},
            {'id': 2, 'title': 'Opportunity Checklist', 'type': 'guide', 'content': 'Compare internships, projects, and events by fit.'},
        ],
        'quizzes': [{'id': 1, 'title': 'Career Readiness Check', 'questions': [1, 2]}],
    },
    {
        'id': 2,
        'title': 'Finding Your First Internship',
        'description': 'A practical course on CVs, applications, and choosing early career opportunities.',
        'materials': [
            {'id': 3, 'title': 'CV Basics', 'type': 'article', 'content': 'Keep your first CV concise and project-focused.'},
        ],
        'quizzes': [{'id': 2, 'title': 'Internship Basics', 'questions': [3, 4]}],
    },
]

DEMO_QUIZZES = {
    1: {
        'id': 1,
        'courseId': 1,
        'title': 'Career Readiness Check',
        'questions': [
            {
                'id': 1,
                'text': 'What is the best first step when choosing a career role?',
                'options': [
                    {'id': 1, 'text': 'Compare the role with your skills'},
                    {'id': 2, 'text': 'Apply everywhere at random'},
                    {'id': 3, 'text': 'Ignore requirements'},
                ],
                'correctOptionId': 1,
            },
            {
                'id': 2,
                'text': 'Why save an opportunity?',
                'options': [
                    {'id': 4, 'text': 'To track it and return later'},
                    {'id': 5, 'text': 'To hide it from others'},
                    {'id': 6, 'text': 'To delete it'},
                ],
                'correctOptionId': 4,
            },
        ],
    },
    2: {
        'id': 2,
        'courseId': 2,
        'title': 'Internship Basics',
        'questions': [
            {
                'id': 3,
                'text': 'What should an entry-level CV emphasize?',
                'options': [
                    {'id': 7, 'text': 'Projects and skills'},
                    {'id': 8, 'text': 'Unrelated filler'},
                ],
                'correctOptionId': 7,
            },
            {
                'id': 4,
                'text': 'What makes an internship a good fit?',
                'options': [
                    {'id': 9, 'text': 'Relevant learning and requirements'},
                    {'id': 10, 'text': 'Only the longest description'},
                ],
                'correctOptionId': 9,
            },
        ],
    },
}


def _university(user):
    return getattr(user, 'university', None) or DEFAULT_UNIVERSITY_NAME


def _university_from_param(value, user=None):
    if value:
        university = University.objects.filter(id=value).first()
        if university:
            return university
    current_name = _university(user) if user else DEFAULT_UNIVERSITY_NAME
    return University.objects.filter(name=current_name).first()


def _institute_options(university_name, university_id=''):
    items = DEMO_INSTITUTES_BY_UNIVERSITY.get(
        university_name,
        DEMO_INSTITUTES_BY_UNIVERSITY[DEFAULT_UNIVERSITY_NAME],
    )
    return [
        {
            'id': item['id'],
            'name': item['name'],
            'universityId': str(university_id),
        }
        for item in items
    ]


def _institute_name(institute_id):
    for items in DEMO_INSTITUTES_BY_UNIVERSITY.values():
        for item in items:
            if item['id'] == institute_id:
                return item['name']
    return ''


def _program_name(program_id):
    program = next((item for item in DEMO_PROGRAMS if item['id'] == program_id), None)
    return program['name'] if program else ''


def _is_manager(user):
    return bool(
        user and
        user.is_authenticated and
        (user.is_staff or user.is_superuser or getattr(user, 'role', None) in MANAGER_ROLES)
    )


def _forbidden():
    return Response({'detail': 'Admin or editor role required.'}, status=status.HTTP_403_FORBIDDEN)


def _audit(user, action, entity_type, entity_id, title=''):
    AuditLog.objects.create(
        university=_university(user),
        admin=user,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        metadata={'title': title} if title else {},
    )


def _course(course_id):
    return next((course for course in DEMO_COURSES if course['id'] == course_id), None)


def _serialize_opportunity(item, user=None, match=None):
    audience = item.audience or {}
    requirements = [line.strip() for line in item.requirements.splitlines() if line.strip()]
    is_saved = False
    if user and user.is_authenticated and getattr(user, 'role', None) == 'student':
        is_saved = SavedOpportunity.objects.filter(student=user, opportunity=item).exists()
    skills = [
        {
            'name': link.skill,
            'level': OPPORTUNITY_SKILL_LEVELS_REVERSE.get(link.required_level, 3),
            'weight': link.weight,
        }
        for link in item.required_skills.all()
    ]
    return {
        'id': str(item.id),
        'title': item.title,
        'company': audience.get('company', item.university),
        'description': item.description,
        'type': item.type,
        'location': audience.get('location', item.university),
        'remote': bool(audience.get('remote', False)),
        'requirements': requirements,
        'skills': skills,
        'status': 'active' if item.published else 'inactive',
        'published': item.published,
        'verifiedStatus': item.verified_status,
        'deadline': item.deadline.isoformat() if item.deadline else None,
        'sourceUrl': item.source_url,
        'matchPercentage': match['score'] if match else 0,
        'matchReasons': match['reasons'] if match else [],
        'gaps': match['gaps'] if match else [],
        'isSaved': is_saved,
        'postedDate': item.created_at.isoformat(),
        'match': match['score'] if match else 0,
        'saved': is_saved,
        'createdAt': item.created_at.isoformat(),
        'updatedAt': item.updated_at.isoformat(),
    }


def _serialize_role(role):
    skills = [
        {'name': link.skill.name, 'level': link.required_level}
        for link in role.required_skills.select_related('skill').all()
    ]
    return {
        'id': str(role.id),
        'title': role.name,
        'description': role.description,
        'skills': [item['name'] for item in skills],
        'skillLevels': skills,
        'avgSalary': role.avg_salary,
        'demandLevel': role.demand_level,
        'active': role.active,
        'educationPath': role.education_path or [],
        'createdAt': role.created_at.isoformat(),
        'updatedAt': role.updated_at.isoformat(),
    }


def _serialize_student_skill(item):
    return {
        'id': str(item.id),
        'name': item.skill.name,
        'level': item.level,
        'levelLabel': _level_label(item.level),
        'verified': item.verified,
        'evidence': item.evidence or '',
    }


def _level_label(level):
    if level >= 5:
        return 'expert'
    if level >= 4:
        return 'advanced'
    if level >= 3:
        return 'intermediate'
    return 'beginner'


def _serialize_knowledge(item):
    return {
        'id': str(item.id),
        'title': item.title,
        'content': item.content,
        'category': item.responsible_unit or 'General',
        'responsibleUnit': item.responsible_unit,
        'audience': item.audience or [],
        'tags': item.audience or [],
        'summary': item.content[:220],
        'source': {
            'id': str(item.id),
            'name': item.responsible_unit or 'Verified university source',
            'url': item.source_url,
            'type': 'web' if item.source_url else 'database',
        },
        'sourceUrl': item.source_url,
        'published': item.published,
        'verified': item.verified_status == 'verified',
        'verifiedStatus': item.verified_status,
        'actualUntil': item.actual_until.isoformat() if item.actual_until else None,
        'createdAt': item.created_at.isoformat(),
        'updatedAt': item.updated_at.isoformat(),
    }


@api_view(['GET'])
@permission_classes([AllowAny])
def root_health(request):
    return Response({'status': 'ok', 'service': 'UniPath MAX API'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def universities(request):
    items = University.objects.all()
    if not items.exists():
        return Response([{'id': '1', 'name': DEFAULT_UNIVERSITY_NAME}])
    return Response([{'id': str(item.id), 'name': item.name} for item in items])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def institutes(request):
    university_id = request.query_params.get('universityId')
    university = _university_from_param(university_id, request.user)
    university_name = university.name if university else _university(request.user)
    resolved_id = university.id if university else university_id or ''
    return Response(_institute_options(university_name, resolved_id))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def interests(request):
    return Response(DEMO_INTERESTS)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def skills(request):
    queryset = Skill.objects.filter(
        Q(university=_university(request.user)) | Q(university__isnull=True)
    ).order_by('category', 'name')
    return Response([
        {
            'id': str(item.id),
            'name': item.name,
            'category': item.category,
        }
        for item in queryset
    ])


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def onboarding(request):
    university_id = request.data.get('universityId')
    university = University.objects.filter(id=university_id).first() if university_id else None
    university_name = university.name if university else _university(request.user)
    institute = _institute_name(request.data.get('instituteId'))
    program = _program_name(request.data.get('courseId'))
    goal_text = (request.data.get('careerGoal') or 'BIM-координатор в строительстве').strip()
    goal, _ = CareerGoal.objects.get_or_create(
        name=goal_text[:255],
        defaults={'description': 'Career goal selected during onboarding.'},
    )

    request.user.university = university_name
    request.user.save(update_fields=['university'])
    profile, _ = StudentProfile.objects.update_or_create(
        user=request.user,
        defaults={
            'university': university_name,
            'institute': institute,
            'course': _course_year(request.data.get('studyYear')),
            'program': program,
            'interests': request.data.get('interests') or [],
            'career_goal': goal,
            'onboarding_completed': True,
        },
    )
    _sync_student_skills(
        profile,
        _skill_specs(request.data.get('skills') or request.data.get('interests') or []),
    )
    return Response({'completed': True})


def _course_year(value):
    try:
        year = int(value)
    except (TypeError, ValueError):
        return None
    return year if 1 <= year <= 6 else None


def _skill_specs(items):
    specs = []
    for item in items:
        if isinstance(item, str):
            name = item.strip()
            level = 3
        elif isinstance(item, dict):
            name = str(item.get('name') or item.get('skill') or '').strip()
            raw_level = item.get('level', 3)
            level = SKILL_LEVELS.get(str(raw_level).lower(), raw_level)
        else:
            continue
        try:
            level = int(level)
        except (TypeError, ValueError):
            level = 3
        if name:
            specs.append({'name': name[:200], 'level': min(max(level, 1), 5)})
    return specs


def _sync_student_skills(profile, specs):
    names = [spec['name'] for spec in specs]
    if names:
        profile.skills.exclude(skill__name__in=names).delete()
    else:
        profile.skills.all().delete()
    for spec in specs:
        skill, _ = Skill.objects.get_or_create(
            university=profile.university,
            name=spec['name'],
            defaults={'category': 'technical'},
        )
        StudentSkill.objects.update_or_create(
            student=profile,
            skill=skill,
            defaults={'level': spec['level'], 'evidence': 'Declared during onboarding/profile update'},
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def programs(request):
    institute_id = request.query_params.get('instituteId')
    if not institute_id:
        return Response(DEMO_PROGRAMS)
    return Response([item for item in DEMO_PROGRAMS if item['instituteId'] == institute_id])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def courses(request):
    return Response(DEMO_COURSES)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def course_detail(request, course_id):
    course = _course(course_id)
    if not course:
        return Response({'detail': 'Course not found.'}, status=status.HTTP_404_NOT_FOUND)
    return Response(course)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enroll_course(request, course_id):
    course = _course(course_id)
    if not course:
        return Response({'detail': 'Course not found.'}, status=status.HTTP_404_NOT_FOUND)
    return Response({'id': course_id, 'course': course, 'status': 'active'}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def enrollments(request):
    return Response([
        {'id': 1, 'course': DEMO_COURSES[0], 'progress': 35, 'status': 'active'},
    ])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def quiz_detail(request, quiz_id):
    quiz = DEMO_QUIZZES.get(quiz_id)
    if not quiz:
        return Response({'detail': 'Quiz not found.'}, status=status.HTTP_404_NOT_FOUND)
    visible = {
        **quiz,
        'questions': [
            {key: value for key, value in question.items() if key != 'correctOptionId'}
            for question in quiz['questions']
        ],
    }
    return Response(visible)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_quiz(request, quiz_id):
    quiz = DEMO_QUIZZES.get(quiz_id)
    if not quiz:
        return Response({'detail': 'Quiz not found.'}, status=status.HTTP_404_NOT_FOUND)

    answers = {int(key): value for key, value in request.data.get('answers', {}).items()}
    correct = sum(
        1 for question in quiz['questions']
        if answers.get(question['id']) == question['correctOptionId']
    )
    total = len(quiz['questions'])
    return Response({
        'score': round((correct / total) * 100) if total else 0,
        'correctAnswers': correct,
        'totalQuestions': total,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_analytics(request):
    if not _is_manager(request.user):
        return _forbidden()
    User = get_user_model()
    today = timezone.now().date()
    university = _university(request.user)
    total_users = User.objects.filter(university=university).count()
    active_users = User.objects.filter(university=university, is_active=True).count()
    user_growth = [
        {
            'date': (today - timedelta(days=day)).isoformat(),
            'count': User.objects.filter(
                university=university,
                date_joined__date__lte=today - timedelta(days=day),
            ).count(),
        }
        for day in range(13, -1, -1)
    ]
    popular_roles = [
        {'role': item['name'], 'count': item['required_skills__count']}
        for item in CareerRole.objects.filter(university=university)
        .annotate(Count('required_skills'))
        .values('name', 'required_skills__count')[:10]
    ]
    events = InteractionEvent.objects.filter(university=university)
    top_queries = [
        {'query': row['metadata__query'], 'count': row['count']}
        for row in events.filter(event_type='knowledge_search')
        .exclude(metadata__query='')
        .values('metadata__query')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    ]
    unanswered = [
        {'query': row['metadata__query'], 'count': row['count']}
        for row in events.filter(event_type='knowledge_no_answer')
        .exclude(metadata__query='')
        .values('metadata__query')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    ]
    return Response({
        'totalUsers': total_users,
        'activeUsers': active_users,
        'totalOpportunities': Opportunity.objects.filter(university=university).count(),
        'totalKnowledgeBase': KnowledgeItem.objects.filter(university=university).count(),
        'publishedKnowledge': KnowledgeItem.objects.filter(university=university, published=True).count(),
        'activeOpportunities': Opportunity.objects.filter(university=university, published=True).count(),
        'userGrowth': user_growth,
        'popularRoles': popular_roles,
        'topSearchQueries': top_queries,
        'unansweredQueries': unanswered,
        'opportunityViews': events.filter(event_type='opportunity_open').count(),
        'opportunitySaves': events.filter(event_type='opportunity_save').count(),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def opportunities(request):
    return student_opportunities(request)


def _opportunity_list(user=None):
    items = Opportunity.objects.all().order_by('-updated_at')
    if user and not getattr(user, 'is_superuser', False):
        items = items.filter(university=_university(user))
    return [_serialize_opportunity(item, user=user) for item in items]


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_opportunities(request):
    university = _university(request.user)
    items = Opportunity.objects.filter(
        university=university,
        published=True,
        verified_status='verified',
    ).order_by('-updated_at')

    search = request.query_params.get('search', '').strip()
    if search:
        items = items.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(requirements__icontains=search)
        )

    item_type = request.query_params.get('type')
    if item_type and item_type in OPPORTUNITY_TYPES:
        items = items.filter(type=item_type)

    min_match = int(request.query_params.get('minMatch') or 0)
    service = OpportunityMatchingService()
    data = []
    for item, match in service.rank_for_user(request.user, items):
        if match['score'] >= min_match:
            data.append(_serialize_opportunity(item, user=request.user, match=match))
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_opportunity_detail(request, pk):
    try:
        item = Opportunity.objects.get(
            pk=pk,
            university=_university(request.user),
            published=True,
            verified_status='verified',
        )
    except Opportunity.DoesNotExist:
        return Response({'detail': 'Opportunity not found.'}, status=status.HTTP_404_NOT_FOUND)

    match = OpportunityMatchingService().calculate_for_user(request.user, item)
    InteractionEvent.objects.create(
        university=_university(request.user),
        user=request.user,
        event_type='opportunity_open',
        entity_type='opportunity',
        entity_id=str(item.id),
    )
    return Response(_serialize_opportunity(item, user=request.user, match=match))


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def student_save_opportunity(request, pk):
    try:
        item = Opportunity.objects.get(
            pk=pk,
            university=_university(request.user),
            published=True,
            verified_status='verified',
        )
    except Opportunity.DoesNotExist:
        return Response({'detail': 'Opportunity not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        SavedOpportunity.objects.filter(student=request.user, opportunity=item).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    SavedOpportunity.objects.get_or_create(student=request.user, opportunity=item)
    InteractionEvent.objects.create(
        university=_university(request.user),
        user=request.user,
        event_type='opportunity_save',
        entity_type='opportunity',
        entity_id=str(item.id),
    )
    return Response({'saved': True})


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def student_profile(request):
    profile = getattr(request.user, 'student_profile', None)
    if not profile:
        if request.method == 'GET':
            return Response({'detail': 'Profile not found.'}, status=status.HTTP_404_NOT_FOUND)
        profile = StudentProfile.objects.create(
            user=request.user,
            university=_university(request.user),
            onboarding_completed=False,
        )

    if request.method == 'PATCH':
        data = request.data
        request.user.first_name = data.get('firstName', request.user.first_name)
        request.user.last_name = data.get('lastName', request.user.last_name)
        request.user.university = data.get('university', request.user.university)
        request.user.save(update_fields=['first_name', 'last_name', 'university'])

        profile.university = data.get('university', profile.university)
        profile.institute = data.get('institute', profile.institute)
        profile.program = data.get('program', profile.program)
        if 'studyYear' in data:
            profile.course = _course_year(data.get('studyYear'))
        if 'interests' in data:
            profile.interests = data.get('interests') or []
        if data.get('careerGoal'):
            goal, _ = CareerGoal.objects.get_or_create(
                name=str(data['careerGoal'])[:255],
                defaults={'description': 'Career goal selected in profile.', 'is_active': True},
            )
            profile.career_goal = goal
        profile.save()
        if 'skills' in data:
            _sync_student_skills(profile, _skill_specs(data.get('skills') or []))

    return Response(_serialize_student_profile(request.user, profile))


def _serialize_student_profile(user, profile):
    skills = profile.skills.select_related('skill').order_by('-level', 'skill__name')
    subscriptions = Subscription.objects.filter(student=user).order_by('-updated_at')
    return {
        'user': {
            'id': user.id,
            'email': user.email,
            'firstName': user.first_name,
            'lastName': user.last_name,
            'name': user.get_full_name(),
            'role': user.role,
            'maxUserId': user.max_user_id,
        },
        'profile': {
            'university': profile.university,
            'institute': profile.institute,
            'program': profile.program,
            'studyYear': profile.course,
            'interests': profile.interests or [],
            'careerGoal': profile.career_goal.name if profile.career_goal else '',
            'onboardingCompleted': profile.onboarding_completed,
            'updatedAt': profile.updated_at.isoformat(),
        },
        'skills': [_serialize_student_skill(item) for item in skills],
        'subscriptions': [_serialize_subscription(item) for item in subscriptions],
    }


@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def student_subscriptions(request, subscription_id=None):
    if request.method == 'DELETE':
        if subscription_id is None:
            return Response({'detail': 'Subscription id is required.'}, status=status.HTTP_400_BAD_REQUEST)
        subscription = Subscription.objects.filter(student=request.user, id=subscription_id).first()
        if not subscription:
            return Response({'detail': 'Subscription not found.'}, status=status.HTTP_404_NOT_FOUND)
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    if request.method == 'POST':
        topic = str(request.data.get('topic') or '').strip()
        subscription = Subscription.objects.create(
            student=request.user,
            topic=topic or 'BIM',
            filters=request.data.get('filters') or {},
            active=request.data.get('active', True),
        )
        return Response(_serialize_subscription(subscription), status=status.HTTP_201_CREATED)

    items = Subscription.objects.filter(student=request.user).order_by('-updated_at')
    return Response([_serialize_subscription(item) for item in items])


def _serialize_subscription(item):
    return {
        'id': str(item.id),
        'name': item.topic,
        'type': 'active' if item.active else 'paused',
        'active': item.active,
        'topic': item.topic,
        'filters': item.filters,
        'lastUpdate': item.updated_at.isoformat(),
        'newItems': NotificationCount.for_subscription(item),
    }


class NotificationCount:
    @staticmethod
    def for_subscription(subscription):
        text = subscription.topic.lower()
        return Opportunity.objects.filter(
            university=subscription.student.university,
            published=True,
            verified_status='verified',
        ).filter(
            Q(title__icontains=text) |
            Q(description__icontains=text) |
            Q(requirements__icontains=text) |
            Q(type__icontains=text)
        ).count()


OPPORTUNITY_TYPES = {'internship', 'vacancy', 'project', 'hackathon', 'event', 'course'}
VERIFIED_STATUSES = {'pending', 'verified', 'rejected'}
OPPORTUNITY_SKILL_LEVELS = {1: 'beginner', 2: 'beginner', 3: 'intermediate', 4: 'advanced', 5: 'expert'}
OPPORTUNITY_SKILL_LEVELS_REVERSE = {'beginner': 2, 'intermediate': 3, 'advanced': 4, 'expert': 5}


def _parse_deadline(value):
    if not value:
        return None
    parsed = parse_datetime(value)
    if parsed is None:
        parsed_date = parse_date(value)
        if parsed_date is None:
            return None
        parsed = datetime.combine(parsed_date, datetime.min.time())
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def _replace_opportunity_skills(item, skills):
    item.required_skills.all().delete()
    for spec in skills:
        if isinstance(spec, str):
            name, level = spec.strip(), 3
        elif isinstance(spec, dict):
            name = str(spec.get('name') or '').strip()
            level = spec.get('level', 3)
        else:
            continue
        if not name:
            continue
        try:
            level = int(level)
        except (TypeError, ValueError):
            level = 3
        level = min(max(level, 1), 5)
        OpportunitySkill.objects.create(
            opportunity=item,
            skill=name[:200],
            required_level=OPPORTUNITY_SKILL_LEVELS.get(level, 'intermediate'),
            weight=1,
        )


def _resolve_published(data, fallback=False):
    """`published` is the canonical field; `status: active/inactive` is kept
    as a back-compat alias for older/contest API callers."""
    if 'published' in data:
        return bool(data.get('published'))
    if 'status' in data:
        return data.get('status') == 'active'
    return fallback


def _resolve_verified_status(data, fallback='verified'):
    value = data.get('verifiedStatus')
    return value if value in VERIFIED_STATUSES else fallback


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def admin_opportunities(request):
    if not _is_manager(request.user):
        return _forbidden()
    if request.method == 'GET':
        return Response(_opportunity_list(request.user))

    data = request.data
    opp_type = data.get('type', 'internship')
    item = Opportunity.objects.create(
        university=_university(request.user),
        type=opp_type if opp_type in OPPORTUNITY_TYPES else 'internship',
        title=data.get('title', ''),
        description=data.get('description', ''),
        requirements='\n'.join(data.get('requirements') or []),
        audience={
            'company': data.get('company', ''),
            'location': data.get('location', ''),
            'remote': bool(data.get('remote', False)),
        },
        deadline=_parse_deadline(data.get('deadline')),
        source_url=data.get('sourceUrl', ''),
        verified_status=_resolve_verified_status(data),
        published=_resolve_published(data, fallback=True),
        created_by=request.user,
    )
    _replace_opportunity_skills(item, data.get('skills') or [])
    _audit(request.user, 'create', 'opportunity', item.id, item.title)
    notifications = []
    if item.published and item.verified_status == 'verified':
        notifications = get_notification_service().create_for_opportunity_subscriptions(item)
    result = _serialize_opportunity(item)
    result['notificationDelivery'] = _notification_delivery_summary(notifications)
    return Response(result, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_opportunity_recipient_preview(request):
    """Preview the exact active subscription audience before publishing."""
    if not _is_manager(request.user):
        return _forbidden()

    data = request.data
    opportunity_type = data.get('type', 'internship')
    if opportunity_type not in OPPORTUNITY_TYPES:
        opportunity_type = 'internship'
    opportunity = Opportunity(
        university=_university(request.user),
        type=opportunity_type,
        title=str(data.get('title') or ''),
        description=str(data.get('description') or ''),
        requirements='\n'.join(data.get('requirements') or []) if isinstance(data.get('requirements'), list) else str(data.get('requirements') or ''),
        audience={
            'company': data.get('company', ''),
            'location': data.get('location', ''),
            'remote': bool(data.get('remote', False)),
        },
    )
    service = get_notification_service()
    subscriptions = service.matching_subscriptions(opportunity)
    recipients = {}
    for subscription in subscriptions:
        student = subscription.student
        recipient = recipients.setdefault(student.pk, {
            'id': student.pk,
            'name': student.get_full_name() or 'Студент',
            'maxLinked': bool(student.max_user_id),
            'subscriptions': [],
        })
        recipient['subscriptions'].append(subscription.topic)
    result = list(recipients.values())
    return Response({
        'recipientCount': len(result),
        'linkedCount': sum(1 for recipient in result if recipient['maxLinked']),
        'recipients': result,
    })


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def admin_opportunity_detail(request, pk):
    if not _is_manager(request.user):
        return _forbidden()
    try:
        item = Opportunity.objects.get(pk=pk, university=_university(request.user))
    except Opportunity.DoesNotExist:
        return Response({'detail': 'Opportunity not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        _audit(request.user, 'delete', 'opportunity', item.id, item.title)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    data = request.data
    opp_type = data.get('type', item.type)
    item.type = opp_type if opp_type in OPPORTUNITY_TYPES else item.type
    item.title = data.get('title', item.title)
    item.description = data.get('description', item.description)
    item.requirements = '\n'.join(data.get('requirements') or [])
    item.audience = {
        'company': data.get('company', ''),
        'location': data.get('location', ''),
        'remote': bool(data.get('remote', False)),
    }
    if 'deadline' in data:
        item.deadline = _parse_deadline(data.get('deadline'))
    item.source_url = data.get('sourceUrl', item.source_url)
    item.verified_status = _resolve_verified_status(data, item.verified_status)
    item.published = _resolve_published(data, item.published)
    item.save()
    if 'skills' in data:
        _replace_opportunity_skills(item, data.get('skills') or [])
    _audit(request.user, 'update', 'opportunity', item.id, item.title)
    notifications = []
    if item.published and item.verified_status == 'verified':
        notifications = get_notification_service().create_for_opportunity_subscriptions(item)
    result = _serialize_opportunity(item)
    result['notificationDelivery'] = _notification_delivery_summary(notifications)
    return Response(result)


def _notification_delivery_summary(notifications):
    """Return a compact, non-sensitive outcome summary for the admin UI."""
    statuses = [notification.delivery_status for notification in notifications]
    return {
        'recipientCount': len(notifications),
        'sentCount': statuses.count('sent'),
        'simulatedCount': statuses.count('simulated'),
        'failedCount': statuses.count('failed'),
        'pendingCount': statuses.count('pending'),
        'errors': sorted({
            notification.last_error[:160]
            for notification in notifications
            if notification.delivery_status == 'failed' and notification.last_error
        }),
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def career_roles(request):
    return Response(_career_role_list(request.user))


def _career_role_list(user=None):
    roles = CareerRole.objects.prefetch_related('required_skills__skill').order_by('name')
    if user and user.is_authenticated and not user.is_superuser:
        roles = roles.filter(university=_university(user))
    return [_serialize_role(role) for role in roles]


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_career_goals(request):
    return Response(_career_goal_options(request.user))


def _career_goal_options(user):
    roles = CareerRole.objects.filter(
        university=_university(user),
        active=True,
    ).order_by('name')
    return [
        {
            'id': role.id,
            'title': role.name,
            'description': role.description,
            'category': 'Career role',
        }
        for role in roles
    ]


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_career_analysis(request, role_id):
    try:
        profile = request.user.student_profile
        role = CareerRole.objects.prefetch_related('required_skills__skill').get(
            id=role_id,
            university=_university(request.user),
            active=True,
        )
    except (StudentProfile.DoesNotExist, CareerRole.DoesNotExist):
        return Response({'detail': 'Career profile not found.'}, status=status.HTTP_404_NOT_FOUND)

    return Response(_career_analysis_payload(profile, role))


def _career_analysis_payload(profile, role):
    result = CareerGPSService().calculate(profile, role)
    return {
        'goal': {
            'id': role.id,
            'title': role.name,
            'description': role.description,
            'category': 'Career role',
        },
        'readinessScore': result['readiness_score'],
        'strengths': result['strengths'],
        'gaps': [
            {
                'skill': gap['skill'],
                'currentLevel': gap['current_level'],
                'requiredLevel': gap['required_level'],
                'priority': gap['priority'],
            }
            for gap in result['gaps']
        ],
        'nextActions': [
            {'id': index + 1, 'title': title, 'type': 'resource', 'estimatedTime': '1-2 weeks', 'priority': index + 1}
            for index, title in enumerate(result['next_actions'])
        ],
        'lastUpdated': timezone.now().isoformat(),
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_career_gps(request):
    try:
        profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return Response({
            'currentScore': 0,
            'maxScore': 100,
            'recommendations': ['Заполните профиль, чтобы получить карьерный маршрут.'],
            'nextSteps': ['Пройти onboarding.'],
        })

    roles = CareerRole.objects.prefetch_related('required_skills__skill').filter(
        university=_university(request.user),
        active=True,
    ).order_by('name')
    role = None
    if profile.career_goal:
        role = roles.filter(name=profile.career_goal.name).first()
    role = role or roles.first()
    if not role:
        return Response({
            'currentScore': 0,
            'maxScore': 100,
            'recommendations': ['Выберите карьерную цель в профиле.'],
            'nextSteps': ['Пройти onboarding.'],
        })
    analysis = _career_analysis_payload(profile, role)
    return Response({
        'currentScore': analysis.get('readinessScore', 0),
        'maxScore': 100,
        'recommendations': analysis.get('strengths', [])[:3] or ['Добавьте навыки в профиль.'],
        'nextSteps': [item['title'] for item in analysis.get('nextActions', [])],
    })


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def admin_career_roles(request):
    if not _is_manager(request.user):
        return _forbidden()
    if request.method == 'GET':
        return Response(_career_role_list(request.user))

DEMAND_LEVELS = {'high', 'medium', 'low'}


def _demand_level(data, fallback='medium'):
    value = data.get('demandLevel', fallback)
    return value if value in DEMAND_LEVELS else fallback


def _education_path(data, fallback=None):
    value = data.get('educationPath', fallback)
    if value is None:
        return fallback or []
    return [str(step).strip() for step in value if str(step).strip()]


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def admin_career_roles(request):
    if not _is_manager(request.user):
        return _forbidden()
    if request.method == 'GET':
        return Response(_career_role_list(request.user))

    role = CareerRole.objects.create(
        university=_university(request.user),
        name=request.data.get('title', ''),
        description=request.data.get('description', ''),
        avg_salary=request.data.get('avgSalary', ''),
        demand_level=_demand_level(request.data),
        education_path=_education_path(request.data),
        active=request.data.get('active', True),
    )
    _replace_role_skills(role, request.data.get('skills') or [])
    _audit(request.user, 'create', 'career_role', role.id, role.name)
    return Response(_serialize_role(role), status=status.HTTP_201_CREATED)


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def admin_career_role_detail(request, pk):
    if not _is_manager(request.user):
        return _forbidden()
    try:
        role = CareerRole.objects.get(pk=pk, university=_university(request.user))
    except CareerRole.DoesNotExist:
        return Response({'detail': 'Role not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        _audit(request.user, 'delete', 'career_role', role.id, role.name)
        role.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    role.name = request.data.get('title', role.name)
    role.description = request.data.get('description', role.description)
    role.avg_salary = request.data.get('avgSalary', role.avg_salary)
    role.demand_level = _demand_level(request.data, role.demand_level)
    role.education_path = _education_path(request.data, role.education_path)
    role.active = request.data.get('active', role.active)
    role.save()
    if 'skills' in request.data:
        _replace_role_skills(role, request.data.get('skills') or [])
    _audit(request.user, 'update', 'career_role', role.id, role.name)
    return Response(_serialize_role(role))


def _replace_role_skills(role, skills):
    role.required_skills.all().delete()
    for spec in skills:
        if isinstance(spec, str):
            name, level = spec.strip(), 3
        elif isinstance(spec, dict):
            name = str(spec.get('name') or '').strip()
            level = spec.get('level', 3)
        else:
            continue
        if not name:
            continue
        try:
            level = int(level)
        except (TypeError, ValueError):
            level = 3
        level = min(max(level, 1), 5)
        skill, _ = Skill.objects.get_or_create(
            university=role.university,
            name=name,
            defaults={'category': 'technical'},
        )
        CareerRoleSkill.objects.create(career_role=role, skill=skill, required_level=level, weight=1)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def knowledge(request):
    return Response(_knowledge_list(request.user))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def knowledge_detail(request, pk):
    try:
        item = KnowledgeItem.objects.get(pk=pk, university=_university(request.user))
    except KnowledgeItem.DoesNotExist:
        return Response({'detail': 'Article not found.'}, status=status.HTTP_404_NOT_FOUND)
    if not _is_manager(request.user) and not (item.published and item.verified_status == 'verified'):
        return Response({'detail': 'Article not found.'}, status=status.HTTP_404_NOT_FOUND)
    InteractionEvent.objects.create(
        university=_university(request.user),
        user=request.user,
        event_type='knowledge_open',
        entity_type='knowledge',
        entity_id=str(item.id),
    )
    return Response(_serialize_knowledge(item))


def _knowledge_list(user=None):
    items = KnowledgeItem.objects.all().order_by('-updated_at')
    if user and user.is_authenticated and not user.is_superuser:
        items = items.filter(university=_university(user))
        if not _is_manager(user):
            items = items.filter(published=True, verified_status='verified')
    return [_serialize_knowledge(item) for item in items]


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def knowledge_search(request):
    result = KnowledgeSearchService().search(request.query_params.get('q', ''), request.user)
    if result.get('found') and result.get('answer'):
        answer = result['answer']
        result['results'] = [
            {
                'id': item['id'],
                'title': item['title'],
                'content': item['content'],
                'summary': item['content'][:220],
                'source': {
                    'id': item['id'],
                    'name': item['responsible_unit'] or 'Verified university source',
                    'url': item['source_url'],
                    'type': 'web' if item['source_url'] else 'database',
                },
                'verified': item['verified_status'] == 'verified',
                'relevanceScore': min(1, item['relevance_score'] / 10),
                'createdAt': answer['updated_at'],
                'updatedAt': item['updated_at'],
                'verifiedStatus': item['verified_status'],
                'actualUntil': item['actual_until'],
            }
            for item in result['results']
        ]
        result['total'] = len(result['results'])
    else:
        result['total'] = 0
    return Response(result)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def admin_knowledge(request):
    if not _is_manager(request.user):
        return _forbidden()
    if request.method == 'GET':
        return Response(_knowledge_list(request.user))

KNOWLEDGE_VERIFIED_STATUSES = {'draft', 'verified', 'outdated'}


def _knowledge_audience(data, fallback=None):
    value = data.get('audience', data.get('tags', fallback))
    if value is None:
        return fallback or []
    valid = set(KnowledgeItem.AUDIENCE_CHOICES)
    return [item for item in value if item in valid] or [
        item for item in value if isinstance(item, str) and item.strip()
    ]


def _parse_actual_until(value):
    if not value:
        return None
    return parse_date(value)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def admin_knowledge(request):
    if not _is_manager(request.user):
        return _forbidden()
    if request.method == 'GET':
        return Response(_knowledge_list(request.user))

    data = request.data
    verified_status = data.get('verifiedStatus', 'draft')
    item = KnowledgeItem.objects.create(
        university=_university(request.user),
        title=data.get('title', ''),
        content=data.get('content', ''),
        source_url=data.get('sourceUrl', ''),
        responsible_unit=data.get('category', 'General'),
        audience=_knowledge_audience(data),
        verified_status=verified_status if verified_status in KNOWLEDGE_VERIFIED_STATUSES else 'draft',
        published=bool(data.get('published', False)),
        actual_until=_parse_actual_until(data.get('actualUntil')),
        created_by=request.user,
    )
    _audit(request.user, 'create', 'knowledge', item.id, item.title)
    return Response(_serialize_knowledge(item), status=status.HTTP_201_CREATED)


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def admin_knowledge_detail(request, pk):
    if not _is_manager(request.user):
        return _forbidden()
    try:
        item = KnowledgeItem.objects.get(pk=pk, university=_university(request.user))
    except KnowledgeItem.DoesNotExist:
        return Response({'detail': 'Article not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        _audit(request.user, 'delete', 'knowledge', item.id, item.title)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    data = request.data
    verified_status = data.get('verifiedStatus', item.verified_status)
    item.title = data.get('title', item.title)
    item.content = data.get('content', item.content)
    item.responsible_unit = data.get('category', item.responsible_unit)
    item.audience = _knowledge_audience(data, item.audience)
    item.source_url = data.get('sourceUrl', item.source_url)
    item.verified_status = verified_status if verified_status in KNOWLEDGE_VERIFIED_STATUSES else item.verified_status
    item.published = bool(data.get('published', item.published))
    if 'actualUntil' in data:
        item.actual_until = _parse_actual_until(data.get('actualUntil'))
    item.save()
    _audit(request.user, 'update', 'knowledge', item.id, item.title)
    return Response(_serialize_knowledge(item))
