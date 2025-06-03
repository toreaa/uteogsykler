"""
Pages module for Konkurranseapp
Each page is a separate module for better organization
"""

from .leaderboard import show_leaderboard_page
from .activities import show_activities_page

__all__ = [
    'show_leaderboard_page',
    'show_activities_page'
]
