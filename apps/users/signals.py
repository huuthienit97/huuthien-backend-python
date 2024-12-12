from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth import user_logged_in, user_logged_out

from .models import User, UserProfile, AuditLog


def get_changes(old_instance, new_instance):
    """So sánh và lấy các thay đổi giữa 2 instance"""
    changes = {}
    if not old_instance:
        return {field.name: getattr(new_instance, field.name) 
                for field in new_instance._meta.fields 
                if field.name not in ['password', 'search_vector']}
                
    for field in new_instance._meta.fields:
        if field.name in ['password', 'search_vector']:
            continue
        old_value = getattr(old_instance, field.name)
        new_value = getattr(new_instance, field.name)
        if old_value != new_value:
            changes[field.name] = {
                'old': str(old_value),
                'new': str(new_value)
            }
    return changes


@receiver(pre_save, sender=User)
def user_pre_save(sender, instance, **kwargs):
    """Xử lý trước khi lưu User"""
    if instance.pk:
        try:
            old_instance = User.objects.get(pk=instance.pk)
            instance._pre_save_instance = old_instance
        except User.DoesNotExist:
            instance._pre_save_instance = None
    else:
        instance._pre_save_instance = None


@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    """Xử lý sau khi lưu User"""
    # Lấy request từ thread local storage nếu có
    request = getattr(instance, '_request', None)
    
    # Lấy thông tin về IP và User Agent
    ip_address = None
    user_agent = ''
    if request:
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Tạo audit log
    action = AuditLog.ACTION_CREATE if created else AuditLog.ACTION_UPDATE
    changes = get_changes(getattr(instance, '_pre_save_instance', None), instance)
    
    if changes:  # Chỉ tạo log nếu có thay đổi
        AuditLog.objects.create(
            user=instance,
            action=action,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    # Cập nhật thời gian thay đổi mật khẩu nếu password thay đổi
    if not created and 'password' in changes:
        instance.last_password_change = timezone.now()
        instance.save(update_fields=['last_password_change'])


@receiver(pre_delete, sender=User)
def user_pre_delete(sender, instance, **kwargs):
    """Xử lý trước khi xóa User"""
    request = getattr(instance, '_request', None)
    
    # Tạo audit log cho việc xóa user
    AuditLog.objects.create(
        user=instance,
        action=AuditLog.ACTION_DELETE,
        changes=get_changes(None, instance),
        ip_address=request.META.get('REMOTE_ADDR') if request else None,
        user_agent=request.META.get('HTTP_USER_AGENT', '') if request else ''
    )


@receiver(user_logged_in)
def user_logged_in_callback(sender, request, user, **kwargs):
    """Xử lý khi user đăng nhập"""
    # Reset số lần đăng nhập thất bại
    if user.failed_login_attempts > 0:
        user.failed_login_attempts = 0
        user.save(update_fields=['failed_login_attempts'])
    
    # Tạo audit log cho việc đăng nhập
    AuditLog.objects.create(
        user=user,
        action=AuditLog.ACTION_LOGIN,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )


@receiver(user_logged_out)
def user_logged_out_callback(sender, request, user, **kwargs):
    """Xử lý khi user đăng xuất"""
    if user:  # user có thể None nếu session hết hạn
        AuditLog.objects.create(
            user=user,
            action=AuditLog.ACTION_LOGOUT,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Tự động tạo profile khi tạo user mới"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Tự động lưu profile khi lưu user"""
    instance.profile.save() 