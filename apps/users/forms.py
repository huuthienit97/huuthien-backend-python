from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _

from .models import User, UserProfile


class CustomUserCreationForm(UserCreationForm):
    """Form đăng ký user mới"""
    email = forms.EmailField(
        label=_("Email"),
        max_length=254,
        widget=forms.EmailInput(attrs={'autocomplete': 'email'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')


class CustomUserChangeForm(UserChangeForm):
    """Form cập nhật thông tin user"""
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')


class UserProfileForm(forms.ModelForm):
    """Form cập nhật profile của user"""
    class Meta:
        model = UserProfile
        fields = ('bio', 'position', 'department', 'address')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'address': forms.Textarea(attrs={'rows': 3}),
        } 