from fastapi.responses import JSONResponse
from typing import Any

def response_data(
    status_code: int = 200,
    message: str = "Success",
    data: Any = None,
    source: str | None = None,
):
    if isinstance(data, list):
        count = len(data)
    elif data is None:
        count = 0
        data = []
    else:
        count = 1

    return JSONResponse(
        status_code=status_code,
        content={
            "statusCode": status_code,
            "message": message,
            "source": source,
            "count": count,
            "data": data,
        },
    )


class StatusMessage:
    SUCCESS = "Success"
    BAD_REQUEST = "Bad request"
    UNAUTHORIZED = "Unauthorized"
    FORBIDDEN = "Forbidden"
    NOT_FOUND = "Not found"
    METHOD_NOT_ALLOWED = "Method not allowed"
    UNPROCESSABLE = "Unprocessable entity"
    TOO_MANY_REQUESTS = "Too many requests"
    SERVER_ERROR = "Server error"

