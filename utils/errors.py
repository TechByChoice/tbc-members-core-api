class CustomException(Exception):
    """
    Custom exception for handling specific errors in the application.

    Attributes:
        message (str): Human readable string describing the exception.
        status_code (int): HTTP status code to return in case of this exception.
        payload (dict, optional): Additional data to include with the exception.
    """
    def __init__(self, message, status_code=None, payload=None):
        self.message = message
        self.status_code = status_code or 400  # Default status code is 400
        self.payload = payload
        super().__init__(self.message)

    def __str__(self):
        return self.message

    def to_dict(self):
        """
        Convert the exception to a dictionary format, useful for JSON responses.

        Returns:
            dict: A dictionary representation of the exception.
        """
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['status'] = self.status_code
        return rv
