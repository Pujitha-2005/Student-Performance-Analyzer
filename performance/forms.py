from django import forms
from .models import Student, Performance

# Login form for handling user login
class LoginForm(forms.Form):
    username = forms.CharField(max_length=100, label='Enter your username')
    password = forms.CharField(widget=forms.PasswordInput, label='Enter your password', min_length=8)

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 8:
            raise forms.ValidationError('Password must be at least 8 characters long.')
        return password

# Form to handle student data
class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['roll_no', 'name', 'email', 'parent_email', 'dob']

    def clean_parent_email(self):
        parent_email = self.cleaned_data.get('parent_email')
        if not parent_email:
            raise forms.ValidationError("Parent email is required.")
        return parent_email

# Form to handle performance data
class PerformanceForm(forms.ModelForm):
    class Meta:
        model = Performance
        fields = ['student', 'subject', 'marks']
