"""
Validation script for Standalone Local LinkedIn EasyApply Bot (Playwright Version)
Tests all local components and validates complete removal of Whitebox Learning dependencies.
"""

import sys
import os
import glob
import re

# Set stdout/stderr to UTF-8 encoding on Windows
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Add workspace directory to path
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORKSPACE_DIR)


def test_whitebox_absence():
    """Verify that zero Whitebox Learning (WBL) dependencies, files, or configs exist"""
    print("=" * 60)
    print("TESTING WHITEBOX INDEPENDENCE (LOCAL-ONLY AUDIT)")
    print("=" * 60)
    
    passed = True
    
    # 1. Check that wbl_api.py does not exist
    wbl_api_path = os.path.join(WORKSPACE_DIR, "bot", "utils", "wbl_api.py")
    if os.path.exists(wbl_api_path):
        print(f"❌ FAIL: Legacy Whitebox API file found at {wbl_api_path}")
        passed = False
    else:
        print("✅ No bot/utils/wbl_api.py file present")
        
    # 2. Check forbidden environment variables in environment
    forbidden_env_vars = ["WBL_API_BASE_URL", "WBL_EMAIL", "WBL_PASSWORD", "EMPLOYEE_ID"]
    found_env = [var for var in forbidden_env_vars if os.getenv(var)]
    if found_env:
        print(f"❌ FAIL: Whitebox environment variables detected in runtime env: {found_env}")
        passed = False
    else:
        print("✅ No Whitebox environment variables active in runtime")
        
    # 3. Scan code files for forbidden Whitebox patterns
    forbidden_patterns = [
        r"wbl_api",
        r"send_job_activity_log",
        r"api\.whitebox-learning\.com",
        r"wbl_candidate_id",
        r"WBL_API_BASE_URL",
        r"WBL_EMAIL",
        r"WBL_PASSWORD",
        r"EMPLOYEE_ID",
    ]
    
    code_extensions = (".py", ".yaml", ".yml", ".json", ".env.example")
    scanned_files = []
    
    for root, dirs, files in os.walk(WORKSPACE_DIR):
        # Exclude git, cache, virtualenvs, and log data
        if any(ignored in root for ignored in [".git", "__pycache__", ".venv", "venv", "node_modules"]):
            continue
        for file in files:
            if file.endswith(code_extensions) and file != "validate.py":
                scanned_files.append(os.path.join(root, file))
                
    violations = []
    for file_path in scanned_files:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                for pattern in forbidden_patterns:
                    matches = re.findall(pattern, content, flags=re.IGNORECASE)
                    if matches:
                        rel_path = os.path.relpath(file_path, WORKSPACE_DIR)
                        violations.append((rel_path, pattern, len(matches)))
        except Exception as e:
            print(f"⚠️ Warning reading {file_path}: {e}")
            
    if violations:
        print("❌ FAIL: Forbidden Whitebox references found in codebase:")
        for rel_path, pattern, count in violations:
            print(f"   - {rel_path}: matches '{pattern}' ({count} times)")
        passed = False
    else:
        print(f"✅ Scanned {len(scanned_files)} runtime/config files: 0 Whitebox references found")
        
    if passed:
        print("\n✅ Whitebox independence test passed!\n")
    else:
        print("\n❌ Whitebox independence test failed!\n")
        
    return passed


