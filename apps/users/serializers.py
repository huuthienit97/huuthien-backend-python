from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.cache import cache
from .models import UserProfile, Role, AuditLog
from typing import Dict, List, Any, Optional
from django.db.models import QuerySet

UserModel = get_user_model()


class RoleSerializer(serializers.ModelSerializer):
    """Serializer cho Role model"""
    class Meta:
        model = Role
        fields = ('id', 'name', 'description', 'permissions')


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer cho UserProfile model"""
    class Meta:
        model = UserProfile
        fields = ('bio', 'position', 'department', 'address')


class UserSerializer(serializers.ModelSerializer):
    """Serializer cho User model"""
    profile = UserProfileSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    custom_roles = RoleSerializer(many=True, read_only=True)
    permissions = serializers.SerializerMethodField()
    email_verified = serializers.SerializerMethodField()
    
    class Meta:
        model = UserModel
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 
            'full_name', 'phone_number', 'avatar', 'birth_date', 
            'profile', 'date_joined', 'last_login', 'role',
            'custom_roles', 'permissions', 'email_verified'
        )
        read_only_fields = (
            'date_joined', 'last_login', 'email_verified'
        )
        
    def get_full_name(self, obj) -> str:
        return obj.get_full_name()
    
    def get_permissions(self, obj) -> List[str]:
        return list(obj.get_permissions())
    
    def get_email_verified(self, obj) -> bool:
        """Kiểm tra trạng thái xác thực email của user"""
        return bool(getattr(obj, 'is_email_verified', False))


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer cho việc tạo User mới"""
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = UserModel
        fields = (
            'username', 'email', 'password', 'confirm_password',
            'first_name', 'last_name', 'phone_number'
        )
        
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if data['password'] != data.pop('confirm_password'):
            raise serializers.ValidationError({
                "confirm_password": "Mật khẩu xác nhận không khớp"
            })
        return data
        
    def create(self, validated_data: Dict[str, Any]) -> Any:
        from .services import send_verification_email
        user = UserModel.objects.create_user(**validated_data)
        send_verification_email(user)
        return user


class EmailVerificationSerializer(serializers.Serializer):
    """Serializer cho việc xác thực email"""
    token = serializers.CharField()

    def validate_token(self, value: str) -> str:
        from .services import verify_email
        success, message = verify_email(value)
        if not success:
            raise serializers.ValidationError(message)
        return value


class ResendVerificationSerializer(serializers.Serializer):
    """Serializer cho việc gửi lại email xác thực"""
    email = serializers.EmailField()

    def validate_email(self, value: str) -> str:
        try:
            user = UserModel.objects.get(email=value)
            if getattr(user, 'is_email_verified', False):
                raise serializers.ValidationError(
                    "Email này đã được xác thực"
                )
            self.context['user'] = user
        except UserModel.DoesNotExist:
            raise serializers.ValidationError(
                "Không tìm thấy tài khoản với email này"
            )
        return value

    def save(self) -> Dict[str, str]:
        from .services import resend_verification_email
        user = self.context['user']
        success, message = resend_verification_email(user)
        if not success:
            raise serializers.ValidationError(message)
        return {'message': message}


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer cho AuditLog"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = AuditLog
        fields = ('id', 'user', 'action', 'changes', 'ip_address', 'user_agent', 'timestamp')
        read_only_fields = fields