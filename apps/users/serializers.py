from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile, Role, AuditLog

User = get_user_model()


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


class BaseUserSerializer(serializers.ModelSerializer):
    """Base serializer cho User model với các trường cơ bản"""
    full_name = serializers.SerializerMethodField()
    email_verified = serializers.SerializerMethodField()

    def get_full_name(self, obj) -> str:
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username

    def get_email_verified(self, obj) -> bool:
        return getattr(obj, 'is_email_verified', False)


class UserSerializer(BaseUserSerializer):
    """Serializer cho User model với đầy đủ thông tin"""
    profile = UserProfileSerializer(read_only=True)
    custom_roles = RoleSerializer(many=True, read_only=True)
    permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 
            'full_name', 'phone_number', 'avatar', 'birth_date', 
            'profile', 'date_joined', 'last_login', 'role',
            'custom_roles', 'permissions', 'email_verified'
        )
        read_only_fields = ('date_joined', 'last_login', 'email_verified')
    
    def get_permissions(self, obj) -> list:
        return list(getattr(obj, 'get_permissions', lambda: [])())


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer cho việc tạo User mới"""
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text="Mật khẩu phải có ít nhất 8 ký tự"
    )
    confirm_password = serializers.CharField(
        write_only=True,
        help_text="Nhập lại mật khẩu để xác nhận"
    )
    
    class Meta:
        model = User
        fields = (
            'username', 'email', 'password', 'confirm_password',
            'first_name', 'last_name', 'phone_number'
        )
        
    def validate(self, data):
        if data['password'] != data.pop('confirm_password'):
            raise serializers.ValidationError({
                "confirm_password": "Mật khẩu xác nhận không khớp"
            })
        return data
        
    def create(self, validated_data):
        from .services import send_verification_email
        user = User.objects.create_user(**validated_data)
        send_verification_email(user)
        return user


class EmailVerificationSerializer(serializers.Serializer):
    """Serializer cho việc xác thực email"""
    token = serializers.CharField(help_text="Token xác thực email")

    def validate_token(self, value):
        from .services import verify_email
        success, message = verify_email(value)
        if not success:
            raise serializers.ValidationError(message)
        return value


class ResendVerificationSerializer(serializers.Serializer):
    """Serializer cho việc gửi lại email xác thực"""
    email = serializers.EmailField(help_text="Email cần gửi lại xác thực")

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
            if getattr(user, 'is_email_verified', False):
                raise serializers.ValidationError(
                    "Email này đã được xác thực"
                )
            self.context['user'] = user
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "Không tìm thấy tài khoản với email này"
            )

    def save(self):
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