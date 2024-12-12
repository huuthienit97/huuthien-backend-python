from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.core.cache import cache
from django.conf import settings
from typing import Set, Optional
from datetime import datetime
from django.db.models import (
    CharField, TextField, JSONField, DateTimeField, EmailField,
    ImageField, DateField, PositiveIntegerField, BooleanField,
    OneToOneField, ForeignKey, ManyToManyField, GenericIPAddressField
)


class Role(models.Model):
    """
    Model để quản lý role động
    """
    name: CharField = models.CharField(_('role name'), max_length=50, unique=True)
    description: TextField = models.TextField(_('description'), blank=True)
    permissions: JSONField = models.JSONField(default=dict)
    created_at: DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('role')
        verbose_name_plural = _('roles')

    def __str__(self) -> str:
        return self.name


class User(AbstractUser):
    """
    Custom User Model kế thừa từ AbstractUser với các tính năng nâng cao
    """
    ROLE_ADMIN = 'admin'
    ROLE_STAFF = 'staff'
    ROLE_USER = 'user'
    
    ROLE_CHOICES = [
        (ROLE_ADMIN, _('Admin')),
        (ROLE_STAFF, _('Staff')),
        (ROLE_USER, _('User')),
    ]
    
    # Basic fields
    email: EmailField = models.EmailField(_('email address'), unique=True)
    phone_number: CharField = models.CharField(_('phone number'), max_length=15, blank=True)
    avatar: Optional[ImageField] = models.ImageField(upload_to='avatars/', null=True, blank=True)
    birth_date: Optional[DateField] = models.DateField(_('birth date'), null=True, blank=True)
    role: CharField = models.CharField(
        _('role'),
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_USER
    )
    custom_roles: ManyToManyField = models.ManyToManyField(
        Role,
        verbose_name=_('custom roles'),
        blank=True,
        related_name='users'
    )
    
    # Security fields
    last_password_change: Optional[DateTimeField] = models.DateTimeField(
        _('last password change'),
        null=True,
        blank=True
    )
    failed_login_attempts: PositiveIntegerField = models.PositiveIntegerField(default=0)
    last_failed_login: Optional[DateTimeField] = models.DateTimeField(null=True, blank=True)
    
    # Search field
    search_vector: SearchVectorField = SearchVectorField(null=True)
    
    # Email verification fields
    email_verified: BooleanField = models.BooleanField(
        _('email verified'),
        default=False,
        help_text=_('Designates whether this user has verified their email address.')
    )
    email_verification_token: Optional[CharField] = models.CharField(
        _('email verification token'),
        max_length=100,
        blank=True,
        null=True,
        unique=True
    )
    email_verification_sent_at: Optional[DateTimeField] = models.DateTimeField(
        _('email verification sent at'),
        null=True,
        blank=True
    )
    
    # Required fields
    REQUIRED_FIELDS = ['email']

    class Meta:
        swappable = 'AUTH_USER_MODEL'
        verbose_name = _('user')
        verbose_name_plural = _('users')
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['date_joined']),
            GinIndex(fields=['search_vector']),
        ]

    def __str__(self) -> str:
        return self.get_full_name() or self.username

    def save(self, *args, **kwargs) -> None:
        # Xóa cache khi user được cập nhật
        cache_key = f'user_stats_{self.pk}'
        cache.delete(cache_key)
        super().save(*args, **kwargs)

    def get_permissions(self) -> Set[str]:
        """Lấy tất cả quyền của user bao gồm cả custom roles"""
        permissions = set()
        if self.is_superuser:
            return {'all'}
        
        # Thêm quyền từ role mặc định
        if self.role == self.ROLE_ADMIN:
            permissions.update(['admin', 'staff', 'user'])
        elif self.role == self.ROLE_STAFF:
            permissions.update(['staff', 'user'])
        else:
            permissions.add('user')
            
        # Thêm quyền từ custom roles
        for role in self.custom_roles.all():
            permissions.update(role.permissions.keys())
            
        return permissions

    def has_permission(self, permission: str) -> bool:
        """Kiểm tra xem user có quyền cụ thể không"""
        return permission in self.get_permissions()

    @property
    def is_email_verified(self) -> bool:
        """Property để kiểm tra trạng thái xác thực email"""
        return self.email_verified


class UserProfile(models.Model):
    """
    Model để lưu thông tin bổ sung của User
    """
    user: OneToOneField = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='profile'
    )
    bio: TextField = models.TextField(_('biography'), max_length=500, blank=True)
    position: CharField = models.CharField(_('position'), max_length=100, blank=True)
    department: CharField = models.CharField(_('department'), max_length=100, blank=True)
    address: TextField = models.TextField(_('address'), blank=True)
    
    class Meta:
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')

    def __str__(self):
        return f"{self.user.get_full_name()}'s profile"


class AuditLog(models.Model):
    """
    Model để ghi lại lịch sử thay đổi của User
    """
    ACTION_CREATE = 'create'
    ACTION_UPDATE = 'update'
    ACTION_DELETE = 'delete'
    ACTION_LOGIN = 'login'
    ACTION_LOGOUT = 'logout'
    
    ACTION_CHOICES = [
        (ACTION_CREATE, _('Create')),
        (ACTION_UPDATE, _('Update')),
        (ACTION_DELETE, _('Delete')),
        (ACTION_LOGIN, _('Login')),
        (ACTION_LOGOUT, _('Logout')),
    ]
    
    user: ForeignKey = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    action: CharField = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES
    )
    changes: JSONField = models.JSONField(default=dict)
    ip_address: GenericIPAddressField = models.GenericIPAddressField(null=True)
    user_agent: TextField = models.TextField(blank=True)
    timestamp: DateTimeField = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('audit log')
        verbose_name_plural = _('audit logs')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"
