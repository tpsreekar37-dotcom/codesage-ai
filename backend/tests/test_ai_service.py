import os
import tempfile
import pytest
from app.services.ai_engine import AIEngineService

def test_scan_repository_files_filters_dirs():
    # Setup temporary directory and files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create supported file
        py_file = os.path.join(temp_dir, "app.py")
        with open(py_file, "w") as f:
            f.write("print('hello')")
            
        # Create ignored folder and file
        ignored_dir = os.path.join(temp_dir, "node_modules")
        os.makedirs(ignored_dir)
        ignored_file = os.path.join(ignored_dir, "package.js")
        with open(ignored_file, "w") as f:
            f.write("console.log('ignored')")
            
        # Run scan
        files_data = AIEngineService._scan_repository_files(temp_dir)
        
        # Verify result
        assert len(files_data) == 1
        assert files_data[0][0] == "app.py"
        assert files_data[0][1] == "Python"
        assert files_data[0][2] == "print('hello')"

def test_mock_report_generation():
    # Verify mock engine fallback handles generating standard keys
    files_data = [("main.py", "Python", "def run(): pass")]
    report = AIEngineService._generate_mock_report(files_data)
    
    assert "score_quality" in report
    assert "score_security" in report
    assert "findings" in report
    assert "markdown_report" in report
    assert len(report["findings"]) > 0
