"""
Define common exceptions used when fetching data
"""


class TooManyRequestsError(Exception):

    def __init__(self, *args: object) -> None:
        super().__init__("Too many request error with code 429")

class UnauthorizedError(Exception):

    def __init__(self, *args: object) -> None:
        super().__init__("Unauthorized error with code 401")

class UnknownResponseError(Exception):

    def __init__(self, response) -> None:
        super().__init__(f"Unknown error with response status code {response.status_code}")
