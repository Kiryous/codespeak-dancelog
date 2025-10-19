import pytest
from datetime import date, datetime
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django_app.models import Group, Pass, Teacher, Student, StudentVisit, Purchase


class TestTeacher(TestCase):
    """Unit tests for Teacher model"""

    def setUp(self):
        self.user_with_name = User.objects.create_user(
            username='teacher1',
            first_name='John',
            last_name='Smith'
        )
        self.user_without_name = User.objects.create_user(
            username='teacher2'
        )

    @pytest.mark.timeout(30)
    def test_str_with_full_name(self):
        """Test Teacher.__str__ with first and last name"""
        # kind: unit_tests, original method: django_app.models.Teacher.__str__
        teacher = Teacher.objects.create(user=self.user_with_name)
        expected = "John Smith"
        self.assertEqual(str(teacher), expected)

    @pytest.mark.timeout(30)
    def test_str_without_full_name(self):
        """Test Teacher.__str__ with username only"""
        # kind: unit_tests, original method: django_app.models.Teacher.__str__
        teacher = Teacher.objects.create(user=self.user_without_name)
        expected = "teacher2"
        self.assertEqual(str(teacher), expected)


class TestStudent(TestCase):
    """Unit tests for Student model"""

    def setUp(self):
        self.user_with_name = User.objects.create_user(
            username='student1',
            first_name='Jane',
            last_name='Doe'
        )
        self.user_without_name = User.objects.create_user(
            username='student2'
        )

        # Create test group and pass for get_active_passes tests
        self.group = Group.objects.create(
            name='Test Group',
            schedule=[{"day": "tue", "time": "19:30"}],
            duration='1hr',
            start_at=date.today(),
            location='Test Location'
        )
        self.pass_obj = Pass.objects.create(
            name='Test Pass',
            price=100.00,
            group=self.group,
            lessons_included=5
        )

    @pytest.mark.timeout(30)
    def test_str_with_full_name(self):
        """Test Student.__str__ with first and last name"""
        # kind: unit_tests, original method: django_app.models.Student.__str__
        student = Student.objects.create(user=self.user_with_name)
        expected = "Jane Doe"
        self.assertEqual(str(student), expected)

    @pytest.mark.timeout(30)
    def test_str_without_full_name(self):
        """Test Student.__str__ with username only"""
        # kind: unit_tests, original method: django_app.models.Student.__str__
        student = Student.objects.create(user=self.user_without_name)
        expected = "student2"
        self.assertEqual(str(student), expected)

    @pytest.mark.timeout(30)
    def test_get_active_passes_no_purchases(self):
        """Test Student.get_active_passes with no purchases"""
        # kind: unit_tests, original method: django_app.models.Student.get_active_passes
        student = Student.objects.create(user=self.user_with_name)
        active_passes = student.get_active_passes()
        self.assertEqual(len(active_passes), 0)

    @pytest.mark.timeout(30)
    def test_get_active_passes_unpaid_purchase(self):
        """Test Student.get_active_passes with unpaid purchase"""
        # kind: unit_tests, original method: django_app.models.Student.get_active_passes
        student = Student.objects.create(user=self.user_with_name)
        purchase = Purchase.objects.create(
            student=student,
            dance_pass=self.pass_obj
        )
        # Unpaid purchase should not appear in active passes
        active_passes = student.get_active_passes()
        self.assertEqual(len(active_passes), 0)

    @pytest.mark.timeout(30)
    def test_get_active_passes_paid_with_remaining_lessons(self):
        """Test Student.get_active_passes with paid purchase and remaining lessons"""
        # kind: unit_tests, original method: django_app.models.Student.get_active_passes
        student = Student.objects.create(user=self.user_with_name)
        purchase = Purchase.objects.create(
            student=student,
            dance_pass=self.pass_obj,
            paid_at=timezone.now()
        )

        active_passes = student.get_active_passes()
        self.assertEqual(len(active_passes), 1)

        active_pass = active_passes[0]
        self.assertEqual(active_pass['purchase'], purchase)
        self.assertEqual(active_pass['pass'], self.pass_obj)
        self.assertEqual(active_pass['remaining_lessons'], 5)
        self.assertEqual(active_pass['visits_used'], 0)

    @pytest.mark.timeout(30)
    def test_get_active_passes_with_visits(self):
        """Test Student.get_active_passes with some visits used"""
        # kind: unit_tests, original method: django_app.models.Student.get_active_passes
        student = Student.objects.create(user=self.user_with_name)
        purchase = Purchase.objects.create(
            student=student,
            dance_pass=self.pass_obj,
            paid_at=timezone.now()
        )

        # Add some visits
        StudentVisit.objects.create(
            student=student,
            group=self.group,
            date=date.today(),
            skipped=False
        )
        StudentVisit.objects.create(
            student=student,
            group=self.group,
            date=date.today(),
            skipped=True  # Skipped visits don't count
        )

        active_passes = student.get_active_passes()
        self.assertEqual(len(active_passes), 1)

        active_pass = active_passes[0]
        self.assertEqual(active_pass['remaining_lessons'], 4)  # 5 - 1 (non-skipped visit)
        self.assertEqual(active_pass['visits_used'], 1)

    @pytest.mark.timeout(30)
    def test_get_active_passes_exhausted(self):
        """Test Student.get_active_passes with all lessons used"""
        # kind: unit_tests, original method: django_app.models.Student.get_active_passes
        student = Student.objects.create(user=self.user_with_name)
        purchase = Purchase.objects.create(
            student=student,
            dance_pass=self.pass_obj,
            paid_at=timezone.now()
        )

        # Use all 5 lessons
        for i in range(5):
            StudentVisit.objects.create(
                student=student,
                group=self.group,
                date=date.today(),
                skipped=False
            )

        active_passes = student.get_active_passes()
        self.assertEqual(len(active_passes), 0)


