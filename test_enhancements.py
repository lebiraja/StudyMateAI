"""
Test script for StudyMateAI enhancements
"""
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

def test_imports():
    """Test if all modules can be imported"""
    console.print("🧪 Testing module imports...", style="blue")
    
    tests = []
    
    try:
        import config
        tests.append(("config", "✅", "green"))
    except Exception as e:
        tests.append(("config", f"❌ {e}", "red"))
    
    try:
        import utils
        tests.append(("utils", "✅", "green"))
    except Exception as e:
        tests.append(("utils", f"❌ {e}", "red"))
    
    try:
        import studymateai_rag_pipeline
        tests.append(("studymateai_rag_pipeline", "✅", "green"))
    except Exception as e:
        tests.append(("studymateai_rag_pipeline", f"❌ {e}", "red"))
    
    try:
        import assignment_handler
        tests.append(("assignment_handler", "✅", "green"))
    except Exception as e:
        tests.append(("assignment_handler", f"❌ {e}", "red"))
    
    try:
        import dashboard
        tests.append(("dashboard", "✅", "green"))
    except Exception as e:
        tests.append(("dashboard", f"❌ {e}", "red"))
    
    return tests

def test_directories():
    """Test if directories are created properly"""
    console.print("📁 Testing directory structure...", style="blue")
    
    import config
    
    tests = []
    
    for name, path in {
        "DATA_DIR": config.DATA_DIR,
        "ASSIGNMENT_DIR": config.ASSIGNMENT_DIR,
        "ASSIGNMENT_ANSWERS_DIR": config.ASSIGNMENT_ANSWERS_DIR,
        "LOGS_DIR": config.LOGS_DIR,
    }.items():
        if path.exists():
            tests.append((name, "✅", "green"))
        else:
            tests.append((name, "❌ Missing", "red"))
    
    return tests

def test_utilities():
    """Test utility functions"""
    console.print("🔧 Testing utility functions...", style="blue")
    
    tests = []
    
    try:
        import utils
        
        # Test safe filename
        safe_name = utils.safe_filename("Test<>File?.txt")
        if "Test" in safe_name and "<" not in safe_name:
            tests.append(("safe_filename", "✅", "green"))
        else:
            tests.append(("safe_filename", "❌ Failed", "red"))
        
        # Test text chunking
        chunks = utils.chunk_text("This is a test. This is another test.", chunk_size=10)
        if len(chunks) > 0:
            tests.append(("chunk_text", "✅", "green"))
        else:
            tests.append(("chunk_text", "❌ Failed", "red"))
        
        # Test prompt formatting
        prompt = utils.format_assignment_prompt("Test Assignment", "Test description")
        if "Test Assignment" in prompt:
            tests.append(("format_assignment_prompt", "✅", "green"))
        else:
            tests.append(("format_assignment_prompt", "❌ Failed", "red"))
            
    except Exception as e:
        tests.append(("utility_functions", f"❌ {e}", "red"))
    
    return tests

def test_file_structure():
    """Test if all important files exist"""
    console.print("📄 Testing file structure...", style="blue")
    
    tests = []
    
    required_files = [
        "config.py",
        "utils.py", 
        "studymateai_rag_pipeline.py",
        "assignment_handler.py",
        "dashboard.py",
        "setup.py",
        "requirements.txt",
        "readme.md"
    ]
    
    for file in required_files:
        if Path(file).exists():
            tests.append((file, "✅", "green"))
        else:
            tests.append((file, "❌ Missing", "red"))
    
    return tests

def main():
    """Run all tests"""
    console.print("🚀 StudyMateAI Enhancement Tests", style="bold blue")
    console.print("="*50, style="blue")
    
    all_tests = []
    
    # Run tests
    all_tests.extend(test_imports())
    all_tests.extend(test_directories())
    all_tests.extend(test_utilities())
    all_tests.extend(test_file_structure())
    
    # Create results table
    table = Table(title="Test Results")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="white")
    
    passed = 0
    total = len(all_tests)
    
    for test_name, status, color in all_tests:
        table.add_row(test_name, status)
        if "✅" in status:
            passed += 1
    
    console.print(table)
    
    # Summary
    console.print(f"\n📊 Results: {passed}/{total} tests passed", 
                  style="green" if passed == total else "yellow")
    
    if passed == total:
        console.print("🎉 All enhancements are working correctly!", style="bold green")
        console.print("\n🚀 Ready to use StudyMateAI with enhanced features!", style="blue")
    else:
        console.print("⚠️ Some issues detected. Please check the failing components.", style="yellow")

if __name__ == "__main__":
    main()

