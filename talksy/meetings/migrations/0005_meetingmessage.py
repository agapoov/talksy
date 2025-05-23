# Generated by Django 5.1.4 on 2024-12-26 15:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('meetings', '0004_alter_meetingmembership_joined_at'),
    ]

    operations = [
        migrations.CreateModel(
            name='MeetingMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sender_id', models.CharField(max_length=1024)),
                ('encrypted_message', models.TextField(max_length=1024)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('meeting', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='meetings.meeting')),
            ],
        ),
    ]
