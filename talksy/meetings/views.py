from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Meeting
from .serializers import (MeetingSerializer, MeetingStatusSerializer,
                          MeetingUpdateToken)


class MeetingListCreate(generics.ListCreateAPIView):
    queryset = Meeting.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = MeetingSerializer

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class MeetingViewSet(ModelViewSet):
    queryset = Meeting.objects.all()
    serializer_class = MeetingSerializer
    http_method_names = ['get', 'post']

    @action(detail=True, methods=['get'], url_path='status', serializer_class=MeetingStatusSerializer)
    def status(self, request, pk=None):
        meeting = self.get_object()
        serializer = MeetingStatusSerializer(instance={'status': meeting.status})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='end', serializer_class=None)
    def end(self, request, pk=None):
        meeting = self.get_object()
        meeting.end_time = timezone.now()
        meeting.save()
        return Response({"message": "Meeting ended successfully"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='delete', serializer_class=None)
    def delete(self, request, pk=None):
        meeting = self.get_object()
        meeting.delete()
        return Response({"message": "Meeting Deleted successfully"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='update_token', serializer_class=MeetingUpdateToken)
    def update_token(self, request, pk=None):
        meeting = self.get_object()
        meeting.token = meeting.update_token
        return Response({'new_link': meeting.link})

    # @action(detail=True, methods=['post'], url_path='join')
    # def join(self, request, pk=None):
    #     pass
