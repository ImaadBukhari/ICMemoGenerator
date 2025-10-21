#!/usr/bin/env python3
"""
Test script for the 1-page memo feature
This script tests the new short memo functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_short_memo_prompts():
    """Test that short memo prompts are loaded correctly"""
    try:
        from backend.services.memo_generation_service import load_short_memo_prompts
        
        prompts = load_short_memo_prompts()
        print("✅ Short memo prompts loaded successfully")
        print(f"   Found {len(prompts)} prompt sections:")
        for key in prompts.keys():
            print(f"   - {key}")
        
        # Check that all required sections are present
        required_sections = [
            'company_brief', 'startup_overview', 'founder_team',
            'deal_traction', 'competitive_landscape', 'remarks'
        ]
        
        for section in required_sections:
            if section not in prompts:
                print(f"❌ Missing required section: {section}")
                return False
        
        print("✅ All required sections present")
        return True
        
    except Exception as e:
        print(f"❌ Error loading short memo prompts: {str(e)}")
        return False

def test_document_service_import():
    """Test that the new document service functions can be imported"""
    try:
        from backend.services.document_service import generate_short_word_document
        print("✅ Short document service imported successfully")
        return True
    except Exception as e:
        print(f"❌ Error importing short document service: {str(e)}")
        return False

def test_memo_generation_service_import():
    """Test that the new memo generation functions can be imported"""
    try:
        from backend.services.memo_generation_service import generate_short_memo, compile_short_memo
        print("✅ Short memo generation service imported successfully")
        return True
    except Exception as e:
        print(f"❌ Error importing short memo generation service: {str(e)}")
        return False

def test_model_changes():
    """Test that the model changes are valid"""
    try:
        from backend.db.models import MemoRequest
        
        # Check if memo_type field exists in the model
        if hasattr(MemoRequest, 'memo_type'):
            print("✅ MemoRequest model has memo_type field")
            return True
        else:
            print("❌ MemoRequest model missing memo_type field")
            return False
    except Exception as e:
        print(f"❌ Error checking model changes: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing 1-Page Memo Feature Implementation")
    print("=" * 50)
    
    tests = [
        ("Model Changes", test_model_changes),
        ("Short Memo Prompts", test_short_memo_prompts),
        ("Document Service Import", test_document_service_import),
        ("Memo Generation Service Import", test_memo_generation_service_import),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing: {test_name}")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! 1-page memo feature is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
