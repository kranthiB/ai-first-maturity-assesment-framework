"""
Custom exceptions for the AFS Assessment Framework.
"""


class AFSException(Exception):
    """Base exception for AFS Assessment Framework."""
    pass


class ValidationError(AFSException):
    """Raised when data validation fails."""
    pass


class AssessmentError(AFSException):
    """Raised when assessment operations fail."""
    pass


class ScoringError(AFSException):
    """Raised when scoring calculations fail."""
    pass


class RecommendationError(AFSException):
    """Raised when recommendation generation fails."""
    pass


class DatabaseError(AFSException):
    """Raised when database operations fail."""
    pass


class ConfigurationError(AFSException):
    """Raised when configuration is invalid."""
    pass


class BusinessLogicError(AFSException):
    """Raised when business logic rules are violated."""
    pass


class AuthenticationError(AFSException):
    """Raised when authentication fails."""
    pass


class AuthorizationError(AFSException):
    """Raised when authorization fails."""
    pass


class ExportError(AFSException):
    """Raised when data export operations fail."""
    pass


class ServiceError(AFSException):
    """Raised when service operations fail."""
    pass


class AnalyticsError(AFSException):
    """Raised when analytics operations fail."""
    pass


class NotFoundError(AFSException):
    """Raised when a requested resource is not found."""
    pass
