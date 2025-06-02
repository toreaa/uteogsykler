"""
Streamlit test app for database connection and operations
Deploy this to Streamlit Cloud to test your database setup
"""

import streamlit as st
import sys
import os
from datetime import datetime

# Legg til src-mappen til Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.supabase_client import get_supabase_client
from utils.database_helpers import get_db_helper, DatabaseError
from utils.error_handler import StreamlitErrorHandler, format_error_for_user

st.set_page_config(
    page_title="Konkurranseapp - Database Test",
    page_icon="🧪",
    layout="wide"
)

def test_database_connection():
    """Test database connection"""
    with StreamlitErrorHandler(context="Database Connection Test"):
        client = get_supabase_client()
        success = client.test_connection()
        return success

def test_activities():
    """Test activities retrieval"""
    with StreamlitErrorHandler(context="Activities Test"):
        db = get_db_helper()
        activities = db.get_active_activities()
        return activities

def test_points_calculation(activity_id: str, test_value: float):
    """Test points calculation"""
    with StreamlitErrorHandler(context="Points Calculation Test"):
        db = get_db_helper()
        points = db.calculate_points_for_activity(activity_id, test_value)
        return points

def main():
    st.title("🧪 Konkurranseapp - Database Test")
    st.markdown("---")
    
    # Configuration status
    st.header("📋 Configuration Status")
    
    try:
        from config import config
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("App Name", config.app_name)
            st.metric("App Version", config.app_version)
            
        with col2:
            supabase_url_status = "✅ Configured" if config.supabase_url else "❌ Missing"
            supabase_key_status = "✅ Configured" if config.supabase_anon_key else "❌ Missing"
            
            st.metric("Supabase URL", supabase_url_status)
            st.metric("Supabase Key", supabase_key_status)
        
        config_valid = config.validate_config()
        if config_valid:
            st.success("✅ Configuration is valid")
        else:
            st.error("❌ Configuration is incomplete")
            st.stop()
            
    except Exception as e:
        st.error(f"❌ Configuration error: {format_error_for_user(e)}")
        st.stop()
    
    st.markdown("---")
    
    # Database connection test
    st.header("🔗 Database Connection Test")
    
    if st.button("Test Database Connection", type="primary"):
        with st.spinner("Testing connection..."):
            success = test_database_connection()
            
            if success:
                st.success("✅ Database connection successful!")
            else:
                st.error("❌ Database connection failed")
                st.stop()
    
    st.markdown("---")
    
    # Activities test
    st.header("🏃 Activities Test")
    
    if st.button("Load Activities"):
        with st.spinner("Loading activities..."):
            activities = test_activities()
            
            if activities:
                st.success(f"✅ Found {len(activities)} activities")
                
                # Display activities
                for activity in activities:
                    with st.expander(f"{activity['name']} ({activity['unit']})"):
                        st.write(f"**Description:** {activity['description']}")
                        st.write(f"**Unit:** {activity['unit']}")
                        st.write(f"**Active:** {activity['is_active']}")
                        
                        # Show scoring tiers
                        scoring_tiers = activity['scoring_tiers']['tiers']
                        st.write("**Scoring Tiers:**")
                        for tier in scoring_tiers:
                            min_val = tier['min']
                            max_val = tier.get('max', '∞')
                            points = tier['points']
                            st.write(f"  • {min_val} - {max_val} {activity['unit']} = {points} points")
            else:
                st.warning("⚠️ No activities found")
    
    st.markdown("---")
    
    # Points calculation test
    st.header("🎯 Points Calculation Test")
    
    # Load activities for testing
    try:
        db = get_db_helper()
        activities = db.get_active_activities()
        
        if activities:
            selected_activity = st.selectbox(
                "Select activity to test:",
                activities,
                format_func=lambda x: f"{x['name']} ({x['unit']})"
            )
            
            test_value = st.number_input(
                f"Enter test value ({selected_activity['unit']}):",
                min_value=0.0,
                value=50.0,
                step=1.0
            )
            
            if st.button("Calculate Points"):
                with st.spinner("Calculating..."):
                    points = test_points_calculation(selected_activity['id'], test_value)
                    
                    if points is not None:
                        st.success(f"✅ {test_value} {selected_activity['unit']} = **{points} points**")
                    else:
                        st.error("❌ Points calculation failed")
        else:
            st.info("Load activities first to test points calculation")
            
    except Exception as e:
        st.error(f"Error setting up points test: {format_error_for_user(e)}")
    
    st.markdown("---")
    
    # System information
    st.header("ℹ️ System Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Environment:** Streamlit Cloud")
        st.write("**Timestamp:**", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
    with col2:
        st.write("**Python Version:**", sys.version.split()[0])
        st.write("**Streamlit Version:**", st.__version__)
    
    # Debug information (only if debug mode)
    try:
        if config.debug_mode:
            st.markdown("---")
            st.header("🐛 Debug Information")
            
            with st.expander("Secrets Status"):
                secrets_info = config.get_streamlit_secrets()
                for key, value in secrets_info.items():
                    if 'key' in key.lower():
                        # Don't show actual keys
                        st.write(f"**{key}:** {'✅ Set' if value else '❌ Missing'}")
                    else:
                        st.write(f"**{key}:** {value}")
                        
    except Exception as e:
        st.info("Debug mode not available")

if __name__ == "__main__":
    main()
