import base64
import hashlib
import hmac


def has_valid_line_signature(raw_body: bytes, signature: str | None, channel_secret: str) -> bool:
    if not signature:
        return False
    digest = hmac.new(channel_secret.encode("utf-8"), raw_body, hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode("ascii")
    return hmac.compare_digest(expected, signature)
