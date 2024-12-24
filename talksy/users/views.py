from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from utils import email

from .models import BlockHistory, User
from .serializers import (UserBlockSerializer, UserLoginSerializer,
                          UserProfileSerializer, UserRegistrationSerializer,
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


class UserActionViewSet(ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAdminUser]
    http_method_names = ['get', 'post', 'delete']

    def get_queryset(self):
        return User.objects.all()

    @action(detail=True, methods=['post'], url_path='block', serializer_class=UserBlockSerializer)
    def block(self, request, pk=None):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if user.is_blocked:
            return Response({'message': 'User is already blocked'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user.is_blocked = True
            user.save()
            BlockHistory.objects.create(
                user=user,
                blocked_by=request.user,
                reason=serializer.validated_data['reason']
            )

        return Response(
            {
                'message': 'User blocked successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                },
                'reason': serializer.validated_data['reason']
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='unblock', serializer_class=None)
    def unblock(self, request, pk=None):
        user = self.get_object()
        if not user.is_blocked:
            return Response({'message': 'User is not blocked'}, status=status.HTTP_400_BAD_REQUEST)

        user.is_blocked = False
        user.save()

        deleted_count, _ = BlockHistory.objects.filter(user=user).delete()

        return Response(
            {
                'message': 'User unblocked',
                'deleted_block_history_count': deleted_count
            },
            status=status.HTTP_200_OK
        )
