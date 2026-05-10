"""
企业微信消息加解密工具（Phase 1a Stub）

企微消息加解密协议：
- AES-256-CBC 加密
- PKCS#7 填充
- SHA1 签名验证
- XML 消息格式

Phase 1a 仅实现基础 URL 验证 + 消息格式回显，
正式加解密在 Phase 3 接入真实企微应用时启用。
"""

import base64
import hashlib
import struct
import time
from Crypto.Cipher import AES


def pkcs7_pad(data: bytes, block_size: int = 32) -> bytes:
    pad_len = block_size - len(data) % block_size
    return data + bytes([pad_len] * pad_len)


def pkcs7_unpad(data: bytes) -> bytes:
    pad_len = data[-1]
    if pad_len < 1 or pad_len > 32:
        return data
    return data[:-pad_len]


class WeComCrypto:
    """企业微信加解密处理器"""

    def __init__(self, token: str, encoding_aes_key: str, corp_id: str):
        self.token = token
        self.corp_id = corp_id
        # EncodingAESKey 是 Base64 编码的 43 字符密钥，解码后为 32 字节
        self.aes_key = base64.b64decode(encoding_aes_key + "=")

    def verify_signature(
        self, msg_signature: str, timestamp: str, nonce: str, echostr: str
    ) -> bool:
        """验证消息签名"""
        sorted_params = sorted([self.token, timestamp, nonce, echostr])
        sha1 = hashlib.sha1("".join(sorted_params).encode()).hexdigest()
        return sha1 == msg_signature

    def verify_url(self, msg_signature: str, timestamp: str, nonce: str, echostr: str) -> tuple[bool, str]:
        """URL 验证：验证签名 + 解密 echostr"""
        if not self.verify_signature(msg_signature, timestamp, nonce, echostr):
            return False, ""
        plain = self._decrypt(echostr)
        return True, plain

    def decrypt_message(
        self, msg_signature: str, timestamp: str, nonce: str, encrypted_xml: str
    ) -> tuple[bool, str]:
        """解密消息"""
        if not self.verify_signature(msg_signature, timestamp, nonce, encrypted_xml):
            return False, ""
        plain = self._decrypt(encrypted_xml)
        return True, plain

    def encrypt_message(self, reply_xml: str, nonce: str, timestamp: str = None) -> tuple[str, str]:
        """加密回复消息，返回 (encrypted_xml, msg_signature)"""
        if timestamp is None:
            timestamp = str(int(time.time()))
        encrypted = self._encrypt(reply_xml)
        sorted_params = sorted([self.token, timestamp, nonce, encrypted])
        signature = hashlib.sha1("".join(sorted_params).encode()).hexdigest()
        return encrypted, signature

    def _decrypt(self, encrypted_text: str) -> str:
        cipher = AES.new(self.aes_key, AES.MODE_CBC, iv=self.aes_key[:16])
        plain = cipher.decrypt(base64.b64decode(encrypted_text))
        plain = pkcs7_unpad(plain)
        # 格式: random(16) + msg_len(4) + msg + corp_id
        content = plain[16:]
        msg_len = struct.unpack(">I", content[:4])[0]
        msg = content[4: 4 + msg_len].decode("utf-8")
        return msg

    def _encrypt(self, reply_xml: str) -> str:
        # 格式: random(16) + msg_len(4) + msg + corp_id
        random_bytes = base64.b64decode(base64.b64encode(struct.pack("IIII", 0, 0, 0, 0)))[:16]
        msg_bytes = reply_xml.encode("utf-8")
        msg_len = struct.pack(">I", len(msg_bytes))
        corp_bytes = self.corp_id.encode("utf-8")
        plain = random_bytes + msg_len + msg_bytes + corp_bytes
        plain = pkcs7_pad(plain)

        cipher = AES.new(self.aes_key, AES.MODE_CBC, iv=self.aes_key[:16])
        encrypted = cipher.encrypt(plain)
        return base64.b64encode(encrypted).decode()