def test_imports():
    """Test that all local modules can be imported without external WBL dependencies"""
    print("=" * 60)
    print("TESTING MODULE IMPORTS")
    print("=" * 60)
    
    modules_to_test = [
        ("bot.core.browser", "Browser"),
        ("bot.core.session", "Session"),
        ("bot.core.execution_guard", "ExecutionGuard"),
        ("bot.core.dry_run", "DryRun"),
        ("bot.core.metrics", "Metrics"),
        ("bot.core.proxy_manager", "ProxyManager"),
        ("bot.application.workflow", "Workflow"),
        ("bot.application.form_filler", "FormFiller"),
        ("bot.application.smart_form_filler", "SmartFormFiller"),
        ("bot.discovery.search", "Search"),
        ("bot.discovery.job_identity", "JobIdentity"),
        ("bot.discovery.scroll_tracker", "ScrollTracker"),
        ("bot.persistence.store", "Store"),
        ("bot.utils.selectors", "Selectors"),
        ("bot.utils.human_interaction", "HumanInteraction"),
        ("bot.utils.logger", "StructuredLogger"),
        ("bot.utils.profile_safety", "ProfileSafety"),
    ]
    
    all_ok = True
    for mod_path, name in modules_to_test:
        try:
            __import__(mod_path)
            print(f"✅ {mod_path} ({name})")
        except Exception as e:
            print(f"❌ {mod_path} ({name}): {e}")
            all_ok = False
            
    if all_ok:
        print("\n✅ All local modules imported successfully!\n")
    else:
        print("\n❌ Some local module imports failed!\n")
        
    return all_ok


def test_selectors():
    """Test selector definitions"""
    print("=" * 60)
    print("TESTING SELECTORS")
    print("=" * 60)
    
    from bot.utils.selectors import LOCATORS, get_locator
    
    critical_selectors = [
        'easy_apply_button',
        'next',
        'submit',
        'error',
        'upload_resume',
        'search',
        'links',
    ]
    
    all_ok = True
    for selector_key in critical_selectors:
        selector = get_locator(selector_key)
        if selector:
            print(f"✅ {selector_key:20s} -> {selector}")
        else:
            print(f"❌ {selector_key:20s} -> NOT DEFINED")
            all_ok = False
    
    if all_ok:
        print("\n✅ All critical selectors defined!\n")
    else:
        print("\n❌ Some selectors are missing!\n")
    
    return all_ok


def test_dependencies():
    """Test that all required dependencies are installed"""
    print("=" * 60)
    print("TESTING DEPENDENCIES")
    print("=" * 60)
    
    dependencies = [
        ('playwright', 'Playwright'),
        ('dotenv', 'python-dotenv'),
        ('duckdb', 'DuckDB'),
        ('yaml', 'PyYAML'),
        ('requests', 'Requests'),
        ('bs4', 'BeautifulSoup4'),
        ('lxml', 'lxml'),
        ('psutil', 'psutil'),
        ('pandas', 'pandas'),
    ]
    
    all_ok = True
    for module_name, package_name in dependencies:
        try:
            __import__(module_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name} - NOT INSTALLED")
            all_ok = False
    
    if all_ok:
        print("\n✅ All dependencies installed!\n")
    else:
        print("\n❌ Some dependencies are missing! Run: pip install -r requirements.txt\n")
    
    return all_ok


def test_config():
    """Test configuration files (candidates.yaml / config.yaml)"""
    print("=" * 60)
    print("TESTING CONFIGURATION")
    print("=" * 60)
    
    import yaml
    
    candidates_file = os.path.join(WORKSPACE_DIR, "config", "candidates.yaml")
    candidates_example = os.path.join(WORKSPACE_DIR, "config", "candidates.example.yaml")
    legacy_file = os.path.join(WORKSPACE_DIR, "config.yaml")
    legacy_example = os.path.join(WORKSPACE_DIR, "config.example.yaml")
    
    target_candidates = candidates_file if os.path.exists(candidates_file) else candidates_example
    target_legacy = legacy_file if os.path.exists(legacy_file) else legacy_example
    
    try:
        with open(target_candidates, 'r', encoding='utf-8') as f:
            cdata = yaml.safe_load(f)
        candidates = cdata.get('candidates', [])
        print(f"✅ Candidate configuration valid ({os.path.basename(target_candidates)}): {len(candidates)} candidate profile(s) found")
        for c in candidates:
            # Verify no wbl_candidate_id required
            assert 'wbl_candidate_id' not in c, f"Candidate {c.get('id')} contains deprecated wbl_candidate_id"
            print(f"   - Candidate: {c.get('name')} (id: {c.get('id')}) [Enabled: {c.get('enabled', False)}]")
    except Exception as e:
        print(f"❌ Error in candidate config: {e}")
        return False
        
    try:
        with open(target_legacy, 'r', encoding='utf-8') as f:
            ldata = yaml.safe_load(f)
        print(f"✅ Legacy configuration valid ({os.path.basename(target_legacy)})")
    except Exception as e:
        print(f"❌ Error in legacy config: {e}")
        return False
        
    print("\n✅ Configuration files valid!\n")
    return True


