import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from .models import Meeting, MeetingMembership, MeetingMessage


class MeetingsConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.meeting_uuid = None
        self.group_name = None
        self.user_temporary_id = None
        self.admitted = None
        self.membership_cache = None

    async def connect(self):
        self.meeting_uuid = self.scope['url_route']['kwargs']['meeting_uuid']
        self.group_name = f"meeting_{self.meeting_uuid}"
        sessions = self.scope['session']

        self.user_temporary_id = sessions.get('temporary_id')
        self.admitted = sessions.get('admitted')

        print(f"User {self.user_temporary_id} connected to group {self.group_name}")
        if not self.user_temporary_id or self.admitted is not True:
            print('Нет доступа. сперва в /join/')
            await self.close()
            return

        meeting_membership = await self.get_meeting_membership(self.user_temporary_id)
        if not meeting_membership:
            await self.close()
            return

        await self.update_meeting_membership(meeting_membership)

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.update_meeting_membership_on_disconnect(self.user_temporary_id)
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        message_type = data.get('type')

        if message_type == 'chat':
            message = data.get('message')
            message_obj = await self.save_message(message)
            decrypted_message = message_obj.content

            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "websocket.message",
                    "message": {
                        "type": "chat",
                        "sender_id": self.user_temporary_id,
                        "content": decrypted_message,
                        "timestamp": timezone.now().isoformat(),
                    }
                }
            )

        if message_type in ['offer', 'answer', 'ice-candidate']:
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "websocket.message",
                    "message": data,
                    "sender": self.scope['session'].get('temporary_id'),
                }
            )

    async def websocket_message(self, event):
        if event['sender'] != self.scope['session'].get('temporary_id'):
            await self.send(text_data=json.dumps(event['message']))

    @database_sync_to_async
    def get_meeting_membership(self, anonymous_id):
        if hasattr(self, 'membership_cache'):
            return self.membership_cache
        try:
            membership = MeetingMembership.objects.get(anonymous_id=anonymous_id)
            self.membership_cache = membership
            return membership
        except MeetingMembership.DoesNotExist:
            return None

    @database_sync_to_async
    def update_meeting_membership(self, meeting_membership):
        meeting_membership.status = 'active'
        meeting_membership.joined_at = timezone.now()
        meeting_membership.save()

    @database_sync_to_async
    def update_meeting_membership_on_disconnect(self, anonymous_id):
        try:
            meeting_membership = MeetingMembership.objects.get(anonymous_id=anonymous_id)
            meeting_membership.status = 'closed'
            meeting_membership.left_at = timezone.now()
            meeting_membership.save()
        except MeetingMembership.DoesNotExist:
            pass

    @database_sync_to_async
    def save_message(self, message_content):
        try:
            meeting = Meeting.objects.get(uuid=self.meeting_uuid)
        except ObjectDoesNotExist:
            return None

        message = MeetingMessage(meeting=meeting, sender_id=self.user_temporary_id)
        message.content = message_content
        message.save()
        return message
