from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    def __init__(self, code: str, detail: str, status_code: int = 500):
        self.code = code
        self.detail = detail
        self.status_code = status_code


async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "detail": exc.detail},
    )


async def general_exception_handler(request: Request, exc: Exception):
    from app.core.logging import get_logger
    import traceback

    logger = get_logger(__name__)
    logger.error(f"Unhandled exception: {exc}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"code": "INTERNAL_ERROR", "detail": "内部错误，请查看日志"},
    )


# Standard error codes
ERROR_CODES = {
    "LLM_UNAVAILABLE": ("LLM 服务不可达", 500),
    "EMBEDDING_FAILED": ("向量化失败", 500),
    "SQL_GENERATION_FAILED": ("SQL 生成失败", 400),
    "SQL_EXECUTION_FAILED": ("SQL 执行失败", 400),
    "KNOWLEDGE_NOT_FOUND": ("知识库未找到", 404),
    "SESSION_NOT_FOUND": ("会话不存在", 404),
    "RATE_LIMIT_EXCEEDED": ("请求过于频繁", 429),
    "INVALID_INPUT": ("输入无效", 400),
    "DOCUMENT_TOO_LARGE": ("文档过大", 400),
}
