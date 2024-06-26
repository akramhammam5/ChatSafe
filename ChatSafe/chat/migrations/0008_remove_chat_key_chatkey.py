# Generated by Django 5.0.3 on 2024-05-07 20:53

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0007_chat_key_alter_chat_user1_alter_chat_user2'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='chat',
            name='key',
        ),
        migrations.CreateModel(
            name='ChatKey',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(blank=True, max_length=100)),
                ('key_hash', models.CharField(blank=True, max_length=256)),
                ('chat', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='chat_key', to='chat.chat')),
            ],
        ),
    ]
