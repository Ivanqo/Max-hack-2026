import pytest
from django.core.management import call_command
from rest_framework.test import APIClient


@pytest.mark.django_db
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
