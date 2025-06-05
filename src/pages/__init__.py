"""
Pages module for Konkurranseapp
Each page is a separate module for better organization
"""
from .leaderboard import show_leaderboard_page
from .activities import show_activities_page
from .dashboard import show_dashboard_page
from .profile import show_profile_page
from .admin import show_admin_page
from .admin_activities import show_admin_activities_page

# Import system admin page with try/except for security
try:
    from .report_analytics import show_analytics_page
except ImportError:
    show_analytics_page = None

__all__ = [
    'show_leaderboard_page',
    'show_activities_page',
    'show_dashboard_page',
    'show_profile_page',
    'show_admin_page',
    'show_admin_activities_page',
    'show_analytics_page'
]
