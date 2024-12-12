"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="User Management API",
        default_version='v1',
        description="""
# API Documentation cho Hệ thống Quản lý Users

## Authentication
Hệ thống sử dụng JWT (JSON Web Token) để xác thực. Để sử dụng các protected endpoints:
1. Lấy token qua endpoint `/api/token/`
2. Thêm token vào header: `Authorization: Bearer <token>`
3. Refresh token khi hết hạn qua `/api/token/refresh/`

## Features
- User Management (CRUD)
- Profile Management
- Role-based Access Control
- User Statistics
- Filtering và Pagination

## Error Codes
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Internal Server Error
        """,
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(
            name="Support Team",
            email="support@users.local",
            url="http://users.local/support"
        ),
        license=openapi.License(
            name="MIT License",
            url="https://opensource.org/licenses/MIT"
        ),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    urlconf='apps.users.urls',
)

urlpatterns = [
    # Swagger URLs
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Admin và API URLs
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include('apps.core.urls')),  # API endpoints
    path('api/', include('apps.users.urls')),  # User API endpoints
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
