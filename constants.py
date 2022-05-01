PORT = 12345
SECRET_LENGTH = 8
EXPIRATION_TIME = 60

SERVER_ACCOUNT_EMAIL = "testermail082@gmail.com"
SERVER_ACCOUNT_PASSWORD = "0vx3extensive)"

class Instruction:
    GET_SECRET = "getsecret"
    VERIFY = "verify"


class ErrorMessage:
    NO_ERROR = "No error."
    NO_CONNECTION = "No internet connection present."
    INVALID_CODE = "Invalid code."
    INVALID_EMAIL = "Invalid email address."
    INVALID_INPUT = "Invalid input."