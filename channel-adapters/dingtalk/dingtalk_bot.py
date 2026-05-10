"""
钉钉 Bot 回调处理（Phase 1a Stub）

核心流程：
1. POST /dingtalk/callback → 验证签名 → 提取用户消息 → 调用后端管线 → 回复 JSON

Phase 1a 交付状态: 仅验证 webhook 收发消息可通，不做 SSE 流式推送。
Phase 3 实现正式适配。

钉钉消息格式参考: https://open.dingtalk.com/document/orgapp/receive-messages
"""

import hashlib
import hmac
import json
import time
from typing import Optional


class DingTalkBot:
    """钉钉机器人回调处理器"""

    def __init__(self, app_secret: str = "", robot_code: str = ""):
        self.app_secret = app_secret
        self.robot_code = robot_code

    def verify_signature(self, timestamp: str, sign: str) -> bool:
        """验证钉钉签名（HMAC-SHA256）"""
        if not self.app_secret:
            return True  # Phase 1a Stub: 未配置 secret 时跳过验证
        string_to_sign = f"{timestamp}\n{self.app_secret}"
        hmac_code = hmac.new(
            self.app_secret.encode(),
            string_to_sign.encode(),
            digestmod=hashlib.sha256,
        )
        expected = hmac_code.hexdigest()
        return hmac.compare_digest(sign, expected)

    async def handle_message(self, body: dict) -> Optional[dict]:
        """
        处理钉钉消息回调。

        请求体格式:
        {
            "conversationType": "1",  # 1=单聊, 2=群聊
            "senderId": "user123",
            "senderNick": "用户昵称",
            "sessionWebhook": "https://oapi.dingtalk.com/robot/send?...",
            "text": { "content": "用户消息文本" }
        }

        返回: 回复 JSON 或 None
        """
        # 1. 提取消息
        text_content = body.get("text", {}).get("content", "")
        sender_id = body.get("senderId", "")
        session_webhook = body.get("sessionWebhook", "")

        if not text_content.strip():
            return None

        # 2. 调用后端管线（Phase 1a Stub: 回显消息内容）
        # Phase 3 正式适配: 调用 ConversationManager 获取完整回复
        reply = f"[钉钉Bot Phase 1a Stub] 收到消息: {text_content[:200]}"

        # 3. 构造回复（钉钉 Outgoing Robot 格式）
        return {
            "msgtype": "text",
            "text": {
                "content": reply,
            },
            "at": {
                "atUserIds": [sender_id] if sender_id else [],
            },
        }
