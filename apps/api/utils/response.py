from typing import Any, Optional
from fastapi import status


class APIResponse:    
    @staticmethod
    def success(
        data: Any = None,
        message: str = "Success",
        status_code: int = status.HTTP_200_OK
    ) -> dict:
        return {
            "success": True,
            "message": message,
            "data": data,
            "status_code": status_code
        }
    
    @staticmethod
    def error(
        message: str = "An error occurred",
        error: Optional[str] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ) -> dict:
        response = {
            "success": False,
            "message": message,
            "data": None,
            "status_code": status_code
        }
        if error:
            response["error"] = error
        return response
