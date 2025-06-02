"""
Error handling og logging for Konkurranseapp
"""

import logging
import traceback
from datetime import datetime
from typing import Optional, Any
from functools import wraps


class AppError(Exception):
    """Base exception class for application errors"""
    
    def __init__(self, message: str, error_code: str = None, details: Any = None):
        self.message = message
        self.error_code = error_code or "GENERIC_ERROR"
        self.details = details
        self.timestamp = datetime.now()
        super().__init__(self.message)


class ValidationError(AppError):
    """Exception for validation errors"""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        super().__init__(message, "VALIDATION_ERROR", {"field": field, "value": value})


class AuthenticationError(AppError):
    """Exception for authentication errors"""
    
    def __init__(self, message: str = "Autentisering feilet"):
        super().__init__(message, "AUTH_ERROR")


class AuthorizationError(AppError):
    """Exception for authorization errors"""
    
    def __init__(self, message: str = "Ikke autorisert"):
        super().__init__(message, "AUTHORIZATION_ERROR")


class DatabaseConnectionError(AppError):
    """Exception for database connection errors"""
    
    def __init__(self, message: str = "Database-tilkobling feilet"):
        super().__init__(message, "DB_CONNECTION_ERROR")


# Configure logging
def setup_logging(level=logging.INFO):
    """Set up application logging"""
    
    # Create logger
    logger = logging.getLogger('konkurranseapp')
    logger.setLevel(level)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    return logger


# Global logger instance
logger = setup_logging()


def log_error(error: Exception, context: str = None, user_id: str = None):
    """
    Log error with context information
    
    Args:
        error: Exception object
        context: Additional context information
        user_id: User ID if available
    """
    error_info = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'context': context,
        'user_id': user_id,
        'timestamp': datetime.now().isoformat()
    }
    
    if hasattr(error, 'error_code'):
        error_info['error_code'] = error.error_code
    
    if hasattr(error, 'details'):
        error_info['details'] = error.details
    
    logger.error(f"Application Error: {error_info}")
    
    # In production, you might want to send this to an external service
    # like Sentry, LogRocket, etc.


def handle_database_error(func):
    """
    Decorator for handling database errors
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Convert common database errors to app-specific errors
            error_message = str(e).lower()
            
            if 'connection' in error_message or 'timeout' in error_message:
                raise DatabaseConnectionError(f"Database tilkobling feilet: {e}")
            elif 'permission' in error_message or 'policy' in error_message:
                raise AuthorizationError(f"Ikke tilgang til ressurs: {e}")
            elif 'duplicate' in error_message or 'unique' in error_message:
                raise ValidationError("Duplisert verdi ikke tillatt", details=str(e))
            else:
                # Log original error and re-raise as generic app error
                log_error(e, context=f"Database operation in {func.__name__}")
                raise AppError(f"Database operasjon feilet: {e}")
    
    return wrapper


def safe_execute(func, default_value=None, context: str = None):
    """
    Safely execute a function and return default value on error
    
    Args:
        func: Function to execute
        default_value: Value to return on error
        context: Context for error logging
        
    Returns:
        Function result or default_value on error
    """
    try:
        return func()
    except Exception as e:
        log_error(e, context=context)
        return default_value


def validate_required_fields(data: dict, required_fields: list) -> None:
    """
    Validate that required fields are present and not empty
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
        
    Raises:
        ValidationError: If any required field is missing or empty
    """
    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Påkrevd felt mangler: {field}", field=field)
        
        if data[field] is None or (isinstance(data[field], str) and data[field].strip() == ""):
            raise ValidationError(f"Påkrevd felt kan ikke være tomt: {field}", field=field, value=data[field])


def validate_email(email: str) -> bool:
    """
    Simple email validation
    
    Args:
        email: Email to validate
        
    Returns:
        True if email format is valid
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_company_code(code: str) -> bool:
    """
    Validate company code format
    
    Args:
        code: Company code to validate
        
    Returns:
        True if format is valid
    """
    import re
    # 6 characters: 2 letters + 2 digits + 1 letter + 1 digit
    pattern = r'^[A-Z]{2}\d{2}[A-Z]\d$'
    return re.match(pattern, code.upper()) is not None


def format_error_for_user(error: Exception) -> str:
    """
    Format error message for display to end users
    
    Args:
        error: Exception object
        
    Returns:
        User-friendly error message
    """
    if isinstance(error, ValidationError):
        return f"Ugyldig data: {error.message}"
    elif isinstance(error, AuthenticationError):
        return "Du må logge inn for å få tilgang"
    elif isinstance(error, AuthorizationError):
        return "Du har ikke tilgang til denne funksjonen"
    elif isinstance(error, DatabaseConnectionError):
        return "Kunne ikke koble til database. Prøv igjen senere."
    elif isinstance(error, AppError):
        return error.message
    else:
        # Don't expose internal errors to users
        log_error(error, context="Unexpected error shown to user")
        return "En uventet feil oppstod. Prøv igjen senere."


# Context manager for error handling in Streamlit
class StreamlitErrorHandler:
    """Context manager for handling errors in Streamlit components"""
    
    def __init__(self, show_error: bool = True, context: str = None):
        self.show_error = show_error
        self.context = context
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            log_error(exc_val, context=self.context)
            
            if self.show_error:
                try:
                    import streamlit as st
                    error_message = format_error_for_user(exc_val)
                    st.error(error_message)
                except ImportError:
                    # Streamlit not available, just print
                    print(f"Error: {format_error_for_user(exc_val)}")
            
            # Return True to suppress the exception
            return True
        
        return False
