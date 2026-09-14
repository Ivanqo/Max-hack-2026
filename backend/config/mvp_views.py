from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.analytics.models import AuditLog, InteractionEvent
from apps.careers.models import CareerRole, CareerRoleSkill, Skill
from apps.careers.services import CareerGPSService
from apps.knowledge.services import KnowledgeSearchService
from apps.knowledge.models import KnowledgeItem
from apps.notifications.services import get_notification_service
from apps.opportunities.models import Opportunity, SavedOpportunity
from apps.opportunities.services import OpportunityMatchingService
from apps.profiles.models import CareerGoal, StudentProfile
from apps.subscriptions.models import Subscription
from apps.universities.models import University


MANAGER_ROLES = ['editor', 'institute_admin', 'university_admin', 'organizer', 'admin']

DEMO_INSTITUTES = [
    {'id': 'cs', 'name': 'Institute of Computer Science', 'universityId': '1'},
    {'id': 'data', 'name': 'Institute of Data and AI', 'universityId': '1'},
    {'id': 'business', 'name': 'Institute of Product and Business', 'universityId': '1'},
]

DEMO_PROGRAMS = [
    {'id': '1', 'name': 'Software Engineering', 'instituteId': 'cs'},
    {'id': '2', 'name': 'Applied Data Analytics', 'instituteId': 'data'},
    {'id': '3', 'name': 'Digital Product Management', 'instituteId': 'business'},
]

DEMO_INTERESTS = [
    {'id': 'Backend', 'name': 'Backend'},
    {'id': 'AI', 'name': 'AI'},
    {'id': 'стажировки', 'name': 'Стажировки'},
    {'id': 'хакатоны', 'name': 'Хакатоны'},
    {'id': 'практика', 'name': 'Практика'},
    {'id': 'Data Analysis', 'name': 'Data Analysis'},
]


