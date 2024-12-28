from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from utils.token import generate_token

from .models import Meeting, MeetingMembership
from .permissions import IsOwnerOrReadOnly
from .serializers import MeetingSerializer, MeetingStatusSerializer


class MeetingListCreate(generics.ListCreateAPIView):
    queryset = Meeting.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = MeetingSerializer

    def perform_create(self, serializer):
        meeting = serializer.save(creator=self.request.user)
        MeetingMembership.objects.create(user=self.request.user, meeting=meeting, role='host')


class MeetingViewSet(ModelViewSet):
    serializer_class = MeetingSerializer
    queryset = Meeting.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    http_method_names = ['get', 'post']

    @action(detail=True, methods=['get'], url_path='status', serializer_class=MeetingStatusSerializer)
    def status(self, request, pk=None):
        meeting = self.get_object()
        serializer = MeetingStatusSerializer(instance={'status': meeting.status})
        temporary_id = request.session.get('temporary_id')
        admitted = request.session.get('admitted')
        print(temporary_id, admitted)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='end', serializer_class=None)
    def end(self, request, pk=None):
        meeting = self.get_object()
        meeting.end_time = timezone.now()
        meeting.save()
        return Response({'message': 'Meeting ended successfully'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='delete', serializer_class=None)
    def delete(self, request, pk=None):
        meeting = self.get_object()
        meeting.delete()
        return Response({'message': 'Meeting Deleted successfully'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='update_token', serializer_class=None)
    def update_token_view(self, request, pk=None):
        meeting = self.get_object()
        meeting.token = meeting.update_token
        meeting.save()
        return Response({'new_token': meeting.token,
                         'new_link': {meeting.link}},
                        status=status.HTTP_200_OK)


class JoinMeetingView(APIView):
    def post(self, request, meeting_id, token):
        try:
            meeting = Meeting.objects.get(id=meeting_id)
        except Meeting.DoesNotExist:
            return Response({'message': 'Meeting not found.'}, status=status.HTTP_404_NOT_FOUND)

        input_token = token

        if meeting.token != input_token:
            return Response({'message': 'Wrong Token'}, status=status.HTTP_403_FORBIDDEN)

        if request.user == meeting.creator:
            if meeting.status == 'completed':
                return Response({'message': 'Meeting is completed. Owner cannot join.'},
                                status=status.HTTP_400_BAD_REQUEST)
            request.session['temporary_id'] = request.user.id
            request.session['admitted'] = True
            return Response({'message': 'ok'}, status=status.HTTP_200_OK)

        if meeting.status != 'active':
            return Response({'message': 'Meeting not active or ended'}, status=status.HTTP_400_BAD_REQUEST)

        temporary_id = generate_token(20)

        if request.user.is_authenticated:
            membership, created = MeetingMembership.objects.get_or_create(
                user=request.user, anonymous_id=temporary_id, meeting=meeting,
                defaults={'role': 'participant'}
            )
        else:
            membership, created = MeetingMembership.objects.get_or_create(
                anonymous_id=temporary_id, meeting=meeting,
                defaults={'role': 'participant', 'status': 'pending'}
            )

        if not created:
            if membership.status == 'closed':
                membership.status = 'pending'
                membership.left_at = None  # Clear 'left_at' if user is rejoining
                membership.save()

        request.session['temporary_id'] = membership.anonymous_id

        # The flag indicates that the user has passed the verification and can connect to the WebSocket
        request.session['admitted'] = True
        # TODO мб переделать эту говнологику
        return Response({'message': 'ok'}, status=status.HTTP_200_OK)
