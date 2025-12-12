from django.contrib import admin
from .models import ChatRoom, Message

# 注册 ChatRoom 模型
@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    # 列表页显示哪些字段：ID、房间名、群主、创建时间
    list_display = ('id', 'name', 'creator', 'created_at')
    # 允许点击哪个字段进入编辑页
    list_display_links = ('id', 'name')
    # 侧边栏筛选器
    list_filter = ('created_at',)
    # 搜索框 (支持搜房间名和群主的名字)
    search_fields = ('name', 'creator__username')

# 注册 Message 模型
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    # 列表页显示：发送者、所属房间、内容片段、时间
    list_display = ('sender', 'room', 'content', 'timestamp')
    # 按时间倒序排列
    ordering = ('-timestamp',)