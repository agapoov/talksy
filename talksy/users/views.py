from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from utils import email

from .models import User
from .serializers import (UserLoginSerializer, UserRegistrationSerializer,
                          VerifyEmailSerializer)
from .tasks import send_2fa_email


class UserRegistrationView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        code = email.generate_code()
        send_2fa_email.delay(user.email, code)
        request.session['code'] = code
        request.session['user_id'] = user.id
        return Response({'message': 'Success. Code was sent.'}, status=status.HTTP_201_CREATED)


class UserVerifyEmailView(APIView):
    serializer_class = VerifyEmailSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=VerifyEmailSerializer)
    def post(self, request, *args, **kwargs):
        user_id = request.session.get('user_id')
        user = User.objects.get(id=user_id)
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = request.session.get('code')
        inputed_code = serializer.validated_data['code']

        if code == inputed_code:
            user.email_confirmed = True
            user.save()
            self._clear_session()

            return Response({'message': 'ok'}, status=status.HTTP_200_OK)

        return Response({'message': 'Error, Invalid Code'}, status=status.HTTP_400_BAD_REQUEST)

    def _clear_session(self):
        self.request.session.pop('code', None)
        self.request.session.pop('username', None)


class UserLoginView(APIView):
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=UserLoginSerializer)
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
