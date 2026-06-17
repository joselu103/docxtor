# Exceptions
## Register
class RegisterError(Exception): ...


class DuplicateUserError(RegisterError): ...


## Login
class LoginError(Exception): ...


class UserNotFound(LoginError): ...


class WrongPassword(LoginError): ...


## Refresh
class RefreshError(Exception): ...


class InvalidToken(RefreshError): ...


class InvalidTokenType(RefreshError): ...


class InvalidUserID(RefreshError): ...


class UserNotFound_(
    RefreshError  # '_' in the end to avoid conflict with Login error
): ...
