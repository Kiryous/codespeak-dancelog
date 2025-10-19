from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


class Group(models.Model):
    DAYS_OF_WEEK = [
        ('mon', 'Monday'),
        ('tue', 'Tuesday'),
        ('wed', 'Wednesday'),
        ('thu', 'Thursday'),
        ('fri', 'Friday'),
        ('sat', 'Saturday'),
        ('sun', 'Sunday'),
    ]

    name = models.CharField(max_length=100)
    schedule = models.JSONField(help_text="List of schedule entries, each with 'day' and 'time' keys")
    duration = models.CharField(max_length=20, help_text="e.g., '1hr', '90min'")
    start_at = models.DateField()
    finished_at = models.DateField(null=True, blank=True)
    location = models.TextField(help_text="Location name and Google link")
    teachers = models.ManyToManyField('Teacher', related_name='groups', blank=True)

    def __str__(self):
        return f"{self.name} ({self.start_at})"

    class Meta:
        ordering = ['start_at', 'name']


class Pass(models.Model):
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='passes')
    lessons_included = models.PositiveIntegerField()
    skips_included = models.PositiveIntegerField(default=0)
    name = models.CharField(max_length=100, help_text="e.g., '10-lesson pass', 'Monthly unlimited'")

    def __str__(self):
        return f"{self.name} - {self.group.name} (${self.price})"

    class Meta:
        verbose_name_plural = "Passes"


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}" if self.user.first_name else self.user.username


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    groups = models.ManyToManyField(Group, related_name='students', blank=True)
    phone = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}" if self.user.first_name else self.user.username

    def get_active_passes(self):
        """Get all active passes (with remaining lessons > 0)"""
        from django.db.models import Sum, Count

        purchases = self.purchases.filter(paid_at__isnull=False).select_related('dance_pass')
        active_passes = []

        for purchase in purchases:
            # Count total visits for this pass
            visits_used = StudentVisit.objects.filter(
                student=self,
                group=purchase.dance_pass.group,
                date__gte=purchase.created_at,
                skipped=False
            ).count()

            remaining = purchase.dance_pass.lessons_included - visits_used
            if remaining > 0:
                active_passes.append({
                    'purchase': purchase,
                    'pass': purchase.dance_pass,
                    'remaining_lessons': remaining,
                    'visits_used': visits_used
                })

        return active_passes


class StudentVisit(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='visits')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='visits')
    date = models.DateField()
    skipped = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    def __str__(self):
        status = "Skipped" if self.skipped else "Attended"
        return f"{self.student} - {self.group.name} on {self.date} ({status})"

    class Meta:
        ordering = ['-date']
        unique_together = ['student', 'group', 'date']


class Purchase(models.Model):
    PAYMENT_METHODS = [
        ('TBC', 'TBC Bank'),
        ('BOG', 'Bank of Georgia'),
        ('CASH', 'Cash'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='purchases')
    dance_pass = models.ForeignKey(Pass, on_delete=models.CASCADE, related_name='purchases')
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, blank=True)
    cashier = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        status = "Paid" if self.paid_at else "Unpaid"
        return f"{self.student} - {self.dance_pass.name} ({status})"

    @property
    def pass_(self):
        """Alias for dance_pass to match the field name in the spec"""
        return self.dance_pass

    class Meta:
        ordering = ['-created_at']
