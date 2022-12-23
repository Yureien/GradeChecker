class ScraperException(Exception):
    pass


class AuthenticationException(ScraperException):
    pass


class CaptchaException(ScraperException):
    pass


class UnknownException(ScraperException):
    pass


class ParseException(ScraperException):
    pass
