"""
Pages module for Konkurranseapp
Each page is a separate module for better organization
"""

from .leaderboard import show_leaderboard_page
from .activities import show_activities_page
from .dashboard import show_dashboard_page
from .profile import show_profile_page
from .admin import show_admin_page

__all__ = [
    'show_leaderboard_page',
    'show_activities_page',
    'show_dashboard_page',
    'show_profile_page',
    'show_admin_page'
]
