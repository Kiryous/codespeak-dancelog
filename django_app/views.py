from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Count, Prefetch
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
from django.forms import modelformset_factory

from .models import Group, Pass, Teacher, Student, StudentVisit, Purchase
from .forms import (
    GroupForm, StudentForm, PurchaseForm, StudentVisitFormSet,
    StudentSelectionForm, NewStudentForm
)


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'django_app/login.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    """Dashboard showing upcoming lessons for teachers"""
    today = timezone.now().date()

    # Get user's role
    is_teacher = hasattr(request.user, 'teacher')
    is_admin = request.user.is_staff or request.user.is_superuser

    if is_teacher:
        teacher = request.user.teacher
        groups = teacher.groups.filter(finished_at__isnull=True)
    else:
        groups = Group.objects.filter(finished_at__isnull=True)

    # Generate upcoming lessons based on schedule
    upcoming_lessons = []
    for group in groups:
        for schedule_item in group.schedule:
            # Calculate next occurrence of this lesson
            day_name = schedule_item['day']
            time_str = schedule_item['time']

            # Convert day name to weekday number
            day_mapping = {
                'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3,
                'fri': 4, 'sat': 5, 'sun': 6
            }
            target_weekday = day_mapping.get(day_name, 0)

            # Find next occurrence
            days_until = (target_weekday - today.weekday()) % 7
            if days_until == 0 and timezone.now().time() > timezone.datetime.strptime(time_str, '%H:%M').time():
                days_until = 7  # If today but time has passed, next week

            lesson_date = today + timedelta(days=days_until)

            # Only show lessons for next 2 weeks
            if lesson_date <= today + timedelta(days=14):
                upcoming_lessons.append({
                    'group': group,
                    'date': lesson_date,
                    'time': time_str,
                    'day': day_name,
                })

    # Sort by date and time
    upcoming_lessons.sort(key=lambda x: (x['date'], x['time']))

    context = {
        'upcoming_lessons': upcoming_lessons[:10],  # Show only next 10 lessons
        'is_teacher': is_teacher,
        'is_admin': is_admin,
    }
    return render(request, 'django_app/dashboard.html', context)


@login_required
def add_group(request):
    """Add a new group (admin only)"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Only administrators can add new groups.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Group created successfully.')
            return redirect('dashboard')
    else:
        form = GroupForm()

    return render(request, 'django_app/add_group.html', {'form': form})


@login_required
def lesson_detail(request, group_id, lesson_date):
    """Mark attendance for a specific lesson"""
    group = get_object_or_404(Group, id=group_id)
    lesson_date = datetime.strptime(lesson_date, '%Y-%m-%d').date()

    # Check if user is teacher of this group or admin
    is_teacher = hasattr(request.user, 'teacher') and group in request.user.teacher.groups.all()
    is_admin = request.user.is_staff or request.user.is_superuser

    if not (is_teacher or is_admin):
        messages.error(request, 'You do not have permission to mark attendance for this group.')
        return redirect('dashboard')

    # Get existing visits for this lesson
    existing_visits = StudentVisit.objects.filter(group=group, date=lesson_date)
    existing_student_ids = set(existing_visits.values_list('student_id', flat=True))

    # Get all students in this group
    group_students = group.students.all()

    if request.method == 'POST':
        # Handle attendance marking
        student_ids = request.POST.getlist('students')
        skipped_ids = request.POST.getlist('skipped')
        new_student_id = request.POST.get('new_student')

        with transaction.atomic():
            # Clear existing visits for this lesson
            existing_visits.delete()

            # Add new student if provided
            if new_student_id:
                student = get_object_or_404(Student, id=new_student_id)
                if student not in group_students:
                    group.students.add(student)
                student_ids.append(new_student_id)

            # Create new visits
            for student_id in student_ids:
                student = get_object_or_404(Student, id=student_id)
                is_skipped = student_id in skipped_ids
                StudentVisit.objects.create(
                    student=student,
                    group=group,
                    date=lesson_date,
                    skipped=is_skipped
                )

        messages.success(request, f'Attendance updated for {group.name} on {lesson_date}')
        return redirect('dashboard')

    # Get all students for adding new ones
    all_students = Student.objects.exclude(id__in=group_students.values_list('id', flat=True))

    context = {
        'group': group,
        'lesson_date': lesson_date,
        'group_students': group_students,
        'existing_visits': {v.student_id: v for v in existing_visits},
        'all_students': all_students,
    }
    return render(request, 'django_app/lesson_detail.html', context)


@login_required
def add_student(request):
    """Add a new student"""
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student added successfully.')
            return redirect('students')
    else:
        form = StudentForm()

    return render(request, 'django_app/add_student.html', {'form': form})


@login_required
def students(request):
    """List all students with their pass information"""
    students = Student.objects.select_related('user').prefetch_related(
        'purchases__pass_', 'groups'
    ).all()

    context = {
        'students': students,
    }
    return render(request, 'django_app/students.html', context)


@login_required
def student_detail(request, student_id):
    """Show student details and manage purchases"""
    student = get_object_or_404(Student, id=student_id)
    active_passes = student.get_active_passes()
    recent_visits = student.visits.select_related('group').order_by('-date')[:10]
    purchases = student.purchases.select_related('dance_pass', 'cashier__user').order_by('-created_at')

    context = {
        'student': student,
        'active_passes': active_passes,
        'recent_visits': recent_visits,
        'purchases': purchases,
    }
    return render(request, 'django_app/student_detail.html', context)


@login_required
def add_purchase(request, student_id):
    """Add a new purchase for a student"""
    student = get_object_or_404(Student, id=student_id)

    if request.method == 'POST':
        form = PurchaseForm(request.POST)
        if form.is_valid():
            purchase = form.save(commit=False)
            purchase.student = student
            if hasattr(request.user, 'teacher'):
                purchase.cashier = request.user.teacher

            # If payment method is provided, mark as paid immediately
            if form.cleaned_data['payment_method']:
                purchase.paid_at = timezone.now()

            purchase.save()
            messages.success(request, 'Purchase added successfully.')
            return redirect('student_detail', student_id=student.id)
    else:
        form = PurchaseForm()

    return render(request, 'django_app/add_purchase.html', {
        'form': form,
        'student': student
    })


@login_required
@require_POST
def mark_purchase_paid(request, purchase_id):
    """Mark a purchase as paid"""
    purchase = get_object_or_404(Purchase, id=purchase_id)

    if not purchase.paid_at:
        purchase.paid_at = timezone.now()
        purchase.payment_method = request.POST.get('payment_method', '')
        if hasattr(request.user, 'teacher'):
            purchase.cashier = request.user.teacher
        purchase.save()
        messages.success(request, 'Purchase marked as paid.')

    return redirect('student_detail', student_id=purchase.student.id)
