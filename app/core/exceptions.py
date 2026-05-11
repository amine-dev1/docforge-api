class CustomAuthException(Exception):
    def __init__(self, message: str, error_type: int = 401):
        self.message = message
        self.error_type = error_type
