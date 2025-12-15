import json
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse # <--- 引入这个

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login,logout
from .models import ChatRoom
from django.views.decorators.http import require_POST
from .models import ChatRoom, Message
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ChatRoom #
from django.contrib.auth.models import User
# chat/views.py

import json
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncHour
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ChatRoom, Message

def login_view(request):
    # 1. 如果用户已登录 (比如打开页面时 session 还在)
    # if request.user.is_authenticated:
    #     if request.user.joined_rooms.exists():
    #         # 取出该用户加入的第一个房间
    #         latest_room = request.user.joined_rooms.first()
    #         return redirect('chat_room', room_name=latest_room.name)
    #     else:
    #         return redirect('lobby')

    # 2. 处理提交的登录表单
    if request.method == 'POST':
        username_data = request.POST.get('username')
        password_data = request.POST.get('password')
        user = authenticate(request, username=username_data, password=password_data)

        if user is not None:
            login(request, user)
            # 登录成功！再次检查有没有房间
            if user.joined_rooms.exists():
                latest_room = user.joined_rooms.first()
                return redirect('chat_room', room_name=latest_room.name)
            else:
                return redirect('lobby')
        else:
            return render(request, 'chat/login.html', {'error': '账号或密码错误'})

    return render(request, 'chat/login.html')


