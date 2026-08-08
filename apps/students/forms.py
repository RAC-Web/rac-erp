from django import forms
from django.contrib.auth import get_user_model
from .models import StudentProfile

User = get_user_model()

class StudentForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=False, help_text="Leave blank if editing and you don't want to change the password.")

    class Meta:
        model = StudentProfile
        exclude = ['user']
        widgets = {
            'joining_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['username'].initial = self.instance.user.username
            self.fields['email'].initial = self.instance.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        email = self.cleaned_data.get('email')

        if not self.instance.pk:
            # Create new user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                role='Student'
            )
            profile.user = user
        else:
            # Update existing user
            user = profile.user
            user.username = username
            user.email = email
            if password:
                user.set_password(password)
            user.save()

        if commit:
            profile.save()
        return profile
