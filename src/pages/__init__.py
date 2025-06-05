"""
Pages module - Import all page functions
"""

# Import all page functions
from .activities import show_activities_page
from .leaderboard import show_leaderboard_page
from .dashboard import show_dashboard_page
from .profile import show_profile_page
from .admin import show_admin_page

# Import system admin page with try/except for security
try:
    from .report_analytics import show_analytics_page
except ImportError:
    # System admin analytics not available
    show_analytics_page = None

# Export all functions
__all__ = [
    'show_activities_page',
    'show_leaderboard_page', 
    'show_dashboard_page',
    'show_profile_page',
    'show_admin_page',
    'show_analytics_page'
]
