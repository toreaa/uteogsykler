"""
Utility modules for database operations and error handling
"""

from .supabase_client import get_supabase_client, get_supabase, test_supabase_connection
from .database_helpers import get_db_helper, DatabaseError
from .error_handler import (
    AppError, ValidationError, AuthenticationError, AuthorizationError,
    DatabaseConnectionError, StreamlitErrorHandler, log_error, 
    validate_required_fields, validate_email, validate_company_code,
    format_error_for_user
)

__all__ = [
    # Supabase client
    'get_supabase_client',
    'get_supabase', 
    'test_supabase_connection',
    
    # Database helpers
    'get_db_helper',
    'DatabaseError',
    
    # Error handling
    'AppError',
    'ValidationError', 
    'AuthenticationError',
    'AuthorizationError',
    'DatabaseConnectionError',
    'StreamlitErrorHandler',
    'log_error',
    'validate_required_fields',
    'validate_email',
    'validate_company_code',
    'format_error_for_user'
]
