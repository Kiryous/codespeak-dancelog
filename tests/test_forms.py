import json
import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from django.forms import ValidationError
from django_app.forms import GroupForm, StudentForm, PurchaseForm, StudentVisitForm, NewStudentForm
from django_app.models import Group, Student, Teacher, Pass, StudentVisit


class TestGroupForm(TestCase):
    """Unit tests for GroupForm"""

    @pytest.mark.timeout(30)
    def test_clean_schedule_valid_json_string(self):
        """Test GroupForm.clean_schedule with valid JSON string"""
        # kind: unit_tests, original method: django_app.forms.GroupForm.clean_schedule
        # This specifically tests line 24: schedule = json.loads(schedule)
        form_data = {
            'name': 'Test Group',
            'schedule': '[{"day": "tue", "time": "19:30"}, {"day": "thu", "time": "20:30"}]',
            'duration': '1hr',
            'start_at': '2024-01-01',
            'location': 'Test Location'
        }
        form = GroupForm(data=form_data)
        # Access cleaned_data to trigger clean_schedule
        form.is_valid()
        cleaned_schedule = form.cleaned_data['schedule']

        expected = [{"day": "tue", "time": "19:30"}, {"day": "thu", "time": "20:30"}]
        self.assertEqual(cleaned_schedule, expected)

    @pytest.mark.timeout(30)
    def test_clean_schedule_invalid_json_direct(self):
        """Test GroupForm.clean_schedule with invalid JSON - direct method call"""
        # kind: unit_tests, original method: django_app.forms.GroupForm.clean_schedule
        # Test line 42 directly by calling clean_schedule method
        form = GroupForm()
        form.cleaned_data = {'schedule': '{invalid json syntax'}

        with self.assertRaises(ValidationError) as cm:
            form.clean_schedule()

        self.assertIn('Schedule must be valid JSON', str(cm.exception))

    @pytest.mark.timeout(30)
    def test_clean_schedule_not_list(self):
        """Test GroupForm.clean_schedule with valid JSON but not a list"""
        # kind: unit_tests, original method: django_app.forms.GroupForm.clean_schedule
        form_data = {
            'name': 'Test Group',
            'schedule': '{"day": "tue", "time": "19:30"}',
            'duration': '1hr',
            'start_at': '2024-01-01',
            'location': 'Test Location'
        }
        form = GroupForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('schedule', form.errors)
        self.assertIn('Schedule must be a list', form.errors['schedule'][0])

    @pytest.mark.timeout(30)
    def test_clean_schedule_invalid_day(self):
        """Test GroupForm.clean_schedule with invalid day"""
        # kind: unit_tests, original method: django_app.forms.GroupForm.clean_schedule
        form_data = {
            'name': 'Test Group',
            'schedule': '[{"day": "invalid", "time": "19:30"}]',
            'duration': '1hr',
            'start_at': '2024-01-01',
            'location': 'Test Location'
        }
        form = GroupForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('schedule', form.errors)
        self.assertIn('Invalid day: invalid', form.errors['schedule'][0])

    @pytest.mark.timeout(30)
    def test_clean_schedule_already_list(self):
        """Test GroupForm.clean_schedule when schedule is already a list"""
        # kind: unit_tests, original method: django_app.forms.GroupForm.clean_schedule
        # This tests when isinstance(schedule, str) is False
        form = GroupForm()
        form.cleaned_data = {
            'schedule': [{"day": "tue", "time": "19:30"}]  # Already a list
        }
        cleaned_schedule = form.clean_schedule()
        expected = [{"day": "tue", "time": "19:30"}]
        self.assertEqual(cleaned_schedule, expected)

    @pytest.mark.timeout(30)
    def test_clean_schedule_json_parse_string(self):
        """Test GroupForm.clean_schedule JSON parsing of string"""
        # kind: unit_tests, original method: django_app.forms.GroupForm.clean_schedule
        # This specifically tests line 24: schedule = json.loads(schedule)
        form = GroupForm()
        form.cleaned_data = {
            'schedule': '[{"day": "tue", "time": "19:30"}]'  # String that needs parsing
        }
        cleaned_schedule = form.clean_schedule()
        expected = [{"day": "tue", "time": "19:30"}]
        self.assertEqual(cleaned_schedule, expected)

    @pytest.mark.timeout(30)
    def test_clean_schedule_missing_keys(self):
        """Test GroupForm.clean_schedule with missing day or time keys"""
        # kind: unit_tests, original method: django_app.forms.GroupForm.clean_schedule
        form_data = {
            'name': 'Test Group',
            'schedule': '[{"day": "tue"}]',  # Missing 'time' key
            'duration': '1hr',
            'start_at': '2024-01-01',
            'location': 'Test Location'
        }
        form = GroupForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('schedule', form.errors)
        self.assertIn("must have 'day' and 'time' keys", form.errors['schedule'][0])


