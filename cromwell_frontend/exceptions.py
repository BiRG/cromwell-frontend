class NotFoundException(Exception):
    pass


class AuthException(Exception):
    pass


class LoginError(Exception):
    def __init__(self, message, redirect_url=None):
        super(LoginError, self).__init__(message)
        self.redirect_url = redirect_url