DEMO_COURSES = [
    {
        'id': 1,
        'title': 'Career GPS Foundations',
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
    return getattr(user, 'university', None) or 'Demo University'


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
    return {
        'id': str(item.id),
        'title': item.title,
        'company': audience.get('company', item.university),
        'description': item.description,
        'type': 'job' if item.type == 'vacancy' else item.type,
        'location': audience.get('location', item.university),
        'remote': bool(audience.get('remote', False)),
        'requirements': requirements,
        'status': 'active' if item.published else 'inactive',
        'deadline': item.deadline.isoformat() if item.deadline else item.updated_at.isoformat(),
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
    skills = [link.skill.name for link in role.required_skills.select_related('skill').all()]
    return {
        'id': str(role.id),
        'title': role.name,
        'description': role.description,
        'skills': skills,
        'avgSalary': 'Not specified',
        'demandLevel': 'high' if role.active else 'low',
        'educationPath': ['Build core skills', 'Complete relevant projects', 'Apply to matched opportunities'],
        'createdAt': role.created_at.isoformat(),
        'updatedAt': role.updated_at.isoformat(),
    }


def _serialize_knowledge(item):
    return {
        'id': str(item.id),
        'title': item.title,
        'content': item.content,
        'category': item.responsible_unit or 'General',
        'tags': item.audience or [],
        'summary': item.content[:220],
        'source': {
            'id': str(item.id),
            'name': item.responsible_unit or 'Verified university source',
            'url': item.source_url,
            'type': 'web' if item.source_url else 'database',
        },
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
        return Response([{'id': '1', 'name': 'Demo University'}])
    return Response([{'id': str(item.id), 'name': item.name} for item in items])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def institutes(request):
    university_id = request.query_params.get('universityId')
    if not university_id:
        return Response(DEMO_INSTITUTES)
    return Response([item for item in DEMO_INSTITUTES if item['universityId'] == university_id])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def interests(request):
    return Response(DEMO_INTERESTS)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def onboarding(request):
    university_id = request.data.get('universityId')
    university = University.objects.filter(id=university_id).first() if university_id else None
    university_name = university.name if university else _university(request.user)
    institute = next((item['name'] for item in DEMO_INSTITUTES if item['id'] == request.data.get('instituteId')), '')
    program = next((item['name'] for item in DEMO_PROGRAMS if item['id'] == request.data.get('courseId')), '')
    goal_text = (request.data.get('careerGoal') or 'Backend Developer').strip()
    goal, _ = CareerGoal.objects.get_or_create(
        name=goal_text[:255],
        defaults={'description': 'Career goal selected during onboarding.'},
    )

    request.user.university = university_name
    request.user.save(update_fields=['university'])
    StudentProfile.objects.update_or_create(
        user=request.user,
        defaults={
            'university': university_name,
            'institute': institute,
            'course': 3,
            'program': program,
            'interests': request.data.get('interests') or [],
            'career_goal': goal,
            'onboarding_completed': True,
        },
    )
    return Response({'completed': True})


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
    if item_type:
        db_type = 'vacancy' if item_type in ['job', 'full-time'] else item_type
        items = items.filter(type=db_type)

    min_match = int(request.query_params.get('minMatch') or 0)
    service = OpportunityMatchingService()
    data = []
    for item, match in service.rank_for_user(request.user, items):
        if match['score'] >= min_match:
            data.append(_serialize_opportunity(item, user=request.user, match=match))
    return Response(data)


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


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def student_subscriptions(request):
    if request.method == 'POST':
        subscription = Subscription.objects.create(
            student=request.user,
            topic=request.data.get('topic', 'Backend'),
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


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def admin_opportunities(request):
    if not _is_manager(request.user):
        return _forbidden()
    if request.method == 'GET':
        return Response(_opportunity_list(request.user))

    data = request.data
    item = Opportunity.objects.create(
        university=_university(request.user),
        type='vacancy' if data.get('type') == 'job' else data.get('type', 'internship'),
        title=data.get('title', ''),
        description=data.get('description', ''),
        requirements='\n'.join(data.get('requirements') or []),
        audience={
            'company': data.get('company', ''),
            'location': data.get('location', ''),
            'remote': data.get('remote', False),
        },
        verified_status='verified',
        published=data.get('status', 'active') == 'active',
        created_by=request.user,
    )
    _audit(request.user, 'create', 'opportunity', item.id, item.title)
    if item.published and item.verified_status == 'verified':
        get_notification_service().create_for_opportunity_subscriptions(item)
    return Response(_serialize_opportunity(item), status=status.HTTP_201_CREATED)


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
    item.type = 'vacancy' if data.get('type') == 'job' else data.get('type', item.type)
    item.title = data.get('title', item.title)
    item.description = data.get('description', item.description)
    item.requirements = '\n'.join(data.get('requirements') or [])
    item.audience = {
        'company': data.get('company', ''),
        'location': data.get('location', ''),
        'remote': data.get('remote', False),
    }
    item.published = data.get('status', 'active') == 'active'
    item.save()
    _audit(request.user, 'update', 'opportunity', item.id, item.title)
    if item.published and item.verified_status == 'verified':
        get_notification_service().create_for_opportunity_subscriptions(item)
    return Response(_serialize_opportunity(item))


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

    role = CareerRole.objects.create(
        university=_university(request.user),
        name=request.data.get('title', ''),
        description=request.data.get('description', ''),
        active=request.data.get('demandLevel', 'medium') != 'low',
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
    role.active = request.data.get('demandLevel', 'medium') != 'low'
    role.save()
    _replace_role_skills(role, request.data.get('skills') or [])
    _audit(request.user, 'update', 'career_role', role.id, role.name)
    return Response(_serialize_role(role))


def _replace_role_skills(role, skill_names):
    role.required_skills.all().delete()
    for name in [name for name in skill_names if name]:
        skill, _ = Skill.objects.get_or_create(
            university=role.university,
            name=name,
            defaults={'category': 'technical'},
        )
        CareerRoleSkill.objects.create(career_role=role, skill=skill, required_level=3, weight=1)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def knowledge(request):
    return Response(_knowledge_list(request.user))


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

    item = KnowledgeItem.objects.create(
        university=_university(request.user),
        title=request.data.get('title', ''),
        content=request.data.get('content', ''),
        source_url=request.data.get('sourceUrl', ''),
        responsible_unit=request.data.get('category', 'General'),
        audience=request.data.get('tags') or [],
        verified_status='verified',
        published=True,
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

    item.title = request.data.get('title', item.title)
    item.content = request.data.get('content', item.content)
    item.responsible_unit = request.data.get('category', item.responsible_unit)
    item.audience = request.data.get('tags') or []
    item.source_url = request.data.get('sourceUrl', item.source_url)
    item.save()
    _audit(request.user, 'update', 'knowledge', item.id, item.title)
    return Response(_serialize_knowledge(item))
