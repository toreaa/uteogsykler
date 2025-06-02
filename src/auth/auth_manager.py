"""
Authentication manager for Konkurranseapp using Supabase Auth
"""

import streamlit as st
from typing import Optional, Dict, Any
from ..utils.supabase_client import get_supabase
from ..utils.database_helpers import get_db_helper, DatabaseError
from ..utils.error_handler import (
    AuthenticationError, ValidationError, StreamlitErrorHandler,
    validate_email, validate_required_fields, format_error_for_user
)


class AuthManager:
    """Handles authentication and user session management"""
    
    def __init__(self):
        self.supabase = get_supabase()
        self.db = get_db_helper()
    
    def initialize_session(self):
        """Initialize session state for authentication"""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        
        if 'user' not in st.session_state:
            st.session_state.user = None
        
        if 'company' not in st.session_state:
            st.session_state.company = None
    
    def sign_up(self, email: str, password: str, full_name: str, company_code: str = None) -> Dict[str, Any]:
        """
        Register new user with email/password
        
        Args:
            email: User email
            password: User password
            full_name: User's full name
            company_code: Optional company code for joining existing company
            
        Returns:
            Dict with user information
            
        Raises:
            ValidationError: If input validation fails
            AuthenticationError: If signup fails
        """
        # Validate input
        validate_required_fields({
            'email': email,
            'password': password,
            'full_name': full_name
        }, ['email', 'password', 'full_name'])
        
        if not validate_email(email):
            raise ValidationError("Ugyldig e-postadresse", field="email")
        
        if len(password) < 6:
            raise ValidationError("Passord må være minst 6 tegn", field="password")
        
        if len(full_name.strip()) < 2:
            raise ValidationError("Fullt navn må være minst 2 tegn", field="full_name")
        
        try:
            # Sign up with Supabase Auth
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": full_name,
                        "company_code": company_code
                    }
                }
            })
            
            if response.user:
                # User created successfully
                user_data = {
                    'id': response.user.id,
                    'email': response.user.email,
                    'full_name': full_name,
                    'company_code': company_code,
                    'email_confirmed': response.user.email_confirmed_at is not None
                }
                
                return user_data
            else:
                raise AuthenticationError("Kunne ikke opprette bruker")
                
        except Exception as e:
            if "already registered" in str(e).lower():
                raise ValidationError("E-post er allerede registrert", field="email")
            else:
                raise AuthenticationError(f"Registrering feilet: {e}")
    
    def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """
        Sign in user with email/password
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Dict with user information
            
        Raises:
            ValidationError: If input validation fails
            AuthenticationError: If signin fails
        """
        # Validate input
        validate_required_fields({
            'email': email,
            'password': password
        }, ['email', 'password'])
        
        if not validate_email(email):
            raise ValidationError("Ugyldig e-postadresse", field="email")
        
        try:
            # Sign in with Supabase Auth
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user:
                # Get additional user data from our database
                user_profile = self.db.get_user_by_id(response.user.id)
                
                if user_profile:
                    # User exists in our database
                    user_data = {
                        'id': response.user.id,
                        'email': response.user.email,
                        'full_name': user_profile['full_name'],
                        'company_id': user_profile['company_id'],
                        'is_admin': user_profile['is_admin'],
                        'company': user_profile.get('companies', {}),
                        'email_confirmed': response.user.email_confirmed_at is not None
                    }
                    
                    return user_data
                else:
                    # User exists in Auth but not in our database (incomplete registration)
                    raise AuthenticationError("Brukerregistrering ikke fullført. Kontakt support.")
            else:
                raise AuthenticationError("Ugyldig e-post eller passord")
                
        except Exception as e:
            if "invalid" in str(e).lower() or "wrong" in str(e).lower():
                raise AuthenticationError("Ugyldig e-post eller passord")
            else:
                raise AuthenticationError(f"Pålogging feilet: {e}")
    
    def sign_out(self):
        """Sign out current user"""
        try:
            self.supabase.auth.sign_out()
            
            # Clear session state
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.company = None
            
        except Exception as e:
            # Log error but don't fail - user should be signed out locally anyway
            print(f"Warning: Sign out error: {e}")
            
            # Force local sign out
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.company = None
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current authenticated user"""
        try:
            user = self.supabase.auth.get_user()
            
            if user and user.user:
                # Get fresh user data from database
                user_profile = self.db.get_user_by_id(user.user.id)
                
                if user_profile:
                    return {
                        'id': user.user.id,
                        'email': user.user.email,
                        'full_name': user_profile['full_name'],
                        'company_id': user_profile['company_id'],
                        'is_admin': user_profile['is_admin'],
                        'company': user_profile.get('companies', {}),
                        'email_confirmed': user.user.email_confirmed_at is not None
                    }
            
            return None
            
        except Exception as e:
            print(f"Error getting current user: {e}")
            return None
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return st.session_state.get('authenticated', False)
    
    def is_admin(self) -> bool:
        """Check if current user is admin"""
        user = st.session_state.get('user')
        return user and user.get('is_admin', False)
    
    def require_auth(self, admin_required: bool = False):
        """
        Decorator/function to require authentication
        
        Args:
            admin_required: If True, require admin privileges
        """
        if not self.is_authenticated():
            st.error("Du må logge inn for å få tilgang til denne siden")
            st.stop()
        
        if admin_required and not self.is_admin():
            st.error("Du har ikke tilgang til denne funksjonen (kun admin)")
            st.stop()
    
    def update_session(self, user_data: Dict[str, Any]):
        """Update session state with user data"""
        st.session_state.authenticated = True
        st.session_state.user = user_data
        
        if user_data.get('company'):
            st.session_state.company = user_data['company']
    
    def reset_password(self, email: str):
        """
        Send password reset email
        
        Args:
            email: User email address
        """
        if not validate_email(email):
            raise ValidationError("Ugyldig e-postadresse", field="email")
        
        try:
            self.supabase.auth.reset_password_email(email)
            return True
            
        except Exception as e:
            raise AuthenticationError(f"Kunne ikke sende tilbakestilling: {e}")
    
    def complete_user_registration(self, user_id: str, full_name: str, 
                                 company_id: str = None, is_admin: bool = False) -> Dict[str, Any]:
        """
        Complete user registration by creating user profile in database
        
        Args:
            user_id: Supabase Auth user ID
            full_name: User's full name
            company_id: Company ID (optional)
            is_admin: Whether user is admin
            
        Returns:
            User profile data
        """
        try:
            # Get user email from Auth
            auth_user = self.supabase.auth.get_user()
            if not auth_user or not auth_user.user or auth_user.user.id != user_id:
                raise AuthenticationError("Ugyldig bruker-session")
            
            # Create user profile in our database
            user_profile = self.db.create_user(
                user_id=user_id,
                email=auth_user.user.email,
                full_name=full_name,
                company_id=company_id,
                is_admin=is_admin
            )
            
            return user_profile
            
        except DatabaseError as e:
            raise AuthenticationError(f"Kunne ikke fullføre registrering: {e}")


# Global auth manager instance
_auth_manager = None

def get_auth_manager() -> AuthManager:
    """Get global auth manager instance"""
    global _auth_manager
    
    if _auth_manager is None:
        _auth_manager = AuthManager()
    
    return _auth_manager

def require_auth(admin_required: bool = False):
    """Convenience function for requiring authentication"""
    auth = get_auth_manager()
    auth.require_auth(admin_required)

def get_current_user() -> Optional[Dict[str, Any]]:
    """Convenience function for getting current user"""
    auth = get_auth_manager()
    return auth.get_current_user()

def is_authenticated() -> bool:
    """Convenience function for checking authentication"""
    auth = get_auth_manager()
    return auth.is_authenticated()

def is_admin() -> bool:
    """Convenience function for checking admin status"""
    auth = get_auth_manager()
    return auth.is_admin()
