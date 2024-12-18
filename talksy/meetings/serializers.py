from rest_framework import serializers

from users.models import User

from .models import Meeting


class MeetingSerializer(serializers.ModelSerializer):
    creator = serializers.ReadOnlyField(source='creator.username')
    token = serializers.CharField(read_only=True)
    link = serializers.SerializerMethodField()

    class Meta:
        model = Meeting
        fields = ['id', 'creator', 'title', 'description', 'start_time', 'end_time', 'token', 'link']

    def get_link(self, obj):
        return obj.link


class MeetingStatusSerializer(serializers.Serializer):
    status = serializers.CharField(read_only=True)


class MeetingUpdateToken(serializers.Serializer):
    token = serializers.CharField(read_only=True)
