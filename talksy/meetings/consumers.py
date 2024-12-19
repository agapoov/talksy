import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone

from .models import MeetingMembership


class MeetingsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.meeting_uuid = self.scope['url_route']['kwargs']['meeting_uuid']
        self.group_name = f"meeting_{self.meeting_uuid}"
        sessions = self.scope['session']

        self.temporary_id = sessions.get('temporary_id')
        self.admitted = sessions.get('admitted')

        print(f"User {self.temporary_id} connected to group {self.group_name}")
        if not self.temporary_id or not self.admitted:
            print('Нет доступа. сперва в /join/ ')
            await self.close()
            return

        meeting_membership = await sync_to_async(self.get_meeting_membership)(self.temporary_id)
        if not meeting_membership:
            await self.close()
            return

        await sync_to_async(self.update_meeting_membership)(meeting_membership)

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await sync_to_async(self.update_meeting_membership_on_disconnect)(self.temporary_id)
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        if not text_data:
            return
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError as e:
            return

        message_type = data.get('type')

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

    def get_meeting_membership(self, anonymous_id):
        try:
            return MeetingMembership.objects.get(anonymous_id=anonymous_id)
        except MeetingMembership.DoesNotExist:
            return None

    def update_meeting_membership(self, meeting_membership):
        meeting_membership.status = 'active'
        meeting_membership.joined_at = timezone.now()
        meeting_membership.save()

    def update_meeting_membership_on_disconnect(self, anonymous_id):
        try:
            meeting_membership = MeetingMembership.objects.get(anonymous_id=anonymous_id)
            meeting_membership.status = 'closed'
            meeting_membership.left_at = timezone.now()
            meeting_membership.save()
        except MeetingMembership.DoesNotExist:
            pass
