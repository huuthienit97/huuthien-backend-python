from django_filters import rest_framework as filters
from .models import User

class UserFilter(filters.FilterSet):
    username = filters.CharFilter(lookup_expr='icontains')
    email = filters.CharFilter(lookup_expr='icontains')
    is_active = filters.BooleanFilter()
    created_at = filters.DateTimeFromToRangeFilter()
    role = filters.ChoiceFilter(choices=(
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('user', 'User'),
    ))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'is_active', 'created_at', 'role'] 