from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Group, Pass, Teacher, Student, StudentVisit, Purchase


class TeacherInline(admin.StackedInline):
    model = Teacher
    can_delete = False
    verbose_name_plural = 'Teacher'


class StudentInline(admin.StackedInline):
    model = Student
    can_delete = False
    verbose_name_plural = 'Student'


class CustomUserAdmin(UserAdmin):
    inlines = (TeacherInline, StudentInline)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_at', 'finished_at', 'duration', 'get_teachers']
    list_filter = ['finished_at', 'start_at', 'teachers']
    search_fields = ['name', 'location']
    filter_horizontal = ['teachers']
    date_hierarchy = 'start_at'

    def get_teachers(self, obj):
        return ", ".join([str(teacher) for teacher in obj.teachers.all()])
    get_teachers.short_description = 'Teachers'


@admin.register(Pass)
class PassAdmin(admin.ModelAdmin):
    list_display = ['name', 'group', 'price', 'lessons_included', 'skips_included']
    list_filter = ['group']
    search_fields = ['name', 'group__name']


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'user__email', 'get_groups']
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'user__email']

    def get_groups(self, obj):
        return ", ".join([group.name for group in obj.groups.all()])
    get_groups.short_description = 'Groups'


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'user__email', 'phone', 'get_groups']
    list_filter = ['groups']
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'user__email', 'phone']
    filter_horizontal = ['groups']

    def get_groups(self, obj):
        return ", ".join([group.name for group in obj.groups.all()])
    get_groups.short_description = 'Groups'


@admin.register(StudentVisit)
class StudentVisitAdmin(admin.ModelAdmin):
    list_display = ['student', 'group', 'date', 'skipped']
    list_filter = ['group', 'skipped', 'date']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'group__name']
    date_hierarchy = 'date'


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['student', 'dance_pass', 'created_at', 'paid_at', 'payment_method', 'cashier']
    list_filter = ['payment_method', 'paid_at', 'dance_pass__group', 'cashier']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'dance_pass__name']
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'student__user', 'dance_pass__group', 'cashier__user'
        )
