"""
Test script for database connection and basic operations
Kjør: python src/test_database_connection.py
"""

import sys
import os
from datetime import date

# Legg til src-mappen til Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.supabase_client import get_supabase_client, test_supabase_connection
from utils.database_helpers import get_db_helper, DatabaseError
from utils.error_handler import StreamlitErrorHandler, log_error


def test_basic_connection():
    """Test grunnleggende database-tilkobling"""
    print("=== Testing Basic Database Connection ===")
    
    try:
        client = get_supabase_client()
        success = client.test_connection()
        
        if success:
            print("✅ Database-tilkobling fungerer")
            return True
        else:
            print("❌ Database-tilkobling feilet")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False


def test_activities():
    """Test henting av aktiviteter"""
    print("\n=== Testing Activities ===")
    
    try:
        db = get_db_helper()
        activities = db.get_active_activities()
        
        print(f"Fant {len(activities)} aktive aktiviteter:")
        for activity in activities:
            print(f"  - {activity['name']} ({activity['unit']})")
            
        return True
        
    except DatabaseError as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_points_calculation():
    """Test poengberegning for aktiviteter"""
    print("\n=== Testing Points Calculation ===")
    
    try:
        db = get_db_helper()
        activities = db.get_active_activities()
        
        if not activities:
            print("❌ Ingen aktiviteter funnet")
            return False
        
        # Test poengberegning for første aktivitet
        activity = activities[0]
        activity_id = activity['id']
        activity_name = activity['name']
        
        print(f"Testing poengberegning for {activity_name}:")
        
        test_values = [10, 50, 100, 200]
        for value in test_values:
            points = db.calculate_points_for_activity(activity_id, value)
            print(f"  {value} {activity['unit']} = {points} poeng")
        
        return True
        
    except Exception as e:
        print(f"❌ Points calculation error: {e}")
        return False


def test_company_operations():
    """Test bedriftsoperasjoner (read-only)"""
    print("\n=== Testing Company Operations ===")
    
    try:
        db = get_db_helper()
        
        # Test å hente en ikke-eksisterende bedrift
        company = db.get_company_by_code("TEST99")
        
        if company is None:
            print("✅ Korrekt håndtering av ikke-eksisterende bedrift")
        else:
            print(f"ℹ️  Uventet: Fant bedrift med kode TEST99: {company['name']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Company operations error: {e}")
        return False


def test_error_handling():
    """Test error handling"""
    print("\n=== Testing Error Handling ===")
    
    try:
        db = get_db_helper()
        
        # Test invalid activity ID
        try:
            points = db.calculate_points_for_activity("invalid-uuid", 50)
            print("❌ Should have thrown error for invalid activity ID")
            return False
        except DatabaseError:
            print("✅ Korrekt error handling for ugyldig aktivitet-ID")
        
        # Test invalid user ID
        try:
            user = db.get_user_by_id("invalid-uuid")
            if user is None:
                print("✅ Korrekt håndtering av ugyldig bruker-ID")
            else:
                print("❌ Uventet: Fant bruker med ugyldig ID")
        except DatabaseError:
            print("✅ Korrekt error handling for bruker-ID")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


def test_competition_operations():
    """Test konkurranseoperasjoner (read-only)"""
    print("\n=== Testing Competition Operations ===")
    
    try:
        db = get_db_helper()
        
        # Test henting av leaderboard for ikke-eksisterende konkurranse
        fake_competition_id = "00000000-0000-0000-0000-000000000000"
        leaderboard = db.get_leaderboard_for_competition(fake_competition_id)
        
        if isinstance(leaderboard, list) and len(leaderboard) == 0:
            print("✅ Korrekt håndtering av tom leaderboard")
        else:
            print(f"❌ Uventet leaderboard-resultat: {leaderboard}")
        
        return True
        
    except Exception as e:
        print(f"❌ Competition operations error: {e}")
        return False


def run_full_test_suite():
    """Kjør alle tester"""
    print("🧪 KONKURRANSEAPP - DATABASE TEST SUITE")
    print("=" * 50)
    
    tests = [
        ("Basic Connection", test_basic_connection),
        ("Activities", test_activities),
        ("Points Calculation", test_points_calculation),
        ("Company Operations", test_company_operations),
        ("Error Handling", test_error_handling),
        ("Competition Operations", test_competition_operations)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Sammendrag
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8} {test_name}")
        if result:
            passed += 1
    
    print("-" * 50)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Database setup is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check configuration and database setup.")
        return False


def test_minimal_connection():
    """Minimal test for quick verification"""
    print("🔍 Quick Connection Test")
    print("-" * 30)
    
    success = test_supabase_connection()
    
    if success:
        print("✅ Database connection OK")
        
        # Quick activity test
        try:
            db = get_db_helper()
            activities = db.get_active_activities()
            print(f"✅ Found {len(activities)} activities")
            
            if activities:
                activity = activities[0]
                points = db.calculate_points_for_activity(activity['id'], 50)
                print(f"✅ Points calculation works: 50 {activity['unit']} = {points} points")
            
            print("\n🎯 Database setup is ready for development!")
            return True
            
        except Exception as e:
            print(f"❌ Error during activity test: {e}")
            return False
    else:
        print("❌ Database connection failed")
        print("\nTroubleshooting tips:")
        print("1. Check that .env file exists with correct Supabase credentials")
        print("2. Verify SUPABASE_URL and SUPABASE_ANON_KEY in .env")
        print("3. Ensure database schema is set up correctly")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test database connection and operations")
    parser.add_argument("--quick", "-q", action="store_true", help="Run quick connection test only")
    parser.add_argument("--full", "-f", action="store_true", help="Run full test suite")
    
    args = parser.parse_args()
    
    if args.quick:
        test_minimal_connection()
    elif args.full:
        run_full_test_suite()
    else:
        # Default: run quick test
        print("Running quick test. Use --full for complete test suite.")
        print()
        test_minimal_connection()
