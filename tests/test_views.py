import pytest
from datetime import date, datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from freezegun import freeze_time
from django_app.models import Group, Pass, Teacher, Student, StudentVisit, Purchase


class TestViews(TestCase):
    """Endpoint tests for views"""

    def setUp(self):
        self.client = Client()

        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )

        self.teacher_user = User.objects.create_user(
            username='teacher',
            password='testpass123',
            first_name='John',
            last_name='Teacher'
        )
        self.teacher = Teacher.objects.create(user=self.teacher_user)

        self.student_user = User.objects.create_user(
            username='student',
            password='testpass123',
            first_name='Jane',
            last_name='Student'
        )
        self.student = Student.objects.create(user=self.student_user, phone='1234567890')

        # Create test group and pass
        self.group = Group.objects.create(
            name='Test Group',
            schedule=[{"day": "tue", "time": "19:30"}],
            duration='1hr',
            start_at=date.today(),
            location='Test Location'
        )
        self.group.teachers.add(self.teacher)

        self.pass_obj = Pass.objects.create(
            name='Test Pass',
            price=100.00,
            group=self.group,
            lessons_included=10
        )

    @pytest.mark.timeout(30)
    def test_login_view_get(self):
        """Test login_view GET request"""
        # kind: endpoint_tests, original method: django_app.views.login_view
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'login')

    @pytest.mark.timeout(30)
    def test_login_view_post_valid(self):
        """Test login_view POST with valid credentials"""
        # kind: endpoint_tests, original method: django_app.views.login_view
        response = self.client.post(reverse('login'), {
            'username': 'admin',
            'password': 'testpass123'
        })
        self.assertRedirects(response, reverse('dashboard'))

    @pytest.mark.timeout(30)
    def test_login_view_post_invalid(self):
        """Test login_view POST with invalid credentials"""
        # kind: endpoint_tests, original method: django_app.views.login_view
        response = self.client.post(reverse('login'), {
            'username': 'admin',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password')

    @pytest.mark.timeout(30)
    def test_logout_view(self):
        """Test logout_view"""
        # kind: endpoint_tests, original method: django_app.views.logout_view
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))

    @pytest.mark.timeout(30)
    def test_logout_view_requires_login(self):
        """Test logout_view requires login"""
        # kind: endpoint_tests, original method: django_app.views.logout_view
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, '/login/?next=/logout/')

    @pytest.mark.timeout(30)
    @freeze_time("2024-01-15")  # Monday
    def test_dashboard_admin_view(self):
        """Test dashboard view for admin user"""
        # kind: endpoint_tests, original method: django_app.views.dashboard
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')

    @pytest.mark.timeout(30)
    def test_dashboard_teacher_view(self):
        """Test dashboard view for teacher user"""
        # kind: endpoint_tests, original method: django_app.views.dashboard
        self.client.login(username='teacher', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')

    @pytest.mark.timeout(30)
    def test_dashboard_requires_login(self):
        """Test dashboard requires login"""
        # kind: endpoint_tests, original method: django_app.views.dashboard
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, '/login/?next=/')

    @pytest.mark.timeout(30)
    def test_add_group_admin_get(self):
        """Test add_group GET request as admin"""
        # kind: endpoint_tests, original method: django_app.views.add_group
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('add_group'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add Group')

    @pytest.mark.timeout(30)
    def test_add_group_admin_post_valid(self):
        """Test add_group POST with valid data as admin"""
        # kind: endpoint_tests, original method: django_app.views.add_group
        self.client.login(username='admin', password='testpass123')
        response = self.client.post(reverse('add_group'), {
            'name': 'New Group',
            'schedule': '[{"day": "mon", "time": "18:00"}]',
            'duration': '1hr',
            'start_at': '2024-02-01',
            'location': 'New Location'
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(Group.objects.filter(name='New Group').exists())

    @pytest.mark.timeout(30)
    def test_add_group_non_admin_forbidden(self):
        """Test add_group forbidden for non-admin users"""
        # kind: endpoint_tests, original method: django_app.views.add_group
        self.client.login(username='teacher', password='testpass123')
        response = self.client.get(reverse('add_group'))
        self.assertRedirects(response, reverse('dashboard'))

    @pytest.mark.timeout(30)
    def test_lesson_detail_teacher_get(self):
        """Test lesson_detail GET request as teacher"""
        # kind: endpoint_tests, original method: django_app.views.lesson_detail
        self.client.login(username='teacher', password='testpass123')
        response = self.client.get(reverse('lesson_detail', kwargs={
            'group_id': self.group.id,
            'lesson_date': '2024-01-15'
        }))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Group')

    @pytest.mark.timeout(30)
    def test_lesson_detail_admin_get(self):
        """Test lesson_detail GET request as admin"""
        # kind: endpoint_tests, original method: django_app.views.lesson_detail
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('lesson_detail', kwargs={
            'group_id': self.group.id,
            'lesson_date': '2024-01-15'
        }))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Group')

    @pytest.mark.timeout(30)
    def test_lesson_detail_unauthorized(self):
        """Test lesson_detail unauthorized access"""
        # kind: endpoint_tests, original method: django_app.views.lesson_detail
        other_user = User.objects.create_user(username='other', password='testpass123')
        Teacher.objects.create(user=other_user)

        self.client.login(username='other', password='testpass123')
        response = self.client.get(reverse('lesson_detail', kwargs={
            'group_id': self.group.id,
            'lesson_date': '2024-01-15'
        }))
        self.assertRedirects(response, reverse('dashboard'))

    @pytest.mark.timeout(30)
    def test_add_student_get(self):
        """Test add_student GET request"""
        # kind: endpoint_tests, original method: django_app.views.add_student
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('add_student'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add Student')

    @pytest.mark.timeout(30)
    def test_add_student_post_valid(self):
        """Test add_student POST with valid data"""
        # kind: endpoint_tests, original method: django_app.views.add_student
        self.client.login(username='admin', password='testpass123')
        response = self.client.post(reverse('add_student'), {
            'first_name': 'New',
            'last_name': 'Student',
            'email': 'new@example.com',
            'phone': '9876543210',
            'notes': 'Test notes'
        })
        self.assertRedirects(response, reverse('students'))
        self.assertTrue(User.objects.filter(email='new@example.com').exists())

    @pytest.mark.timeout(30)
    def test_students_view(self):
        """Test students list view"""
        # kind: endpoint_tests, original method: django_app.views.students
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('students'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Jane Student')

    @pytest.mark.timeout(30)
    def test_student_detail_view(self):
        """Test student_detail view"""
        # kind: endpoint_tests, original method: django_app.views.student_detail
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('student_detail', kwargs={'student_id': self.student.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Jane Student')

    @pytest.mark.timeout(30)
    def test_add_purchase_get(self):
        """Test add_purchase GET request"""
        # kind: endpoint_tests, original method: django_app.views.add_purchase
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('add_purchase', kwargs={'student_id': self.student.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add Purchase')

    @pytest.mark.timeout(30)
    def test_add_purchase_post_valid(self):
        """Test add_purchase POST with valid data"""
        # kind: endpoint_tests, original method: django_app.views.add_purchase
        self.client.login(username='admin', password='testpass123')
        response = self.client.post(reverse('add_purchase', kwargs={'student_id': self.student.id}), {
            'dance_pass': self.pass_obj.id,
            'payment_method': 'CASH',
            'notes': 'Test purchase'
        })
        self.assertRedirects(response, reverse('student_detail', kwargs={'student_id': self.student.id}))

        # Verify purchase was created and marked as paid
        purchase = Purchase.objects.filter(student=self.student).first()
        self.assertIsNotNone(purchase)
        self.assertIsNotNone(purchase.paid_at)

    @pytest.mark.timeout(30)
    def test_mark_purchase_paid(self):
        """Test mark_purchase_paid view"""
        # kind: endpoint_tests, original method: django_app.views.mark_purchase_paid
        purchase = Purchase.objects.create(
            student=self.student,
            dance_pass=self.pass_obj
        )

        self.client.login(username='admin', password='testpass123')
        response = self.client.post(reverse('mark_purchase_paid', kwargs={'purchase_id': purchase.id}), {
            'payment_method': 'TBC'
        })
        self.assertRedirects(response, reverse('student_detail', kwargs={'student_id': self.student.id}))

        # Verify purchase was marked as paid
        purchase.refresh_from_db()
        self.assertIsNotNone(purchase.paid_at)
        self.assertEqual(purchase.payment_method, 'TBC')

    @pytest.mark.timeout(30)
    def test_mark_purchase_paid_already_paid(self):
        """Test mark_purchase_paid for already paid purchase"""
        # kind: endpoint_tests, original method: django_app.views.mark_purchase_paid
        original_paid_at = timezone.now()
        purchase = Purchase.objects.create(
            student=self.student,
            dance_pass=self.pass_obj,
            paid_at=original_paid_at
        )

        self.client.login(username='admin', password='testpass123')
        response = self.client.post(reverse('mark_purchase_paid', kwargs={'purchase_id': purchase.id}), {
            'payment_method': 'TBC'
        })
        self.assertRedirects(response, reverse('student_detail', kwargs={'student_id': self.student.id}))

        # Verify paid_at timestamp wasn't changed
        purchase.refresh_from_db()
        self.assertEqual(purchase.paid_at, original_paid_at)