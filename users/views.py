from django.contrib.auth import get_user_model
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

# from ..serializers.user import UserSerializer, TokenObtainPairSerializer
from .serializers import UserSerializer, TokenObtainPairSerializer, UserProfileSerializer


class RegisterView(APIView):
    http_method_names = ['post']

    def post(self, *args, **kwargs):
        serializer = UserSerializer(data=self.request.data)
        if serializer.is_valid():
            get_user_model().objects.create_user(**serializer.validated_data)
            return Response(status=HTTP_201_CREATED)
        return Response(status=HTTP_400_BAD_REQUEST, data={'errors': serializer.errors})


class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer


class ChangePasswordView(APIView):
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['old_password', 'new_password'],
        properties={
            'old_password': openapi.Schema(type=openapi.TYPE_STRING, description='Your current password'),
            'new_password': openapi.Schema(type=openapi.TYPE_STRING, description='Your new password'),
        }
    ))
    def post(self, request, *args, **kwargs):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not user.check_password(old_password):
            return Response({'detail': 'Old password is incorrect.'}, status=400)

        user.set_password(new_password)
        user.save()
        return Response({'detail': 'Password changed successfully.'})


class UserProfileView(generics.RetrieveUpdateAPIView):
    parser_classes = (MultiPartParser, FormParser)
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def put(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
