from django.http import JsonResponse
from django.urls import resolve
from rest_framework import status


class EmailVerificationMiddleware:
    """
    Middleware kiểm tra xác thực email.
    
    Yêu cầu người dùng xác thực email trước khi sử dụng các tính năng của hệ thống.
    Một số endpoint được miễn kiểm tra như: đăng nhập, xác thực email, admin site.
    """

    EXEMPT_PATHS = [
        '/api/token/',              # JWT endpoints
        '/api/users/verify-email/',  # Verify email
        '/api/users/resend-verification/',  # Resend verification
        '/admin/',                  # Admin site
        '/static/',                 # Static files
        '/media/',                  # Media files
        '/api/docs/',               # API documentation
        '/api/schema/',             # API schema
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Bỏ qua các endpoint không cần xác thực email
        if self._is_path_exempt(request.path_info):
            return self.get_response(request)

        # Kiểm tra user đã đăng nhập và cần xác thực email
        if request.user.is_authenticated:
            # Bỏ qua kiểm tra cho superuser và staff
            if request.user.is_superuser or request.user.is_staff:
                return self.get_response(request)
                
            # Kiểm tra xác thực email
            if not request.user.is_email_verified:
                return JsonResponse({
                    'detail': 'Email chưa được xác thực. Vui lòng kiểm tra email của bạn.',
                    'code': 'email_not_verified',
                    'resend_url': '/api/users/resend-verification/',
                    'email': request.user.email
                }, status=status.HTTP_403_FORBIDDEN)

        return self.get_response(request)
        
    def _is_path_exempt(self, path):
        """Kiểm tra xem path có được miễn kiểm tra không"""
        return any(path.startswith(exempt_path) for exempt_path in self.EXEMPT_PATHS) 