import pytest
from django.core.management import call_command
from django.test import override_settings
from rest_framework.test import APIClient

from apps.notifications.models import Notification


@pytest.mark.django_db
@override_settings(USE_MOCK_MAX_CLIENT=True)
def test_demo_student_api_journey_smoke():
    call_command('seed_demo', verbosity=0)

    client = APIClient()
    login = client.post(
        '/api/auth/login/',
        {'email': 'student@demo.local', 'password': 'demo12345'},
        format='json',
    )
    assert login.status_code == 200
    assert login.data['user']['role'] == 'student'

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    gps = client.get('/api/student/career-gps')
    assert gps.status_code == 200
    assert 0 <= gps.data['currentScore'] <= gps.data['maxScore']
    assert gps.data['nextSteps']

    knowledge = client.get('/api/knowledge/search', {'q': 'практика'})
    assert knowledge.status_code == 200
    assert knowledge.data['found'] is True
    assert knowledge.data['results']

    opportunities = client.get('/api/student/opportunities')
    assert opportunities.status_code == 200
    assert opportunities.data
    assert 'matchPercentage' in opportunities.data[0]

    saved = client.post(f"/api/student/opportunities/{opportunities.data[0]['id']}/save")
    assert saved.status_code == 200
    assert saved.data == {'saved': True}

    subscriptions = client.post('/api/student/subscriptions', {'topic': 'DevOps'}, format='json')
    assert subscriptions.status_code == 201
    assert subscriptions.data['topic'] == 'DevOps'

    extra_subscription = client.post(
        '/api/student/subscriptions',
        {'topic': 'Observability'},
        format='json',
    )
    assert extra_subscription.status_code == 201

    admin_login = client.post(
        '/api/auth/login/',
        {'email': 'admin@demo.local', 'password': 'demo12345'},
        format='json',
    )
    assert admin_login.status_code == 200
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_login.data['access']}")
    published = client.post(
        '/api/admin/opportunities',
        {
            'type': 'internship',
            'title': 'Observability Internship',
            'description': 'Build dashboards and alerting for student services.',
            'requirements': ['Observability', 'Python'],
            'company': 'MAX Labs',
            'location': 'Campus',
            'remote': False,
            'status': 'active',
        },
        format='json',
    )
    assert published.status_code == 201
    notification = Notification.objects.get(
        student__email='student@demo.local',
        opportunity_id=published.data['id'],
    )
    assert notification.delivery_status == Notification.DeliveryStatus.SIMULATED
    assert notification.idempotency_key