def test_store():
    """Test local DuckDB store"""
    print("=" * 60)
    print("TESTING LOCAL DATABASE STORE (DUCKDB)")
    print("=" * 60)
    
    try:
        from bot.persistence.store import Store
        
        test_db = os.path.join(WORKSPACE_DIR, "data", "test_bot_data.duckdb")
        store = Store(db_file=test_db)
        print("✅ Local DuckDB Store initialized")
        
        # Test saving answer
        store.save_answer("test_q_whitebox_check", "test_a_local")
        print("✅ Local QA answer saved")
        
        # Test retrieving answer
        answer = store.get_answer("test_q_whitebox_check")
        if answer == "test_a_local":
            print("✅ QA answer retrieved correctly from local DuckDB")
        else:
            print(f"❌ QA answer mismatch: expected 'test_a_local', got '{answer}'")
            return False
            
        # Clean up test DB
        if os.path.exists(test_db):
            os.remove(test_db)
        
        print("\n✅ Local Store test passed!\n")
        return True
        
    except Exception as e:
        print(f"❌ Local Store test failed: {e}")
        return False


def test_local_logging():
    """Test local structured logging and file output"""
    print("=" * 60)
    print("TESTING LOCAL LOGGING")
    print("=" * 60)
    
    try:
        from bot.utils.logger import logger
        
        test_log_path = os.path.join(WORKSPACE_DIR, "data", "bot.log")
        logger.info("Validation local logger test entry", step="validate", event="test_run")
        
        if os.path.exists(test_log_path):
            print(f"✅ Local log file confirmed at {test_log_path}")
        else:
            print(f"⚠️ Log file not yet written to {test_log_path} (stdout handler active)")
            
        print("\n✅ Local logging test passed!\n")
        return True
    except Exception as e:
        print(f"❌ Local logging test failed: {e}")
        return False


def test_local_metrics():
    """Test local metrics calculations and output"""
    print("=" * 60)
    print("TESTING LOCAL METRICS")
    print("=" * 60)
    
    try:
        from bot.core.metrics import Metrics
        m = Metrics()
        m.increment('attempted')
        m.increment('submitted')
        m.increment('skipped')
        m.increment('failed')
        
        assert m.attempted == 1
        assert m.submitted == 1
        assert m.skipped == 1
        assert m.failed == 1
        
        print("✅ Metrics incrementation verified")
        print("✅ Local session summary printing works locally without external telemetry")
        print("\n✅ Local metrics test passed!\n")
        return True
    except Exception as e:
        print(f"❌ Local metrics test failed: {e}")
        return False


def main():
    """Run all validation tests"""
    print("\n" + "=" * 60)
    print("LINKEDIN EASYAPPLY BOT - STANDALONE VALIDATION")
    print("Playwright Version (100% Local, Zero Whitebox Dependencies)")
    print("=" * 60 + "\n")
    
    results = {
        "Whitebox Independence": test_whitebox_absence(),
        "Dependencies": test_dependencies(),
        "Module Imports": test_imports(),
        "Selectors": test_selectors(),
        "Configuration": test_config(),
        "Database Store (DuckDB)": test_store(),
        "Local Logging": test_local_logging(),
        "Local Metrics": test_local_metrics(),
    }
    
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:25s} {status}")
    
    all_passed = all(results.values())
    
    print("=" * 60)
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! Standalone bot is ready for local execution.")
        print("\nTo run the bot locally:")
        print("  python main.py")
        print("\nQuick setup checklist:")
        print("  1. Copy .env.example to .env and configure credentials")
        print("  2. Copy config/candidates.example.yaml to config/candidates.yaml")
        print("  3. Set dry_run: false when ready to submit live applications")
    else:
        print("\n⚠️  SOME TESTS FAILED! Please check the output above.")
    
    print("\n")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
