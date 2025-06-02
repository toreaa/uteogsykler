"""
Authentication module for Konkurranseapp
"""

from .auth_manager import (
    AuthManager, get_auth_manager, require_auth, 
    get_current_user, is_authenticated, is_admin
)
from .auth_components import (
    render_login_form, render_signup_form, render_logout_button,
    render_user_info, render_auth_tabs, render_company_selection,
    render_company_creation_form, render_company_join_form,
    check_authentication_status
)

__all__ = [
    # Auth Manager
    'AuthManager',
    'get_auth_manager',
    'require_auth',
    'get_current_user', 
    'is_authenticated',
    'is_admin',
    
    # Auth Components
    'render_login_form',
    'render_signup_form', 
    'render_logout_button',
    'render_user_info',
    'render_auth_tabs',
    'render_company_selection',
    'render_company_creation_form',
    'render_company_join_form',
    'check_authentication_status'
]
