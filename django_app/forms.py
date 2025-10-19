from django import forms
from django.contrib.auth.models import User
from django.forms import formset_factory
from .models import Group, Pass, Student, Teacher, Purchase, StudentVisit


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'schedule', 'duration', 'start_at', 'finished_at', 'location', 'teachers']
        widgets = {
            'schedule': forms.TextInput(attrs={'placeholder': '[{"day": "tue", "time": "19:30"}, {"day": "thu", "time": "20:30"}]'}),
            'start_at': forms.DateInput(attrs={'type': 'date'}),
            'finished_at': forms.DateInput(attrs={'type': 'date'}),
            'location': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_schedule(self):
        import json
        schedule = self.cleaned_data['schedule']

        try:
            if isinstance(schedule, str):
                schedule = json.loads(schedule)

            # Validate schedule format
            if not isinstance(schedule, list):
                raise forms.ValidationError("Schedule must be a list of schedule items")

            for item in schedule:
                if not isinstance(item, dict) or 'day' not in item or 'time' not in item:
                    raise forms.ValidationError("Each schedule item must have 'day' and 'time' keys")

                # Validate day
                valid_days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
                if item['day'] not in valid_days:
                    raise forms.ValidationError(f"Invalid day: {item['day']}. Must be one of {valid_days}")

            return schedule

        except json.JSONDecodeError:
            raise forms.ValidationError("Schedule must be valid JSON")


class StudentForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()
    username = forms.CharField(max_length=150, required=False,
                               help_text="Leave empty to auto-generate from email")

    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'email', 'username', 'phone', 'notes', 'groups']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # Editing existing student
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
            self.fields['username'].initial = self.instance.user.username

    def save(self, commit=True):
        if self.instance.pk:
            # Update existing student and user
            user = self.instance.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            if self.cleaned_data['username']:
                user.username = self.cleaned_data['username']
            if commit:
                user.save()
            student = super().save(commit)
        else:
            # Create new student and user
            username = self.cleaned_data['username'] or self.cleaned_data['email']
            user = User.objects.create_user(
                username=username,
                email=self.cleaned_data['email'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name']
            )
            student = super().save(commit=False)
            student.user = user
            if commit:
                student.save()
                self.save_m2m()
        return student


class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['dance_pass', 'payment_method', 'notes']
        labels = {
            'dance_pass': 'Pass',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active groups' passes
        self.fields['dance_pass'].queryset = Pass.objects.filter(group__finished_at__isnull=True)


class StudentVisitForm(forms.ModelForm):
    class Meta:
        model = StudentVisit
        fields = ['student', 'skipped']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student'].widget = forms.HiddenInput()


StudentVisitFormSet = formset_factory(StudentVisitForm, extra=0)


class StudentSelectionForm(forms.Form):
    student = forms.ModelChoiceField(queryset=Student.objects.all(), empty_label="Select a student")


class NewStudentForm(forms.Form):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()
    phone = forms.CharField(max_length=20, required=False)

    def save(self):
        username = self.cleaned_data['email']
        user = User.objects.create_user(
            username=username,
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name']
        )
        student = Student.objects.create(
            user=user,
            phone=self.cleaned_data['phone']
        )
        return student