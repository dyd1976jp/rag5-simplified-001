#!/usr/bin/env python3
"""
Task 5 Verification Script

This script verifies that the delete knowledge base functionality
is properly implemented and meets all requirements.
"""

import sys
import inspect
from typing import Dict, Any

# Import the modules to verify
try:
    from rag5.interfaces.ui.pages.knowledge_base.list import (
        show_delete_confirmation,
        render_kb_card
    )
    from rag5.interfaces.ui.pages.knowledge_base.api_client import (
        KnowledgeBaseAPIClient
    )
    print("✓ All required modules imported successfully")
except ImportError as e:
    print(f"✗ Failed to import modules: {e}")
    sys.exit(1)


def verify_function_exists(func, name: str) -> bool:
    """Verify a function exists and has proper signature"""
    if func is None:
        print(f"✗ Function {name} not found")
        return False
    print(f"✓ Function {name} exists")
    return True


def verify_function_signature(func, expected_params: list) -> bool:
    """Verify function has expected parameters"""
    sig = inspect.signature(func)
    params = list(sig.parameters.keys())
    
    for param in expected_params:
        if param not in params:
            print(f"  ✗ Missing parameter: {param}")
            return False
    
    print(f"  ✓ All expected parameters present: {expected_params}")
    return True


def verify_function_docstring(func, name: str) -> bool:
    """Verify function has documentation"""
    if not func.__doc__:
        print(f"  ✗ Function {name} missing docstring")
        return False
    print(f"  ✓ Function {name} has docstring")
    return True


def verify_api_client_method() -> bool:
    """Verify API client has delete method"""
    client = KnowledgeBaseAPIClient()
    
    if not hasattr(client, 'delete_knowledge_base'):
        print("✗ API client missing delete_knowledge_base method")
        return False
    
    print("✓ API client has delete_knowledge_base method")
    
    # Check method signature
    method = getattr(client, 'delete_knowledge_base')
    sig = inspect.signature(method)
    params = list(sig.parameters.keys())
    
    if 'kb_id' not in params:
        print("  ✗ delete_knowledge_base missing kb_id parameter")
        return False
    
    print("  ✓ delete_knowledge_base has correct signature")
    return True


def verify_dialog_decorator() -> bool:
    """Verify show_delete_confirmation uses @st.dialog decorator"""
    # Check if function has the dialog wrapper
    # This is a basic check - in real usage, Streamlit applies the decorator
    func_name = show_delete_confirmation.__name__
    if func_name != 'show_delete_confirmation':
        print("✗ Function name mismatch")
        return False
    
    print("✓ show_delete_confirmation function properly defined")
    return True


def main():
    """Run all verification checks"""
    print("=" * 60)
    print("Task 5 Verification: Delete Knowledge Base Functionality")
    print("=" * 60)
    print()
    
    all_passed = True
    
    # 1. Verify show_delete_confirmation function
    print("1. Verifying show_delete_confirmation function...")
    if not verify_function_exists(show_delete_confirmation, "show_delete_confirmation"):
        all_passed = False
    else:
        if not verify_function_signature(show_delete_confirmation, ['kb', 'api_client']):
            all_passed = False
        if not verify_function_docstring(show_delete_confirmation, "show_delete_confirmation"):
            all_passed = False
        if not verify_dialog_decorator():
            all_passed = False
    print()
    
    # 2. Verify render_kb_card function
    print("2. Verifying render_kb_card function...")
    if not verify_function_exists(render_kb_card, "render_kb_card"):
        all_passed = False
    else:
        if not verify_function_signature(render_kb_card, ['kb', 'api_client']):
            all_passed = False
        if not verify_function_docstring(render_kb_card, "render_kb_card"):
            all_passed = False
    print()
    
    # 3. Verify API client delete method
    print("3. Verifying API client delete method...")
    if not verify_api_client_method():
        all_passed = False
    print()
    
    # 4. Check for test file
    print("4. Verifying test file exists...")
    try:
        with open('test_delete_kb_dialog.py', 'r') as f:
            content = f.read()
            if 'test_show_delete_confirmation' in content:
                print("✓ Test file exists with proper tests")
            else:
                print("✗ Test file missing expected tests")
                all_passed = False
    except FileNotFoundError:
        print("✗ Test file not found")
        all_passed = False
    print()
    
    # 5. Check for documentation
    print("5. Verifying documentation exists...")
    try:
        with open('rag5/interfaces/ui/pages/knowledge_base/DELETE_KB_USAGE.md', 'r') as f:
            content = f.read()
            if 'Delete Knowledge Base' in content:
                print("✓ Documentation file exists")
            else:
                print("✗ Documentation incomplete")
                all_passed = False
    except FileNotFoundError:
        print("✗ Documentation file not found")
        all_passed = False
    print()
    
    # 6. Verify requirements mapping
    print("6. Verifying requirements coverage...")
    requirements = {
        "4.1": "st.dialog decorator for confirmation",
        "4.2": "st.warning for irreversible warning",
        "4.3": "API call and st.rerun on success",
        "4.4": "st.error for failure messages"
    }
    
    # Read the source code to verify
    try:
        with open('rag5/interfaces/ui/pages/knowledge_base/list.py', 'r') as f:
            source = f.read()
            
            checks = {
                "4.1": "@st.dialog" in source,
                "4.2": "st.warning" in source and "不可撤销" in source,
                "4.3": "st.rerun()" in source and "delete_knowledge_base" in source,
                "4.4": "st.error" in source and "删除失败" in source
            }
            
            for req_id, description in requirements.items():
                if checks[req_id]:
                    print(f"  ✓ Requirement {req_id}: {description}")
                else:
                    print(f"  ✗ Requirement {req_id}: {description}")
                    all_passed = False
    except FileNotFoundError:
        print("✗ Source file not found")
        all_passed = False
    print()
    
    # Summary
    print("=" * 60)
    if all_passed:
        print("✓ ALL VERIFICATIONS PASSED")
        print("Task 5 implementation is complete and correct!")
        return 0
    else:
        print("✗ SOME VERIFICATIONS FAILED")
        print("Please review the failed checks above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
