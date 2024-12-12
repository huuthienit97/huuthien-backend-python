from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom User Model kế thừa từ AbstractUser
    """
    ROLE_ADMIN = 'admin'
    ROLE_STAFF = 'staff'
    ROLE_USER = 'user'
    
    ROLE_CHOICES = [
        (ROLE_ADMIN, _('Admin')),
        (ROLE_STAFF, _('Staff')),
        (ROLE_USER, _('User')),
    ]
    
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(_('phone number'), max_length=15, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    birth_date = models.DateField(_('birth date'), null=True, blank=True)
    role = models.CharField(
        _('role'),
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_USER
    )
    
    # Thêm email vào REQUIRED_FIELDS để bắt buộc khi tạo superuser
    REQUIRED_FIELDS = ['email']

    class Meta:
        swappable = 'AUTH_USER_MODEL'
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.get_full_name() or self.username


class UserProfile(models.Model):
    """
    Model để lưu thông tin bổ sung của User
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='profile'
    )
    bio = models.TextField(_('biography'), max_length=500, blank=True)
    position = models.CharField(_('position'), max_length=100, blank=True)
    department = models.CharField(_('department'), max_length=100, blank=True)
    address = models.TextField(_('address'), blank=True)
    
    class Meta:
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')

    def __str__(self):
        return f"{self.user.get_full_name()}'s profile"
