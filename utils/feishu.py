import requests
import hashlib
import os
import json
from datetime import datetime

def push_to_webhook(data, config):
    """推送消息到飞书webhook（带去重机制）"""
    webhook_url = config.get('webhook_url')
    if not webhook_url:
        print("[ERROR] 未配置Webhook URL")
        return False

    # 生成消息唯一标识（基于标题和链接）
    message_id = generate_message_id(data)

    # 检查是否已推送过
    if is_already_sent(message_id):
        print(f"[WARN] 消息已推送过，跳过重复推送: {data.get('title', '')[:50]}...")
        return True  # 返回True避免重复处理

    try:
        print("[DEBUG] 推送JSON到webhook:", data)
        response = requests.post(webhook_url, json=data)
        response.raise_for_status()

        result = response.json()
        if result.get('code') == 0:
            # 记录已推送的消息
            mark_as_sent(message_id, data)
            print("[INFO] 飞书推送成功！")
            return True
        else:
            print(f"[ERROR] 飞书推送失败: {result}")
            return False

    except Exception as e:
        print(f"[ERROR] 飞书推送异常: {str(e)}")
        return False

def generate_message_id(data):
    """生成消息唯一标识"""
    # 使用标题和原文链接生成唯一ID
    title = data.get('title', '')
    link = data.get('original_link', '')
    content = f"{title}|{link}"
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def is_already_sent(message_id):
    """检查消息是否已推送过"""
    sent_file = 'logs/sent_messages.json'

    if not os.path.exists(sent_file):
        return False

    try:
        with open(sent_file, 'r', encoding='utf-8') as f:
            sent_messages = json.load(f)

        # 检查是否在24小时内推送过
        if message_id in sent_messages:
            sent_time = datetime.fromisoformat(sent_messages[message_id]['timestamp'])
            now = datetime.now()
            hours_diff = (now - sent_time).total_seconds() / 3600

            if hours_diff < 24:
                return True
            else:
                # 超过24小时，删除旧记录
                del sent_messages[message_id]
                with open(sent_file, 'w', encoding='utf-8') as f:
                    json.dump(sent_messages, f, ensure_ascii=False, indent=2)

        return False

    except Exception as e:
        print(f"[WARN] 检查重复推送失败: {e}")
        return False

def mark_as_sent(message_id, data):
    """标记消息为已推送"""
    sent_file = 'logs/sent_messages.json'

    # 确保logs目录存在
    os.makedirs('logs', exist_ok=True)

    try:
        # 读取现有记录
        sent_messages = {}
        if os.path.exists(sent_file):
            with open(sent_file, 'r', encoding='utf-8') as f:
                sent_messages = json.load(f)

        # 添加新记录
        sent_messages[message_id] = {
            'timestamp': datetime.now().isoformat(),
            'title': data.get('title', ''),
            'link': data.get('original_link', '')
        }

        # 清理超过7天的旧记录
        now = datetime.now()
        to_remove = []
        for msg_id, msg_data in sent_messages.items():
            try:
                sent_time = datetime.fromisoformat(msg_data['timestamp'])
                days_diff = (now - sent_time).days
                if days_diff > 7:
                    to_remove.append(msg_id)
            except:
                to_remove.append(msg_id)  # 删除格式错误的记录

        for msg_id in to_remove:
            del sent_messages[msg_id]

        # 保存记录
        with open(sent_file, 'w', encoding='utf-8') as f:
            json.dump(sent_messages, f, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"[WARN] 记录推送状态失败: {e}")
