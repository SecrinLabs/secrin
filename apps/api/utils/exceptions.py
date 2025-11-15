from typing import Optional
from fastapi import HTTPException, status


class APIException(HTTPException):    
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        message: str = "An error occurred",
        error: Optional[str] = None
    ):
        detail = {
            "success": False,
            "message": message,
            "error": error
        }
        super().__init__(status_code=status_code, detail=detail)


class BadRequestException(APIException):   
    def __init__(self, message: str = "Bad request", error: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=message,
            error=error
        )


class UnauthorizedException(APIException):    
    def __init__(self, message: str = "Unauthorized", error: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            error=error
        )


class ForbiddenException(APIException):    
    def __init__(self, message: str = "Forbidden", error: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            error=error
        )


class NotFoundException(APIException):    
    def __init__(self, message: str = "Resource not found", error: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            error=error
        )


class ConflictException(APIException):    
    def __init__(self, message: str = "Resource conflict", error: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=message,
            error=error
        )


class InternalServerException(APIException):    
    def __init__(self, message: str = "Internal server error", error: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            error=error
        )