class TestStudentVisit(TestCase):
    """Unit tests for StudentVisit model"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser')
        self.student = Student.objects.create(user=self.user)
        self.group = Group.objects.create(
            name='Test Group',
            schedule=[{"day": "tue", "time": "19:30"}],
            duration='1hr',
            start_at=date.today(),
            location='Test Location'
        )

    @pytest.mark.timeout(30)
    def test_str_attended(self):
        """Test StudentVisit.__str__ for attended visit"""
        # kind: unit_tests, original method: django_app.models.StudentVisit.__str__
        visit = StudentVisit.objects.create(
            student=self.student,
            group=self.group,
            date=date(2024, 1, 15),
            skipped=False
        )
        expected = f"{self.student} - Test Group on 2024-01-15 (Attended)"
        self.assertEqual(str(visit), expected)

    @pytest.mark.timeout(30)
    def test_str_skipped(self):
        """Test StudentVisit.__str__ for skipped visit"""
        # kind: unit_tests, original method: django_app.models.StudentVisit.__str__
        visit = StudentVisit.objects.create(
            student=self.student,
            group=self.group,
            date=date(2024, 1, 15),
            skipped=True
        )
        expected = f"{self.student} - Test Group on 2024-01-15 (Skipped)"
        self.assertEqual(str(visit), expected)


class TestPurchase(TestCase):
    """Unit tests for Purchase model"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser')
        self.student = Student.objects.create(user=self.user)
        self.group = Group.objects.create(
            name='Test Group',
            schedule=[{"day": "tue", "time": "19:30"}],
            duration='1hr',
            start_at=date.today(),
            location='Test Location'
        )
        self.pass_obj = Pass.objects.create(
            name='Test Pass',
            price=100.00,
            group=self.group,
            lessons_included=10
        )

    @pytest.mark.timeout(30)
    def test_str_paid(self):
        """Test Purchase.__str__ for paid purchase"""
        # kind: unit_tests, original method: django_app.models.Purchase.__str__
        purchase = Purchase.objects.create(
            student=self.student,
            dance_pass=self.pass_obj,
            paid_at=timezone.now()
        )
        expected = f"{self.student} - Test Pass (Paid)"
        self.assertEqual(str(purchase), expected)

    @pytest.mark.timeout(30)
    def test_str_unpaid(self):
        """Test Purchase.__str__ for unpaid purchase"""
        # kind: unit_tests, original method: django_app.models.Purchase.__str__
        purchase = Purchase.objects.create(
            student=self.student,
            dance_pass=self.pass_obj
        )
        expected = f"{self.student} - Test Pass (Unpaid)"
        self.assertEqual(str(purchase), expected)