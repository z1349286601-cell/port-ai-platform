"""
企业微信 Bot 回调处理（Phase 1a Stub）

核心流程：
1. GET  /wecom/callback  → echostr 验证（URL 校验）
2. POST /wecom/callback  → 解密 XML → 提取用户消息 → 调用后端管线 → 回复 XML

Phase 1a 交付状态: 仅验证 webhook 收发消息可通，不做 SSE 流式推送。
Phase 3 实现正式适配（SSE → 分条发送，消息模板，卡片消息等）。
"""

import hashlib
import time
import xml.etree.ElementTree as ET
from typing import Optional

from .wecom_crypto import WeComCrypto


def _build_text_reply(to_user: str, from_user: str, content: str) -> str:
    """构造企业微信文本回复 XML"""
    create_time = int(time.time())
    return (
        "<xml>"
        f"<ToUserName><![CDATA[{to_user}]]></ToUserName>"
        f"<FromUserName><![CDATA[{from_user}]]></FromUserName>"
        f"<CreateTime>{create_time}</CreateTime>"
        "<MsgType><![CDATA[text]]></MsgType>"
        f"<Content><![CDATA[{content}]]></Content>"
        "</xml>"
    )


def _extract_message(xml_body: str) -> Optional[dict]:
    """从企微 XML 中提取用户消息"""
    try:
        root = ET.fromstring(xml_body)
        msg_type = root.find("MsgType")
        content = root.find("Content")
        from_user = root.find("FromUserName")
        to_user = root.find("ToUserName")

        if msg_type is not None and msg_type.text == "text" and content is not None:
            return {
                "from_user": from_user.text if from_user is not None else "",
                "to_user": to_user.text if to_user is not None else "",
                "content": content.text or "",
                "msg_type": "text",
            }
    except ET.ParseError:
        pass
    return None


class WeComBot:
    """企业微信机器人回调处理器"""

    def __init__(self, token: str, encoding_aes_key: str, corp_id: str):
        self.crypto = WeComCrypto(token, encoding_aes_key, corp_id)
        self.token = token

    async def handle_verify(self, msg_signature: str, timestamp: str, nonce: str, echostr: str) -> str:
        """处理 URL 验证请求（GET 回调）"""
        ok, plain = self.crypto.verify_url(msg_signature, timestamp, nonce, echostr)
        return plain if ok else ""

    async def handle_message(
        self,
        msg_signature: str,
        timestamp: str,
        nonce: str,
        xml_body: str,
    ) -> Optional[str]:
        """
        处理消息回调（POST 回调）。

        返回: 加密后的回复 XML，或 None（不回复）
        """
        # 1. 解密
        ok, plain = self.crypto.decrypt_message(msg_signature, timestamp, nonce, xml_body)
        if not ok:
            return None

        # 2. 提取消息
        msg = _extract_message(plain)
        if not msg:
            return None

        # 3. 调用后端管线（Phase 1a Stub: 回显消息内容）
        # Phase 3 正式适配: 调用 ConversationManager 获取完整回复
        reply_content = f"[企微Bot Phase 1a Stub] 收到消息: {msg['content'][:200]}"

        # 4. 构造回复 XML
        reply_xml = _build_text_reply(msg["from_user"], msg["to_user"], reply_content)

        # 5. 加密回复
        encrypted, _ = self.crypto.encrypt_message(reply_xml, nonce, timestamp)
        return encrypted
