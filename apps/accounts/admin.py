from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import AdminUserCreationForm
from django import forms
from .models import User

class CustomUserCreationForm(AdminUserCreationForm):
    allow_weak_password = forms.BooleanField(
        required=False,
        label="Allow Weak Password",
        help_text="Check this to bypass password validation rules (e.g., 'password is too similar to the username')."
    )

    class Meta(AdminUserCreationForm.Meta):
        model = User
        fields = ("username", "role")

    def validate_password_for_user(self, user, password_field_name="password2"):
        if self.cleaned_data.get("allow_weak_password"):
            return
        super().validate_password_for_user(user, password_field_name)

class CustomUserAdmin(UserAdmin):
    model = User
    add_form = CustomUserCreationForm
    list_display = ['username', 'email', 'role', 'is_staff', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('role', 'allow_weak_password')}),
    )

admin.site.register(User, CustomUserAdmin)
