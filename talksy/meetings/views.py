from django.shortcuts import get_object_or_404
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
        return Response({'message': 'Meeting Deleted successfully'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='update_token', serializer_class=None)
    def update_token_view(self, request, pk=None):
        meeting = self.get_object()
        meeting.token = meeting.update_token
        meeting.save()
        return Response({'new_token': meeting.token,
                         'new_link': {meeting.link}},
                        status=status.HTTP_200_OK)


class JoinMeetingView(APIView):
    def post(self, request, *args, **kwargs):
        meeting_id = kwargs.get('meeting_id')
        input_token = kwargs.get('token')
        meeting = get_object_or_404(Meeting, id=meeting_id)

        # check token
        if not self._check_token_validity(meeting, input_token):
            return Response({'message': 'Wrong Token'}, status=status.HTTP_403_FORBIDDEN)

        # check meeting status
        if not self._check_meeting_status(meeting):
            return Response({'message': 'Meeting not joinable'}, status=status.HTTP_400_BAD_REQUEST)

        # creating/find membership
        membership = self._get_or_create_membership(request, meeting)

        # setting the flags in the session
        request.session['temporary_id'] = membership.anonymous_id
        request.session['admitted'] = True

        return Response({'message': 'ok'}, status=status.HTTP_200_OK)

    def _check_token_validity(self, meeting, token):
        """
        verifies the validity of the meeting token.
        """
        if not token or len(token) != len(meeting.token):
            return False
        return meeting.token == token

    def _check_meeting_status(self, meeting):
        """
        checks if it is possible to join the meeting.
        """
        if self.request.user == meeting.creator:
            return meeting.status != 'completed'
        return meeting.status == 'active'

    def _get_or_create_membership(self, request, meeting):
        """
        creates or returns an existing meeting participation.
        """
        temporary_id = generate_token(20)

        if request.user.is_authenticated:
            membership, created = MeetingMembership.objects.get_or_create(
                user=request.user,
                meeting=meeting,
                defaults={'role': 'participant', 'anonymous_id': temporary_id}
            )
        else:
            membership, created = MeetingMembership.objects.get_or_create(
                anonymous_id=temporary_id,
                meeting=meeting,
                defaults={'role': 'participant', 'status': 'pending'}
            )

        # if the user returns, we restore the status
        if not created and membership.status == 'closed':
            membership.status = 'pending'
            membership.left_at = None
            membership.save()

        return membership
