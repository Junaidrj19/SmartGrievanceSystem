"""Expected domain errors used to keep route error handling predictable."""


class DomainError(Exception):
    """Base class for an expected, user-facing workflow error."""


class ValidationError(DomainError):
    pass


class AuthorizationError(DomainError):
    pass


class InvalidTransitionError(DomainError):
    pass
