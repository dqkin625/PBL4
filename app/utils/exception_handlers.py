from fastapi import Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.utils.response import response_data, StatusMessage

def register_exception_handlers(app):
    # Bắt mọi HTTPException (404, 400, 405, 429, ...)
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        # Mapping message mặc định theo status phổ biến
        default_messages = {
            400: StatusMessage.BAD_REQUEST,
            401: StatusMessage.UNAUTHORIZED,
            403: StatusMessage.FORBIDDEN,
            404: StatusMessage.NOT_FOUND,
            405: StatusMessage.METHOD_NOT_ALLOWED,
            422: StatusMessage.UNPROCESSABLE,
            429: StatusMessage.TOO_MANY_REQUESTS,
        }
        message = exc.detail or default_messages.get(exc.status_code, StatusMessage.SERVER_ERROR)
        return response_data(status_code=exc.status_code, message=message, data=[])

    # Bắt lỗi validate request body/query/path (422)
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # Bạn có thể trả chi tiết lỗi cho client nếu muốn
        errors = exc.errors()
        return response_data(
            status_code=422,
            message=StatusMessage.UNPROCESSABLE,
            data={"errors": errors}
        )

    # Bắt mọi lỗi chưa lường trước (500)
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # Có thể log `exc` tại đây bằng logger của bạn
        return response_data(
            status_code=500,
            message=StatusMessage.SERVER_ERROR,
            data=[]
        )
