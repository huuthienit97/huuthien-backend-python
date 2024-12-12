import secrets
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse


def generate_verification_token():
    """Tạo token ngẫu nhiên cho việc xác thực email"""
    return secrets.token_urlsafe(32)


def send_verification_email(user):
    """Gửi email xác thực cho user"""
    # Tạo token mới
    token = generate_verification_token()
    user.email_verification_token = token
    user.email_verification_sent_at = timezone.now()
    user.save(update_fields=['email_verification_token', 'email_verification_sent_at'])

    # Tạo verification URL
    verify_url = f"{settings.FRONTEND_URL}/verify-email/{token}"

    # Render email template
    context = {
        'user': user,
        'verify_url': verify_url,
        'valid_hours': settings.EMAIL_VERIFICATION_TIMEOUT_HOURS,
    }
    html_message = render_to_string('users/email/verify_email.html', context)
    plain_message = strip_tags(html_message)

    # Gửi email
    send_mail(
        subject='Xác thực địa chỉ email của bạn',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message
    )


def verify_email(token):
    """Xác thực email dựa trên token"""
    from .models import User  # Import ở đây để tránh circular import
    
    try:
        user = User.objects.get(
            email_verification_token=token,
            email_verified=False
        )
        
        # Kiểm tra token có còn hiệu lực
        if not user.email_verification_sent_at:
            return False, "Link xác thực không hợp lệ"
            
        timeout = timedelta(hours=settings.EMAIL_VERIFICATION_TIMEOUT_HOURS)
        if user.email_verification_sent_at + timeout < timezone.now():
            return False, "Link xác thực đã hết hạn"
            
        # Xác thực email
        user.email_verified = True
        user.email_verification_token = None
        user.email_verification_sent_at = None
        user.save(update_fields=[
            'email_verified',
            'email_verification_token',
            'email_verification_sent_at'
        ])
        
        return True, "Email đã được xác thực thành công"
        
    except User.DoesNotExist:
        return False, "Link xác thực không hợp lệ"


def resend_verification_email(user):
    """Gửi lại email xác thực"""
    # Kiểm tra xem có thể gửi lại email không
    if user.email_verified:
        return False, "Email đã được xác thực"
        
    if user.email_verification_sent_at:
        timeout = timedelta(minutes=settings.EMAIL_VERIFICATION_RESEND_TIMEOUT_MINUTES)
        if user.email_verification_sent_at + timeout > timezone.now():
            return False, "Vui lòng đợi một thời gian trước khi yêu cầu gửi lại email"
    
    # Gửi lại email xác thực
    send_verification_email(user)
    return True, "Email xác thực đã được gửi lại" 