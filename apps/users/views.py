from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.db.models.functions import TruncDate
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import (
    UserSerializer, UserCreateSerializer, UserProfileSerializer,
    ResendVerificationSerializer, EmailVerificationSerializer
)
from .models import UserProfile
from .filters import UserFilter
from .search.services import UserSearchService

UserModel = get_user_model()

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
    """API endpoint để quản lý users"""
    queryset = UserModel.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserFilter
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.search_service = UserSearchService()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'verify_email', 'resend_verification']:
            return [permissions.AllowAny()]
        return super().get_permissions()
    
    @swagger_auto_schema(
        method='get',
        operation_description="Lấy thông tin của user hiện tại đang đăng nhập",
        responses={200: user_response, 401: 'Unauthorized'},
        security=[{'Bearer': []}]
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Endpoint để lấy thông tin user hiện tại"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        methods=['put', 'patch'],
        operation_description="Cập nhật thông tin profile của user hiện tại",
        request_body=profile_request,
        responses={200: user_response, 400: 'Bad Request', 401: 'Unauthorized'},
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
        operation_description="Lấy thống kê về users trong hệ thống",
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
        """Endpoint để lấy thống kê về users"""
        total_users = UserModel.objects.count()
        active_users = UserModel.objects.filter(is_active=True).count()
        
        # Thống kê users theo role
        role_stats = UserModel.objects.values('role').annotate(
            count=Count('id')
        )
        
        return Response({
            'total_users': total_users,
            'active_users': active_users,
            'role_distribution': role_stats
        })

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Tìm kiếm user
        """
        query = request.query_params.get('q', '')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        
        results = self.search_service.search(
            query=query,
            page=page,
            page_size=page_size
        )
        
        return Response(results)
    
    @action(detail=False, methods=['get'])
    def suggest(self, request):
        """
        Gợi ý tìm kiếm
        """
        query = request.query_params.get('q', '')
        limit = int(request.query_params.get('limit', 5))
        
        suggestions = self.search_service.suggest(
            query=query,
            limit=limit
        )
        
        return Response(suggestions)


@swagger_auto_schema(
    method='post',
    operation_description="Xác thực email thông qua token",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['token'],
        properties={
            'token': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    responses={
        200: openapi.Response(
            description="Email đã được xác thực thành công",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )
        ),
        400: 'Token không hợp lệ hoặc đã hết hạn'
    }
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_email(request):
    """View để xác thực email"""
    serializer = EmailVerificationSerializer(data=request.data)
    if serializer.is_valid():
        return Response(
            {'message': 'Email đã được xác thực thành công'},
            status=status.HTTP_200_OK
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='post',
    operation_description="Gửi lại email xác thực",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['email'],
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    responses={
        200: openapi.Response(
            description="Email xác thực đã được gửi lại",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )
        ),
        400: 'Email không hợp lệ hoặc đã được xác thực'
    }
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def resend_verification(request):
    """View để gửi lại email xác thực"""
    serializer = ResendVerificationSerializer(data=request.data)
    if serializer.is_valid():
        try:
            result = serializer.save()
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
