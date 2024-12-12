from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer cho UserProfile"""
    class Meta:
        model = UserProfile
        fields = ('bio', 'position', 'department', 'address')


class UserSerializer(serializers.ModelSerializer):
    """Serializer cho User"""
    profile = UserProfileSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 
                 'full_name', 'phone_number', 'avatar', 'birth_date', 
                 'profile', 'date_joined', 'last_login')
        read_only_fields = ('date_joined', 'last_login')
        
    def get_full_name(self, obj):
        return obj.get_full_name()


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer cho việc tạo User mới"""
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'first_name', 
                 'last_name', 'phone_number')
        
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user 