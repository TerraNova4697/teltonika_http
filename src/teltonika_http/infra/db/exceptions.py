from src.teltonika_http.util.exceptions import AppError


class ItemNotFoundException(AppError):
    def __init__(
            self, 
            code: str = "NOT_FOUND_ERROR", 
            message: str = "Item not found", 
            status_code: int = 404
        ):
        self.code = code
        self.message = message
        self.status_code = status_code

class RepositoryError(AppError):
    def __init__(
            self, 
            code: str = "SERVER_ERROR", 
            message: str = "Internal server error", 
            status_code: int = 500
        ):
        self.code = code
        self.message = message
        self.status_code = status_code

class ItemExistsException(AppError):
    def __init__(
            self, 
            code: str = "ITEM_EXISTS_CONFLICT", 
            message: str = "Item already exists", 
            status_code: int = 409
        ):
        self.code = code
        self.message = message
        self.status_code = status_code
