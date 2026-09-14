from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import InteractionEvent, AuditLog

User = get_user_model()


class InteractionEventModelTest(TestCase):
    """Tests for InteractionEvent model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

    def test_create_interaction_event_with_user(self):
        """Test creating an interaction event with a user."""
        event = InteractionEvent.objects.create(
            university='Test University',
            user=self.user,
            event_type='view',
            entity_type='opportunity',
            entity_id='123',
            metadata={'source': 'search'}
        )
        self.assertEqual(event.university, 'Test University')
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.event_type, 'view')
        self.assertEqual(event.entity_type, 'opportunity')
        self.assertEqual(event.entity_id, '123')
        self.assertIsNotNone(event.created_at)

    def test_create_anonymous_interaction_event(self):
        """Test creating an interaction event without a user (anonymous)."""
        event = InteractionEvent.objects.create(
            university='Test University',
            event_type='view',
            entity_type='page',
            metadata={'page': 'landing'}
        )
        self.assertIsNone(event.user)
        self.assertEqual(event.event_type, 'view')

    def test_interaction_event_string_representation(self):
        """Test string representation of InteractionEvent."""
        event = InteractionEvent.objects.create(
            university='Test University',
            user=self.user,
            event_type='save',
            entity_type='opportunity',
            entity_id='456'
        )
        str_repr = str(event)
        self.assertIn('test@example.com', str_repr)
        self.assertIn('save', str_repr)
        self.assertIn('opportunity:456', str_repr)

    def test_interaction_event_ordering(self):
        """Test that events are ordered by created_at descending."""
        event1 = InteractionEvent.objects.create(
            university='Test University',
            event_type='view'
        )
        event2 = InteractionEvent.objects.create(
            university='Test University',
            event_type='click'
        )
        events = InteractionEvent.objects.all()
        self.assertEqual(events[0], event2)
        self.assertEqual(events[1], event1)


class AuditLogModelTest(TestCase):
    """Tests for AuditLog model."""

    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            role='admin'
        )

    def test_create_audit_log(self):
        """Test creating an audit log entry."""
        log = AuditLog.objects.create(
            university='Test University',
            admin=self.admin,
            action='create',
            entity_type='opportunity',
            entity_id='789',
            metadata={'title': 'New Opportunity'}
        )
        self.assertEqual(log.university, 'Test University')
        self.assertEqual(log.admin, self.admin)
        self.assertEqual(log.action, 'create')
        self.assertEqual(log.entity_type, 'opportunity')
        self.assertEqual(log.entity_id, '789')
        self.assertIsNotNone(log.timestamp)

    def test_audit_log_with_null_admin(self):
        """Test creating an audit log with null admin (system action)."""
        log = AuditLog.objects.create(
            university='Test University',
            action='delete',
            entity_type='user',
            entity_id='100',
            metadata={'reason': 'auto-cleanup'}
        )
        self.assertIsNone(log.admin)

    def test_audit_log_string_representation(self):
        """Test string representation of AuditLog."""
        log = AuditLog.objects.create(
            university='Test University',
            admin=self.admin,
            action='verify',
            entity_type='opportunity',
            entity_id='999'
        )
        str_repr = str(log)
        self.assertIn('admin@example.com', str_repr)
        self.assertIn('verify', str_repr)
        self.assertIn('opportunity:999', str_repr)

    def test_audit_log_ordering(self):
        """Test that logs are ordered by timestamp descending."""
        log1 = AuditLog.objects.create(
            university='Test University',
            admin=self.admin,
            action='create',
            entity_type='opportunity',
            entity_id='1'
        )
        log2 = AuditLog.objects.create(
            university='Test University',
            admin=self.admin,
            action='update',
            entity_type='opportunity',
            entity_id='2'
        )
        logs = AuditLog.objects.all()
        self.assertEqual(logs[0], log2)
        self.assertEqual(logs[1], log1)
