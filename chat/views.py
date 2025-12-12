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

# chat/views.py

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
    return render(request, 'chat/lobby.html')

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

    # 获取该房间的历史消息 (时间正序)
    messages = active_room.messages.all().order_by('timestamp')

    context = {
        'joined_rooms': joined_rooms,  # 左侧列表数据
        'active_room': active_room,  # 当前房间信息
        'messages': messages,  # 中间消息历史
        'user': request.user  # 当前登录用户
    }
    return render(request, 'chat/chat.html', context)


# 2. 发送消息 API (供 JS 调用)
@login_required
@require_POST
def send_message_api(request):
    try:
        data = json.loads(request.body)
        room_id = data.get('room_id')
        content = data.get('content')

        if not content:
            return JsonResponse({'success': False, 'error': '内容不能为空'})

        room = ChatRoom.objects.get(id=room_id)

        # 存入数据库
        msg = Message.objects.create(
            room=room,
            sender=request.user,
            content=content
        )

        # 返回成功信息，包含刚存入的时间，方便前端显示
        return JsonResponse({
            'success': True,
            'timestamp': msg.timestamp.strftime("%H:%M"),
            'sender': msg.sender.username
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def get_messages_api(request):
    # 获取前端传来的房间ID和最后一条消息的ID
    room_id = request.GET.get('room_id')
    last_message_id = request.GET.get('last_message_id', 0) # 默认为0

    if not room_id:
        return JsonResponse({'success': False})

    try:
        # 核心逻辑：只查 ID 比 last_message_id 大的消息
        # id__gt 是 Django 的语法，意思是 ID Greater Than (大于)
        new_messages = Message.objects.filter(
            room_id=room_id,
            id__gt=last_message_id
        ).order_by('timestamp')

        # 把消息转换成 JSON 格式列表
        messages_list = []
        for msg in new_messages:
            messages_list.append({
                'id': msg.id,
                'sender': msg.sender.username,
                'content': msg.content,
                'timestamp': msg.timestamp.strftime("%H:%M"),
                'is_my_msg': msg.sender == request.user # 标记是不是我发的
            })

        return JsonResponse({'success': True, 'messages': messages_list})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})