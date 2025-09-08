def standard_response(success: bool, message: str, data: dict = None):
    return {
        "success": success,
        "message": message,
        "data": data or {}
    }