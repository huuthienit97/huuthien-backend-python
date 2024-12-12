from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

# Create your views here.

@api_view(['GET'])
def index(request):
    return Response({
        'status': 'success',
        'message': 'Welcome to HuuThien API',
        'version': '1.0.0'
    }, status=status.HTTP_200_OK)
