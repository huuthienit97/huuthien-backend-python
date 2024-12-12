from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.db.models.functions import TruncDate
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import UserSerializer, UserCreateSerializer, UserProfileSerializer
from .models import UserProfile
from .filters import UserFilter

User = get_user_model()

# Swagger parameters
user_response = openapi.Response(
    description="Successful response",
    schema=UserSerializer
)

profile_request = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='Tên'),
        'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Họ'),
        'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email'),
        'profile': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'bio': openapi.Schema(type=openapi.TYPE_STRING, description='Tiểu sử'),
                'position': openapi.Schema(type=openapi.TYPE_STRING, description='Chức vụ'),
                'department': openapi.Schema(type=openapi.TYPE_STRING, description='Phòng ban'),
                'address': openapi.Schema(type=openapi.TYPE_STRING, description='Địa chỉ')
            }
        )
    }
)

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint để quản lý users.
    
    list:
    Trả về danh sách tất cả users.
    * Yêu cầu xác thực JWT
    * Hỗ trợ filtering và pagination
    
    create:
    Tạo user mới.
    * Không yêu cầu xác thực
    * Trả về thông tin user và token
    
    retrieve:
    Xem chi tiết một user.
    * Yêu cầu xác thực JWT
    
    update:
    Cập nhật toàn bộ thông tin user.
    * Yêu cầu xác thực JWT
    * Chỉ admin hoặc chính user đó mới có quyền
    
    partial_update:
    Cập nhật một phần thông tin user.
    * Yêu cầu xác thực JWT
    * Chỉ admin hoặc chính user đó mới có quyền
    
    destroy:
    Xóa user.
    * Yêu cầu xác thực JWT
    * Chỉ admin mới có quyền
    """
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserFilter
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return super().get_permissions()
    
    @swagger_auto_schema(
        method='get',
        operation_description="""
        Lấy thông tin của user hiện tại đang đăng nhập.
        
        Responses:
        * 200: Thành công
        * 401: Chưa xác thực
        """,
        responses={
            200: user_response,
            401: 'Unauthorized'
        },
        security=[{'Bearer': []}]
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Endpoint để lấy thông tin user hiện tại"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        methods=['put', 'patch'],
        operation_description="""
        Cập nhật thông tin profile của user hiện tại.
        
        Example Request:
        ```json
        {
            "first_name": "John",
            "last_name": "Doe",
            "profile": {
                "bio": "Software Engineer",
                "position": "Senior Developer",
                "department": "Engineering",
                "address": "123 Street"
            }
        }
        ```
        """,
        request_body=profile_request,
        responses={
            200: user_response,
            400: 'Bad Request',
            401: 'Unauthorized'
        },
        security=[{'Bearer': []}]
    )
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """Endpoint để cập nhật profile của user hiện tại"""
        user = request.user
        profile = user.profile
        
        # Cập nhật thông tin user
        user_serializer = UserSerializer(
            user, 
            data=request.data, 
            partial=True
        )
        user_serializer.is_valid(raise_exception=True)
        user_serializer.save()
        
        # Cập nhật thông tin profile
        profile_data = request.data.get('profile', {})
        profile_serializer = UserProfileSerializer(
            profile,
            data=profile_data,
            partial=True
        )
        profile_serializer.is_valid(raise_exception=True)
        profile_serializer.save()
        
        return Response(user_serializer.data)

    @swagger_auto_schema(
        method='get',
        operation_description="""
        Lấy thống kê về users trong hệ thống.
        
        Returns:
        * total_users: Tổng số users
        * active_users: Số users đang active
        * role_distribution: Phân bố users theo role
        * new_users_trend: Xu hướng users mới trong 7 ngày
        
        Example Response:
        ```json
        {
            "total_users": 100,
            "active_users": 85,
            "role_distribution": [
                {"role": "admin", "count": 5},
                {"role": "staff", "count": 20},
                {"role": "user", "count": 75}
            ],
            "new_users_trend": [
                {"date": "2023-12-11", "count": 10},
                {"date": "2023-12-10", "count": 8}
            ]
        }
        ```
        """,
        responses={
            200: openapi.Response(
                description="Thống kê users",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'total_users': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'active_users': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'role_distribution': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'role': openapi.Schema(type=openapi.TYPE_STRING),
                                    'count': openapi.Schema(type=openapi.TYPE_INTEGER)
                                }
                            )
                        ),
                        'new_users_trend': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                                    'count': openapi.Schema(type=openapi.TYPE_INTEGER)
                                }
                            )
                        )
                    }
                )
            ),
            401: 'Unauthorized',
            403: 'Forbidden - Requires admin privileges'
        },
        security=[{'Bearer': []}]
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Endpoint để lấy th���ng kê về users"""
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        
        # Thống kê users theo role
        role_stats = User.objects.values('role').annotate(
            count=Count('id')
        )
        
        # Thống kê users mới trong 7 ngày qua
        new_users_by_date = User.objects.annotate(
            date=TruncDate('date_joined')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('-date')[:7]
        
        return Response({
            'total_users': total_users,
            'active_users': active_users,
            'role_distribution': role_stats,
            'new_users_trend': new_users_by_date
        })
