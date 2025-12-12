from django.db import models
from django.contrib.auth.models import User


class ChatRoom(models.Model):
    # 1. 系统分配的唯一 ID：Django 默认会自动创建名为 id 的主键，无需手动编写

    name = models.CharField(max_length=100, unique=True, verbose_name="聊天室名称")
    description = models.TextField(blank=True, verbose_name="聊天室简介")

    # 2. 创建者 ID (关联到用户表)
    # related_name='created_rooms' 让我们可以用 user.created_rooms.all() 查某人建了哪些群
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_rooms', verbose_name="群主")

    # 3. 聊天室密码 (可选)
    # blank=True 表示密码可以为空，为空就是公开群
    room_password = models.CharField(max_length=50, blank=True, verbose_name="进入密码")

    # 4. 成员 (多对多)
    members = models.ManyToManyField(User, related_name='joined_rooms', blank=True, verbose_name="成员")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    # 5. 可扩展属性 (JSONField)
    # 这里利用了 Postgres 的特性，以后想加 "is_muted", "theme_color" 等配置，直接往这里存 JSON 即可
    # 比如: {"theme": "dark", "max_members": 500}
    extra_data = models.JSONField(default=dict, blank=True, verbose_name="扩展属性")

    def __str__(self):
        return self.name


# Message 类不需要改动，保持原样即可
class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"[{self.sender.username}] {self.content[:20]}"