class TestStudentForm(TestCase):
    """Unit tests for StudentForm"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
        self.student = Student.objects.create(user=self.user, phone='1234567890')

    @pytest.mark.timeout(30)
    def test_init_new_student(self):
        """Test StudentForm.__init__ for new student"""
        # kind: unit_tests, original method: django_app.forms.StudentForm.__init__
        form = StudentForm()

        # For new students, fields should be empty
        self.assertIsNone(form.fields['first_name'].initial)
        self.assertIsNone(form.fields['last_name'].initial)
        self.assertIsNone(form.fields['email'].initial)
        self.assertIsNone(form.fields['username'].initial)

    @pytest.mark.timeout(30)
    def test_init_existing_student(self):
        """Test StudentForm.__init__ for existing student"""
        # kind: unit_tests, original method: django_app.forms.StudentForm.__init__
        form = StudentForm(instance=self.student)

        # For existing students, fields should be populated from user
        self.assertEqual(form.fields['first_name'].initial, 'Test')
        self.assertEqual(form.fields['last_name'].initial, 'User')
        self.assertEqual(form.fields['email'].initial, 'test@example.com')
        self.assertEqual(form.fields['username'].initial, 'testuser')

    @pytest.mark.timeout(30)
    def test_save_new_student(self):
        """Test StudentForm.save for new student"""
        # kind: unit_tests, original method: django_app.forms.StudentForm.save
        form_data = {
            'first_name': 'New',
            'last_name': 'Student',
            'email': 'new@example.com',
            'username': 'newstudent',
            'phone': '9876543210',
            'notes': 'Test notes'
        }
        form = StudentForm(data=form_data)
        self.assertTrue(form.is_valid())

        student = form.save()

        # Verify student was created
        self.assertIsInstance(student, Student)
        self.assertEqual(student.user.first_name, 'New')
        self.assertEqual(student.user.last_name, 'Student')
        self.assertEqual(student.user.email, 'new@example.com')
        self.assertEqual(student.user.username, 'newstudent')
        self.assertEqual(student.phone, '9876543210')

    @pytest.mark.timeout(30)
    def test_save_existing_student(self):
        """Test StudentForm.save for existing student"""
        # kind: unit_tests, original method: django_app.forms.StudentForm.save
        form_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com',
            'username': 'updateduser',
            'phone': '5555555555',
            'notes': 'Updated notes'
        }
        form = StudentForm(data=form_data, instance=self.student)
        self.assertTrue(form.is_valid())

        student = form.save()

        # Verify student was updated
        self.assertEqual(student.id, self.student.id)
        self.assertEqual(student.user.first_name, 'Updated')
        self.assertEqual(student.user.last_name, 'Name')
        self.assertEqual(student.user.email, 'updated@example.com')
        self.assertEqual(student.user.username, 'updateduser')
        self.assertEqual(student.phone, '5555555555')


class TestPurchaseForm(TestCase):
    """Unit tests for PurchaseForm"""

    def setUp(self):
        self.group = Group.objects.create(
            name='Test Group',
            schedule=[{"day": "tue", "time": "19:30"}],
            duration='1hr',
            start_at='2024-01-01',
            location='Test Location'
        )
        self.pass_obj = Pass.objects.create(
            name='Test Pass',
            price=100.00,
            group=self.group,
            lessons_included=10
        )

    @pytest.mark.timeout(30)
    def test_init_filters_active_passes(self):
        """Test PurchaseForm.__init__ filters to active group passes"""
        # kind: unit_tests, original method: django_app.forms.PurchaseForm.__init__
        form = PurchaseForm()

        # Should include passes from active groups (finished_at is null)
        self.assertIn(self.pass_obj, form.fields['dance_pass'].queryset)

        # Mark group as finished
        self.group.finished_at = '2024-12-01'
        self.group.save()

        # Create new form
        form = PurchaseForm()

        # Should not include passes from finished groups
        self.assertNotIn(self.pass_obj, form.fields['dance_pass'].queryset)


class TestStudentVisitForm(TestCase):
    """Unit tests for StudentVisitForm"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com')
        self.student = Student.objects.create(user=self.user)

    @pytest.mark.timeout(30)
    def test_init_hides_student_field(self):
        """Test StudentVisitForm.__init__ makes student field hidden"""
        # kind: unit_tests, original method: django_app.forms.StudentVisitForm.__init__
        form = StudentVisitForm()

        # Student field should be hidden
        from django import forms
        self.assertIsInstance(form.fields['student'].widget, forms.HiddenInput)


class TestNewStudentForm(TestCase):
    """Unit tests for NewStudentForm"""

    @pytest.mark.timeout(30)
    def test_save_creates_user_and_student(self):
        """Test NewStudentForm.save creates both User and Student"""
        # kind: unit_tests, original method: django_app.forms.NewStudentForm.save
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'phone': '1234567890'
        }
        form = NewStudentForm(data=form_data)
        self.assertTrue(form.is_valid())

        student = form.save()

        # Verify both user and student were created
        self.assertIsInstance(student, Student)
        self.assertEqual(student.user.first_name, 'John')
        self.assertEqual(student.user.last_name, 'Doe')
        self.assertEqual(student.user.email, 'john@example.com')
        self.assertEqual(student.user.username, 'john@example.com')
        self.assertEqual(student.phone, '1234567890')

        # Verify user was created in database
        user = User.objects.get(username='john@example.com')
        self.assertEqual(user.email, 'john@example.com')