def register_view(request):
    # 如果是 AJAX 请求 (通过 JS 发起的 POST)
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # 解析前端传来的 JSON 数据
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        # 1. 校验用户名
        if User.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'error': '该用户名已被注册'})

        # 2. 校验密码长度
        if len(password) < 6 or len(password) > 20:
            return JsonResponse({'success': False, 'error': '密码长度需在6-20位之间'})

        # 3. 创建用户
        try:
            user = User.objects.create_user(username=username, password=password)
            login(request, user)  # 自动登录

            # 4. 返回成功信号和数据给前端 JS
            return JsonResponse({
                'success': True,
                'username': user.username,
                'uid': user.id,
                'password_backup': password,  # 仅用于弹窗显示
                'redirect_url': '/lobby/'  # 告诉前端下一步去哪
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': '注册失败，请稍后重试'})

    # 如果是普通 GET 请求，显示注册页面
    return render(request, 'chat/register.html')


@login_required
def lobby_view(request):
    # 获取当前用户加入的所有房间
    # 根据你在 chat_view 中使用的 request.user.joined_rooms 逻辑
    joined_rooms = request.user.joined_rooms.all()

    context = {
        'rooms': joined_rooms
    }
    return render(request, 'chat/lobby.html', context)
    # === 修改部分结束 ===

def logout_view(request):
    logout(request) # 清除 session
    return redirect('login') # 踢回登录页


@login_required
def create_room_view(request):
    # 只处理 AJAX POST 请求
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            room_name = data.get('name')
            password = data.get('password')
            confirm_password = data.get('confirm_password')

            # 1. 基础校验
            if not room_name:
                return JsonResponse({'success': False, 'error': '房间名不能为空'})

            # 2. 密码一致性校验
            if password != confirm_password:
                return JsonResponse({'success': False, 'error': '两次输入的密码不一致'})

            # 3. 房间名查重
            if ChatRoom.objects.filter(name=room_name).exists():
                return JsonResponse({'success': False, 'error': '该房间名已被占用'})

            # 4. 创建房间
            new_room = ChatRoom.objects.create(
                name=room_name,
                creator=request.user,
                room_password=password if password else ""
            )
            new_room.members.add(request.user)

            return JsonResponse({'success': True, 'room_name': new_room.name})

        except Exception as e:
            return JsonResponse({'success': False, 'error': '系统错误，请稍后重试'})

    # 如果有人直接访问这个网址，就踢回大厅
    return redirect('lobby')


# chat/views.py

# chat/views.py

@login_required
def join_room_view(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            room_name = data.get('room_name')
            password = data.get('password')

            # 1. 找房间
            try:
                room = ChatRoom.objects.get(name=room_name)
            except ChatRoom.DoesNotExist:
                return JsonResponse({'success': False, 'error': f'未找到名称为 "{room_name}" 的聊天室'})

            # 2. 【核心修改】检查是否已经是成员
            if request.user in room.members.all():
                # 改动：不再报错，而是直接返回成功，带上房间名，让前端直接跳转
                return JsonResponse({'success': True, 'room_name': room.name})

            # 3. 校验密码 (如果是新加入)
            if room.room_password and room.room_password != password:
                return JsonResponse({'success': False, 'error': '加入密码错误'})

            # 4. 加入
            room.members.add(request.user)
            return JsonResponse({'success': True, 'room_name': room.name})

        except Exception as e:
            return JsonResponse({'success': False, 'error': '系统错误'})

    return redirect('lobby')


@login_required
def chat_view(request, room_name=None):
    # 获取用户加入的所有房间 (用于左侧列表)
    joined_rooms = request.user.joined_rooms.all().order_by('-created_at')

    # 如果用户没有加入任何房间，直接回大厅
    if not joined_rooms.exists():
        return redirect('lobby')

    # 如果 URL 没传房间名，默认显示列表里的第一个房间
    if not room_name:
        return redirect('chat_room', room_name=joined_rooms.first().name)

    # 获取当前选中的房间对象
    try:
        active_room = ChatRoom.objects.get(name=room_name)
    except ChatRoom.DoesNotExist:
        return redirect('lobby')

    # 安全检查：如果我不在这个群里，不能看消息
    if request.user not in active_room.members.all():
        return redirect('lobby')

    # 1. 获取该房间的消息总数
    total_count = active_room.messages.count()

    # 2. 只取最后 10 条消息 (初始显示)
    # 先倒序取前10，再反转回正序
    recent_messages = active_room.messages.order_by('-timestamp')[:10]

    # 【核心修复】将迭代器转为列表 (list)，这样才能在 Python 中获取最后一个元素的 ID
    messages = list(reversed(recent_messages))

    # 【核心修复】在后端直接计算出最后一条消息的 ID
    # 避免前端模板因无法解析 iterator.last 而得到默认值 0
    if messages:
        last_id = messages[-1].id
    else:
        last_id = 0

    # 3. 只要总数超过 10 条，就显示“查看历史”按钮
    has_more = total_count > 10

    context = {
        'joined_rooms': joined_rooms,
        'active_room': active_room,
        'messages': messages,
        'user': request.user,
        'has_more': has_more,
        'last_id': last_id  # 【重要】将计算好的 ID 传给前端
    }

    return render(request, 'chat/chat.html', context)

# 2. 发送消息 API (供 JS 调用)
@login_required
@require_POST
def send_message_api(request):
    try:
        # 注意：不再使用 json.loads(request.body)
        # 前端改用 FormData 提交后，数据在 request.POST 和 request.FILES 中

        room_id = request.POST.get('room_id')
        content = request.POST.get('content', '').strip()
        uploaded_file = request.FILES.get('file')  # 获取上传的文件

        # 校验：既没文字也没文件，才算空
        if not content and not uploaded_file:
            return JsonResponse({'success': False, 'error': '内容不能为空'})

        room = ChatRoom.objects.get(id=room_id)

        msg = Message.objects.create(
            room=room,
            sender=request.user,
            content=content,
            file=uploaded_file  # 保存文件
        )

        return JsonResponse({
            'success': True,
            'id': msg.id,
            'timestamp': msg.timestamp.strftime("%H:%M"),
            'sender': msg.sender.username,
            # 返回文件 URL 给前端 (如果有的话)
            'file_url': msg.file.url if msg.file else None
        })
    except Exception as e:
        print(f"Send Error: {e}")  # 打印错误方便调试
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def get_messages_api(request):
    room_id = request.GET.get('room_id')
    last_message_id = request.GET.get('last_message_id', 0)

    if not room_id: return JsonResponse({'success': False})

    try:
        last_message_id = int(last_message_id)
        new_messages = Message.objects.filter(
            room_id=room_id,
            id__gt=last_message_id
        ).order_by('timestamp')

        messages_list = []
        for msg in new_messages:
            messages_list.append({
                'id': msg.id,
                'sender': msg.sender.username,
                'content': msg.content if msg.content else "",  # 处理 None
                'timestamp': msg.timestamp.strftime("%H:%M"),
                'is_my_msg': msg.sender == request.user,
                # === 新增 ===
                'file_url': msg.file.url if msg.file else None,
                'file_name': msg.file.name.split('/')[-1] if msg.file else ""
            })

        return JsonResponse({'success': True, 'messages': messages_list})
    except Exception as e:
        print(f"Polling Error: {e}")
        return JsonResponse({'success': False, 'messages': []})
# === 管理大厅：列出我创建的房间 ===
@login_required
def manage_dashboard(request):
    # 查询当前用户作为 creator (群主) 的所有房间
    # 你的模型中 related_name='created_rooms'，也可以用 request.user.created_rooms.all()
    rooms = ChatRoom.objects.filter(creator=request.user)  #
    return render(request, 'chat/manage_list.html', {'rooms': rooms})


# === 房间设置：修改密码等 ===
@login_required
def edit_room(request, room_name):
    room = get_object_or_404(ChatRoom, name=room_name)

    if room.creator != request.user:
        messages.error(request, "你没有权限管理此房间")
        return redirect('lobby')

    # === 表单处理逻辑 (保持不变) ===
    if request.method == 'POST':
        new_name = request.POST.get('name', '').strip()
        new_password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if new_name and new_name != room.name:
            if ChatRoom.objects.filter(name=new_name).exclude(id=room.id).exists():
                messages.error(request, "该房间名称已存在，请换一个")
                return render(request, 'chat/manage_edit.html', {'room': room})
            else:
                room.name = new_name
                messages.success(request, "房间名称已更新")
                room.save()
                return redirect('edit_room', room_name=room.name)

        if new_password:
            if new_password != confirm_password:
                messages.error(request, "两次输入的密码不一致")
            else:
                room.room_password = new_password
                room.save()
                messages.success(request, "房间密码已更新")

    # === 数据统计逻辑 (核心修改) ===
    now = timezone.now()
    yesterday = now - timedelta(days=1)

    recent_msgs = Message.objects.filter(room=room, timestamp__gte=yesterday)

    # 1. 用户发言统计
    user_stats = recent_msgs.values('sender__username').annotate(count=Count('id')).order_by('-count')
    user_labels = [item['sender__username'] for item in user_stats]
    user_data = [item['count'] for item in user_stats]

    # 2. 活跃时段统计
    time_stats = recent_msgs.annotate(hour=TruncHour('timestamp')).values('hour').annotate(count=Count('id')).order_by(
        'hour')

    time_labels = []
    time_data = []

    for item in time_stats:
        # === 修复点开始 ===
        # 因为 settings.py 中 USE_TZ = False，这里的 item['hour'] 已经是 naive datetime
        # 直接拿来用，不用转换
        local_time = item['hour']
        # === 修复点结束 ===

        time_labels.append(local_time.strftime("%H:%M"))
        time_data.append(item['count'])

    context = {
        'room': room,
        'user_labels': json.dumps(user_labels),
        'user_data': json.dumps(user_data),
        'time_labels': json.dumps(time_labels),
        'time_data': json.dumps(time_data),
    }

    return render(request, 'chat/manage_edit.html', context)
# === 成员管理：查看和移除成员 ===
@login_required
def manage_members(request, room_name):
    room = get_object_or_404(ChatRoom, name=room_name)  #

    if room.creator != request.user:  #
        return redirect('lobby')

    return render(request, 'chat/manage_members.html', {'room': room})


# === 踢人逻辑 ===
@login_required
def kick_member(request, room_name, user_id):
    room = get_object_or_404(ChatRoom, name=room_name)  #
    user_to_kick = get_object_or_404(User, id=user_id)

    # 只有群主可以踢人，且不能踢自己
    if room.creator == request.user and user_to_kick != room.creator:  #
        room.members.remove(user_to_kick)  #
        messages.success(request, f"用户 {user_to_kick.username} 已被移除")

    return redirect('manage_members', room_name=room_name)


@login_required
def get_history_messages_api(request):
    room_id = request.GET.get('room_id')
    first_msg_id = request.GET.get('first_msg_id')
    limit = 50

    # 1. 基础检查
    if not room_id or not first_msg_id:
        return JsonResponse({'success': False, 'error': '缺少参数'})

    try:
        # === 修复点：尝试把 ID 转为整数，防止前端传 "null" 或非数字导致崩溃 ===
        try:
            first_msg_id = int(first_msg_id)
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': '无效的消息ID'})

        # 2. 查询逻辑 (保持不变)
        previous_messages_query = Message.objects.filter(
            room_id=room_id,
            id__lt=first_msg_id  # 这里现在肯定是安全的整数了
        ).order_by('-timestamp')[:(limit + 1)]

        previous_messages_list = list(previous_messages_query)

        if len(previous_messages_list) > limit:
            has_more = True
            messages_to_return = previous_messages_list[:limit]
        else:
            has_more = False
            messages_to_return = previous_messages_list

        messages_to_return.reverse()

        messages_data = []
        for msg in messages_to_return:
            messages_data.append({
                'id': msg.id,
                'sender': msg.sender.username,
                'content': msg.content if msg.content else "",
                'timestamp': msg.timestamp.strftime("%H:%M"),
                'is_my_msg': msg.sender == request.user,
                # === 新增 ===
                'file_url': msg.file.url if msg.file else None,
                'file_name': msg.file.name.split('/')[-1] if msg.file else ""
            })

        return JsonResponse({
            'success': True,
            'messages': messages_data,
            'has_more': has_more
        })

    except Exception as e:
        # 打印错误到后台终端，方便调试
        print(f"获取历史消息报错: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

# chat/views.py

@login_required
def manage_messages(request, room_name):
    room = get_object_or_404(ChatRoom, name=room_name)

    # 权限校验
    if room.creator != request.user:
        messages.error(request, "你没有权限管理此房间")
        return redirect('lobby')

    # 获取该房间所有消息，按时间倒序排列（最新的在最前）
    room_messages = room.messages.all().order_by('-timestamp')

    return render(request, 'chat/manage_messages.html', {
        'room': room,
        'messages_list': room_messages
    })

@login_required
@require_POST
def delete_messages(request, room_name):
    room = get_object_or_404(ChatRoom, name=room_name)

    if room.creator != request.user:
        return redirect('lobby')

    # 获取前端勾选的所有消息ID (checkbox name="message_ids")
    msg_ids = request.POST.getlist('message_ids')

    if msg_ids:
        # 安全删除：确保这些消息确实属于当前房间
        deleted_count, _ = Message.objects.filter(room=room, id__in=msg_ids).delete()
        messages.success(request, f"成功删除了 {deleted_count} 条消息")
    else:
        messages.warning(request, "未选择任何消息")

    return redirect('manage_messages', room_name=room_name)