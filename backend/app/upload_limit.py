from fastapi import HTTPException
from starlette.responses import JSONResponse


class UploadLimitMiddleware:
    """Bound the whole multipart body, including uploads with no Content-Length."""
    def __init__(self, app, maximum):
        self.app = app
        self.maximum = maximum + 64 * 1024  # Multipart envelope allowance.

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] != "POST" or not scope["path"].endswith("/documents"):
            return await self.app(scope, receive, send)
        headers = dict(scope.get("headers", []))
        try:
            declared = int(headers.get(b"content-length", b"0"))
        except ValueError:
            declared = self.maximum + 1
        if declared > self.maximum:
            return await JSONResponse({"detail": "Yêu cầu upload vượt giới hạn dung lượng."}, status_code=413)(scope, receive, send)
        total = 0

        async def bounded_receive():
            nonlocal total
            message = await receive()
            total += len(message.get("body", b""))
            if total > self.maximum:
                raise HTTPException(413, "Yêu cầu upload vượt giới hạn dung lượng.")
            return message

        return await self.app(scope, bounded_receive, send)
